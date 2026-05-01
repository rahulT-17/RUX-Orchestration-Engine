# CORE / planner.py => This is used for extracting planner from agent_core.py 
# Splitting LLM call, json parsing and schema validation from agent_core.py to planner.py to make the code more modular and maintainable.

import logging
import json
from json import JSONDecodeError
from core.execution_state import ExecutionState

logger = logging.getLogger(__name__)

# ── Layer 1: Deterministic greeting detection ──
# These never reach the LLM — instant response, zero cost
GREETINGS = [
    "hi", "hii", "hello", "hey", "thanks", "thank you",
    "okay", "ok", "good morning", "good evening", "bye",
    "good night", "sup", "yo", "howdy"
]

# ── Layer 2: Action intent keywords ──
# If any of these are present → LLM extracts JSON action
ACTION_KEYWORDS = [
    # log intent
    "log", "spent", "add", "record", "paid", "bought", "save", "note",
    # analyze intent
    "analyze", "show", "how much", "summary", "breakdown", "review",
    "what did i spend", "give me", "tell me", "check my expenses",
    # budget set intent
    "set budget", "set a budget", "create budget", "budget for",
    "budget of", "allocate", "i want to budget", "monthly budget",
    "limit my", "set limit",
    # budget get intent
    "what is my budget", "get budget", "show budget", "check my budget",
    # project intent
    "create project", "new project", "delete project", "remove project",
    "create a project", "delete the project"
]

SYSTEM_PROMPT = """ 
   You are RUX planner. Return exactly one JSON object and nothing else.

Allowed top-level actions:

expense_manager
create_project
delete_project
Intent mapping:

User wants to view/review spending -> expense_manager with action analyze
User wants to record spending -> expense_manager with action log
User wants to create/set budget -> expense_manager with action set_budget
User wants to check existing budget -> expense_manager with action get_budget
If unclear between analyze and log -> choose analyze
Never invent actions or fields.
Only use these schemas:

expense_manager log
{"action":"expense_manager","parameters":{"action":"log","amount":number,"category":string,"note":string optional,"mode":"soft|hard"}}

expense_manager analyze
{"action":"expense_manager","parameters":{"action":"analyze","category":string optional,"period":string optional}}

expense_manager set_budget
{"action":"expense_manager","parameters":{"action":"set_budget","category":string,"budget":number,"start_date":"YYYY-MM-DD","end_date":"YYYY-MM-DD"}}

expense_manager get_budget
{"action":"expense_manager","parameters":{"action":"get_budget","category":string}}

create_project
{"action":"create_project","parameters":{"name":string,"description":string optional}}

delete_project
{"action":"delete_project","parameters":{"project_id":number optional,"name":string optional}}

Mode rule:

Use hard only if user says strict, block, reject, do not exceed, or hard limit.
Otherwise use soft.
"""


class Planner:

    def __init__(self, llm_service):
        self.llm_service = llm_service

    async def plan(self, state: "ExecutionState"):
        """
        Three layer intent detection:
        Layer 1 → greeting detected deterministically, no LLM call
        Layer 2 → action keywords detected, LLM extracts JSON
        Layer 3 → general question, LLM responds conversationally
        """
        state.set_stage("PLANNING")
        message = state.message.lower().strip()

        # ── Layer 1: Greeting (deterministic, zero LLM cost) ──
        if self._is_greeting(message):
            return state, "Hey! How can I help you today?"

        # ── Layer 2: Action intent (LLM extracts structured JSON) ──
        if self._has_action_intent(message):
            reply = await self.llm_service.generate(SYSTEM_PROMPT, state.message)
            
            logger.debug("Planner's raw response: %s", reply)

            return await self._parse_action_reply(reply, state)

        # ── Layer 3: General question (LLM responds conversationally) ──
        reply = await self.llm_service.converse(state.message)
        return state, reply

    def _is_greeting(self, message: str) -> bool:
        """Check if message is a greeting — deterministic, no LLM."""
        return any(
            message == g or message.startswith(g + " ")
            for g in GREETINGS
        )

    def _has_action_intent(self, message: str) -> bool:
        """Check if message contains action keywords — deterministic."""
        return any(k in message for k in ACTION_KEYWORDS)

    async def _parse_action_reply(self, reply: str, state: "ExecutionState"):
        """Parse LLM JSON reply and update state."""
        try:
            # strip markdown fences if model wraps in ```json
            clean = reply.strip().removeprefix("```json").removesuffix("```").strip()
            parsed = json.loads(clean)

            # LLM returned conversational text as JSON somehow
            if "action" not in parsed:
                return state, reply

            state.planner_output = parsed
            state.set_stage("PLANNING_COMPLETED")
            
            logger.debug("Planner's parsed output: %s", parsed)  # debug

            return state, None

        except JSONDecodeError:
            # LLM returned plain text — treat as conversational reply
            return state, reply