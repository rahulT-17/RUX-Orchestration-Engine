# CORE / orchestrator.py => New Agent_core the Orchestrator class which is responsible for managing the overall flow of the AI companion system. 
# It coordinates between different components like the state manager, memory manager, and confirmation manager.
import logging
import time
from core.execution_state import ExecutionState

# repositries and models :
from repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self , planner , executor , confirmation_manager )   :
        self.planner = planner
        self.executor = executor
        self.confirmation_manager = confirmation_manager
        
    async def handle_message(self, user_id , message , db ) :

        # Ensure the user exists in the database, if not create a new user. This is important because we want to have a record of all users interacting with the system for future reference and to associate their actions and confirmations with their user ID.
        user_repo = UserRepository(db)
        await user_repo.get_or_create(user_id)
        
        # Step 1 : Create a new execution state for the incoming message :
        state = ExecutionState(user_id , message)
        
        state.timings_ms = {}

        confirm_start = time.perf_counter()
        # Confirmation handling runs before planning. If the user is replying to an
        # earlier high-risk action, we should resume that path instead of planning a new one.
        confirm_result = await self.confirmation_manager.handle(
            state,
            db,
            self.executor,
        )

        state.timings_ms["confirmation_ms"] = round((time.perf_counter() - confirm_start) * 1000, 2)
        
        # Confirmation manager now returns a full response payload, including a run_id
        # when a confirmed action actually executes through the shared executor pipeline.
        if confirm_result:
            logger.info("stage_timings trace_id=%s timings=%s", state.trace_id, state.timings_ms)
            return confirm_result
        
        # Step 2 : Planning stage : Call the planner to analyze the user message and determine if any action is required, the planner will return the parsed action and parameters if an action is required, or None if no action is required and the message should be treated as a normal reply.
        plan_start = time.perf_counter()
        state , normal_reply = await self.planner.plan(state)

        state.timings_ms["planning_ms"] =  round((time.perf_counter() - plan_start) * 1000, 2)

        if normal_reply :
            logger.info("stage_timings trace_id=%s timings=%s", state.trace_id, state.timings_ms)
            return {
                "response": normal_reply,
                "run_id": None,
                "action": "conversational"
            }                               # if no action is required, we will return the original message as a normal reply.
        
        
        # Step 3 : Execution stage : If the planner returned an action to execute, we will call the executor to execute the action using the tools registry and return the result.
        exec_start = time.perf_counter()
        result = await self.executor.execute(state , db)

        state.timings_ms["execution_ms"] =  round((time.perf_counter() - exec_start) * 1000, 2)
        
        logger.info("stage_timings trace_id=%s timings=%s", state.trace_id, state.timings_ms)
        if isinstance(result, dict) and "run_id" in result:
            return result

        return {
            "response": result,
            "run_id": None
        }

        
