# Decision Engine for evaluating and selecting the best course of action :

import asyncio
import logging
import time
from datetime import datetime, timezone

import httpx
from database import AsyncSessionLocal
from core.config import CRITIC_NON_BLOCKING
from core.tool_response import ToolResponse, ToolStatus
from repositories.agent_run_repository import AgentRunRepository

logger = logging.getLogger(__name__)

class DecisionEngine :

    def __init__ (self, critic_service, critic_non_blocking=None) :
        self.critic_service = critic_service
        self.critic_non_blocking = CRITIC_NON_BLOCKING if critic_non_blocking is None else critic_non_blocking

    def _should_run_critic(self, domain: str, task_type: str, result: ToolResponse) -> bool:
        # Always evaluate failures/partials with critic for diagnostics.
        if result.status in [ToolStatus.FAILED, ToolStatus.PARTIAL]:
            return True

        # For successful runs, critic is only useful for state-changing/high-risk actions.
        return (domain, task_type) in {
            ("project", "delete_project"),
            ("expense", "log"),
            ("expense", "set_budget"),
        }


    async def _persist_background_critic(self, run_id, metadata_updates):
        if not run_id or not metadata_updates:
            return

        try:
            async with AsyncSessionLocal() as bg_db:
                repo = AgentRunRepository(bg_db)
                await repo.merge_run_metadata(run_id, metadata_updates)
        except Exception:
            logger.exception("critic_background_persist_failed run_id=%s", run_id)


    async def _run_critic_background(self, run_id, user_id, message, domain, task_type, result_dict):
        """Fire-and-forget critic path for low-latency responses."""
        critic_start = time.perf_counter()
        try:
            critic_analysis = await self.critic_service.critique(
                message,
                domain,
                task_type,
                result_dict,
            )

            critic_ms = round((time.perf_counter() - critic_start) * 1000, 2)
            await self._persist_background_critic(
                run_id,
                {
                    "critic_background_status": "completed",
                    "critic_background_result": critic_analysis,
                    "critic_background_error": None,
                    "critic_background_latency_ms": critic_ms,
                    "critic_background_completed_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            logger.info(
                "critic_background_completed run_id=%s user_id=%s domain=%s task_type=%s critic_ms=%.2f",
                run_id,
                user_id,
                domain,
                task_type,
                critic_ms,
            )
        except httpx.ReadTimeout as exc:
            critic_ms = round((time.perf_counter() - critic_start) * 1000, 2)
            await self._persist_background_critic(
                run_id,
                {
                    "critic_background_status": "timeout",
                    "critic_background_result": None,
                    "critic_background_error": str(exc),
                    "critic_background_latency_ms": critic_ms,
                    "critic_background_completed_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            logger.warning(
                "critic_background_timeout run_id=%s user_id=%s domain=%s task_type=%s critic_ms=%.2f",
                run_id,
                user_id,
                domain,
                task_type,
                critic_ms,
            )
        except Exception:
            critic_ms = round((time.perf_counter() - critic_start) * 1000, 2)
            await self._persist_background_critic(
                run_id,
                {
                    "critic_background_status": "failed",
                    "critic_background_result": None,
                    "critic_background_error": "unexpected_error",
                    "critic_background_latency_ms": critic_ms,
                    "critic_background_completed_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            logger.exception(
                "critic_background_failed run_id=%s user_id=%s domain=%s task_type=%s",
                run_id,
                user_id,
                domain,
                task_type,
            )

    async def evaluate(self, user_id, message, domain, task_type, result: ToolResponse, run_id=None):
        """
        Generates system reasoning and LLM-based critique for the given
        user message, classified task, and normalized tool result.
        """
        
        # Deterministic reasoning runs first so we always have a local explanation path.
        system_analysis = await self.system_reasoning(domain, task_type, result)

        # Critic runs as a second opinion layer for important domains.
        critic_analysis = None
        critic_ms = 0.0
        critic_mode = "skipped"

        if self._should_run_critic(domain, task_type, result):
            if self.critic_non_blocking:
                critic_mode = "background"
                asyncio.create_task(
                    self._run_critic_background(
                        run_id,
                        user_id,
                        message,
                        domain,
                        task_type,
                        result.to_dict(),
                    )
                )
            else:
                critic_mode = "inline"
                critic_start = time.perf_counter()
                critic_analysis = await self.critic_service.critique(
                    message,
                    domain,
                    task_type,
                    result.to_dict(),
                )
                critic_ms = round((time.perf_counter() - critic_start) * 1000, 2)
    
        return {
            "system_analysis" : system_analysis,
            "critic_analysis" : critic_analysis,
            "critic_mode": critic_mode,
            "critic_ms": critic_ms,
        }
    
    async def system_reasoning(self, domain, task_type, result: ToolResponse) :

        """
        Deterministic reasoning based on normalized ToolResponse.
        This keeps rule-based explanations separate from LLM critique.
        """

        if domain == "expense" :
             
            if task_type == "log" :
                if result.status == ToolStatus.PARTIAL :
                    warning = None 
                    if result.metadata :
                        warning = result.metadata.get("warning")
                    return warning or result.message 
                
                if result.status == ToolStatus.FAILED:
                    return result.message
                return None
            
            elif task_type == "set_budget" :
                if result.status == ToolStatus.SUCCESS :
                    return "Budget set. Future expenses in this category will be validated against it."
                return result.message 
            
            elif task_type == "analyze" :
                if result.status == ToolStatus.SUCCESS and result.data :
                    category= result.data.get("category", "all categories")
                    period = result.data.get("period", "all time")
                    return f"Analysis complete for {category} over {period}."
                return None
            
            elif task_type == "get_budget" :
                return None 
            
        if domain == "project" :
            if task_type == "create_project":
                return None

            elif task_type == "delete_project":
                return "Project deletion is irreversible."

        return None
