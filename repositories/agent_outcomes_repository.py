# Repo / agent_outcomes_repository.py

from datetime import datetime
from sqlalchemy import select, update
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
    
    async def get_by_run(self, run_id:int, user_id:str):
        result = await self.db.execute(
            select(Agent_Outcomes).where(
                (Agent_Outcomes.run_id == run_id),
                (Agent_Outcomes.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()
    
    async def apply_feedback(
        self, 
        run_id: int, 
        user_id: str, 
        was_correct: bool, 
        correction: str | None = None) -> bool:

        result = await self.db.execute(
            update(Agent_Outcomes)
            .where(Agent_Outcomes.run_id == run_id, 
                   Agent_Outcomes.user_id == user_id
            )
            .values(
                was_correct=was_correct, 
                correction=correction, 
                corrected_at=datetime.utcnow()
            )
        )
        await self.db.commit()
        return result.rowcount > 0

