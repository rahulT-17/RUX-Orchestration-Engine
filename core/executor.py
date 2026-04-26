# CORE / executor.py
# The executor is the runtime coordinator for a planned action.
# Data flow is:
# planner_output -> tool lookup -> schema validation -> optional confirmation
# -> tool execution -> domain/task classification -> logging/outcomes
# -> decision analysis -> confidence lookup -> final user response

import logging
import time

from core.tool_response import ToolResponse, ToolStatus
from repositories.confirmation_repository import ConfirmationRepository
from repositories.agent_run_repository import AgentRunRepository
from repositories.agent_outcomes_repository import AgentOutcomesRepository
from services.confidence_service import ConfidenceService
from services.decision_engine import DecisionEngine

logger = logging.getLogger(__name__)


class Executor:
    def __init__(self, tools_registry, critic_service):
        self.tools_registry = tools_registry
        self.critic_service = critic_service
        self.decision_engine = DecisionEngine(critic_service)

    # Resolve runtime classification from tool metadata first.
    # If a tool is multi-action (like expense_manager), fall back to the validated action field.
    def _resolve_domain_and_task_type(self, tool, action_name, validated, parameters):
        domain = getattr(tool, "domain", None) or "general"

        task_type = getattr(tool, "task_type", None)
        if not task_type:
            task_type = getattr(validated, "action", None)

        if not task_type:
            task_type = parameters.get("action")

        if not task_type:
            task_type = action_name

        return domain, task_type

    # This is only a temporary heuristic so feedback/confidence has a first signal.
    # Failed executions should never be auto-marked correct.
    def _should_auto_mark_correct(self, result: ToolResponse, domain: str, task_type: str) -> bool:
        if result.status == ToolStatus.FAILED:
            return False

        if domain == "expense" and task_type in ["log", "set_budget", "analyze", "get_budget"]:
            return True

        if domain == "project" and task_type in ["create_project", "delete_project"]:
            return True

        return False

    # Build the final outward response from the normalized tool result plus post-execution signals.
    def _build_response(self, result: ToolResponse, analysis: dict, confidence: dict) -> str:
        response = result.message

        if analysis["system_analysis"]:
            response += f"\n\nObservation:\n{analysis['system_analysis']}"

        if analysis.get("critic_mode") == "background":
            response += "\n\nSecond Opinion: queued in background (non-blocking)."
        elif analysis["critic_analysis"]:
            response += f"\n\nSecond Opinion:\n{analysis['critic_analysis']}"

        if confidence["confidence"] is None:
            response += f"\n\nConfidence: insufficient data ({confidence['samples']} samples)"
        else:
            response += (
                f"\n\nConfidence: {confidence['confidence']}% "
                f"(based on {confidence['samples']} runs)"
            )

        return response

    # Shared post-execution pipeline.
    # Both normal execution and confirmed execution should pass through here so they
    # produce the same logging, feedback, analysis, confidence, and final response shape.
    async def finalize_execution(
        self,
        state,
        db,
        tool,
        action_name,
        parameters,
        validated,
        result: ToolResponse,
        execution_message: str | None = None,
    ):
        finalize_start = time.perf_counter()
        execution_substages = {
            "tool_call_ms": round(result.latency_ms or 0.0, 2),
        }

        # The normalized tool result is now part of runtime state and can be reused
        # by later stages if needed.
        state.tool_result = result
        state.set_stage("EXECUTION_COMPLETED")

        effective_message = execution_message or state.message

        # Classify the run once so logging, outcomes, and confidence all speak
        # the same domain/task language.
        domain, task_type = self._resolve_domain_and_task_type(
            tool,
            action_name,
            validated,
            parameters,
        )
        
        result.metadata = result.metadata or {}
        if getattr(state, "timings_ms", None):
            result.metadata["stage_timings_ms"] = dict(state.timings_ms)

        result_payload = result.to_dict()
        # Persist the normalized result as the durable audit trail for this run.
        agentrun_repo = AgentRunRepository(db)
        run_log_start = time.perf_counter()
        run_id = await agentrun_repo.log_run(
            user_id=state.user_id,
            message=effective_message,
            action=action_name,
            parameters=parameters,
            result=result_payload,
            latency=result.latency_ms or 0.0,
        )
        execution_substages["run_log_ms"] = round((time.perf_counter() - run_log_start) * 1000, 2)

        # Record the first correctness signal. This is still heuristic and can
        # later be corrected by explicit user feedback.
        auto_correct = self._should_auto_mark_correct(result, domain, task_type)

        outcome_repo = AgentOutcomesRepository(db)
        outcome_start = time.perf_counter()
        await outcome_repo.record_outcome(
            run_id=run_id,
            user_id=state.user_id,
            domain=domain,
            task_type=task_type,
            was_correct=auto_correct,
        )
        execution_substages["outcome_log_ms"] = round((time.perf_counter() - outcome_start) * 1000, 2)

        # Pass the normalized ToolResponse straight into the decision layer so
        # post-execution reasoning uses the same contract as the rest of runtime.
        decision_start = time.perf_counter()
        analysis = await self.decision_engine.evaluate(
            state.user_id,
            effective_message,
            domain,
            task_type,
            result,
            run_id=run_id,
        )
        execution_substages["decision_engine_ms"] = round((time.perf_counter() - decision_start) * 1000, 2)
        execution_substages["critic_ms"] = round(float(analysis.get("critic_ms", 0.0)), 2)
        result.metadata["critic_mode"] = analysis.get("critic_mode", "skipped")

        confidence_service = ConfidenceService(db)
        confidence_start = time.perf_counter()
        confidence = await confidence_service.get_confidence(
            state.user_id,
            domain,
            task_type,
        )
        execution_substages["confidence_ms"] = round((time.perf_counter() - confidence_start) * 1000, 2)

        response_start = time.perf_counter()
        response = self._build_response(result, analysis, confidence)
        execution_substages["response_build_ms"] = round((time.perf_counter() - response_start) * 1000, 2)
        execution_substages["finalize_ms"] = round((time.perf_counter() - finalize_start) * 1000, 2)

        result.metadata["execution_substages_ms"] = execution_substages
        if getattr(state, "timings_ms", None) is not None:
            state.timings_ms["finalize_ms"] = execution_substages["finalize_ms"]

        # Run row already exists (needed for outcomes), so patch enriched metadata now.
        try:
            await agentrun_repo.merge_run_metadata(run_id, result.metadata)
        except Exception:
            logger.exception("Failed to patch run.result metadata run_id=%s", run_id)

        logger.info(
            "execution_substages trace_id=%s run_id=%s substages=%s",
            getattr(state, "trace_id", "n/a"),
            run_id,
            execution_substages,
        )

        return {"run_id": run_id, "response": response}

    # Execution begins :
    async def execute(self, state, db):
        state.set_stage("EXECUTING")

        # 1) The planner must hand us a structured action before execution can begin.
        if not state.planner_output:
            return "Nothing to execute"

        action_name = state.planner_output["action"]
        parameters = state.planner_output.get("parameters", {})

        # 2) Look up the tool definition. This gives us the schema, adapter function,
        # and runtime metadata like domain/task ownership.
        tool = self.tools_registry.get(action_name)
        if not tool:
            state.error = f"Error: Action '{action_name}' is not recognized."
            return state.error

        # 3) Validate planner params before any state-changing code runs.
        # This is the runtime trust boundary for the action request.
        try:
            validated = tool.schema(**parameters)
        except Exception as e:
            return (
                f"Error: Invalid parameters for action '{action_name}'. "
                f"Details: {str(e)} Please clarify your request and try again."
            )

        # 4) High-risk tools pause here and store a pending confirmation.
        # The actual confirmed execution will later resume through confirmation_manager
        # and come back into the shared finalize_execution path.
        if tool.requires_confirmation:
            repo = ConfirmationRepository(db)
            await repo.create(
                user_id=state.user_id,
                action=action_name,
                parameters=parameters,
                original_message=state.message,
            )
            return f"Confirmation required for '{action_name}' action. Reply (yes/no)"

        # 5) Execute the tool adapter. Every tool is expected to return ToolResponse now.
        start = time.time()
        try:
            result = await tool.function(state.user_id, validated, db)

            if not isinstance(result, ToolResponse):
                raise TypeError(
                    f"Tool '{action_name}' returned {type(result).__name__}, expected ToolResponse"
                )
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 2)
            result = ToolResponse(
                status=ToolStatus.FAILED,
                message=f"Execution error: {str(e)}",
                error=str(e),
                metadata={"action": action_name},
                latency_ms=latency_ms,
            )
        else:
            result.latency_ms = round((time.time() - start) * 1000, 2)

        # 6) Hand the normalized result into the shared post-execution pipeline.
        # This keeps the execution path small and lets confirmation reuse the same flow.
        return await self.finalize_execution(
            state=state,
            db=db,
            tool=tool,
            action_name=action_name,
            parameters=parameters,
            validated=validated,
            result=result,
        )
