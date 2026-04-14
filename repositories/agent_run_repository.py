# REPO / agent_run_repository.py => This file contains the repository class for managing agent run records in the database, including creating new runs and retrieving past runs for a user.

from fastapi.encoders import jsonable_encoder

from models import AgentRun

class AgentRunRepository :

    def __init__(self, db) :
        self.db = db

    @staticmethod
    def _as_json_safe(payload):
        # JSON columns cannot store native date/datetime objects directly.
        return jsonable_encoder(payload) if payload is not None else None
    
    async def log_run(self, user_id, message, action, parameters, result, latency) :
        run = AgentRun(
            user_id = user_id,
            message = message,
            action = action,
            parameters = self._as_json_safe(parameters),
            result = self._as_json_safe(result),
            latency = latency
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run) # Refresh the instance to get the generated run_id (important for linking with outcomes and feedback)
        return run.run_id