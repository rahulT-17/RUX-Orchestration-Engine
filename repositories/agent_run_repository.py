# REPO / agent_run_repository.py => This file contains the repository class for managing agent run records in the database, including creating new runs and retrieving past runs for a user.

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, update

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

    async def update_run_result(self, run_id, result) :
        """Patch the run.result JSON after downstream metrics are computed."""
        await self.db.execute(
            update(AgentRun)
            .where(AgentRun.run_id == run_id)
            .values(result=self._as_json_safe(result))
        )
        await self.db.commit()

    async def merge_run_metadata(self, run_id, metadata_updates):
        """Merge keys into run.result.metadata without replacing other result fields."""
        if not metadata_updates:
            return

        query = await self.db.execute(
            select(AgentRun.result).where(AgentRun.run_id == run_id)
        )
        current_result = query.scalar_one_or_none() or {}
        if not isinstance(current_result, dict):
            current_result = {}

        metadata = current_result.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        metadata.update(metadata_updates)
        current_result["metadata"] = metadata

        await self.db.execute(
            update(AgentRun)
            .where(AgentRun.run_id == run_id)
            .values(result=self._as_json_safe(current_result))
        )
        await self.db.commit()