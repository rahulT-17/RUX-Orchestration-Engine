# Repo / agent_outcomes_repository.py

from models import Agent_Outcomes

class AgentOutcomesRepository :

    def __init__(self, db) :
        self.db = db

    async def record_outcome(
            self, 
            run_id,
            user_id,    
            domain, 
            task_type, 
            was_correct, 
            correction: str | None = None
        ):
        outcome = Agent_Outcomes(
            run_id=run_id,
            user_id=user_id,
            domain=domain,
            task_type=task_type,
            was_correct=was_correct,
            correction=correction
        )
        self.db.add(outcome)
        await self.db.commit()