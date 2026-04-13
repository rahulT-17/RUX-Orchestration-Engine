# REPO / agent_run_repository.py => This file contains the repository class for managing agent run records in the database, including creating new runs and retrieving past runs for a user.

from models import AgentRun

class AgentRunRepository :

    def __init__(self, db) :
        self.db = db
    
    async def log_run(self, user_id, message, action, parameters, result, latency) :
        run = AgentRun(
            user_id = user_id,
            message = message,
            action = action,
            parameters = parameters,
            result = result,
            latency = latency
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run) # Refresh the instance to get the generated run_id (important for linking with outcomes and feedback)
        return run.run_id