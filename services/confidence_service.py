# services/confidence_service.py : This file is responsible for implementing the business logic related to recording user feedback on the agent's responses

from sqlalchemy import Integer, Float, select, func , cast
from models import Agent_Outcomes

class ConfidenceService :
    def __init__(self, db) :
        self.db = db

    async def get_confidence(self, user_id, domain, task_type) :
         
        """this query calculates the total number of feedback samples and the average correctness for a specific run_id, domain, and task_type.
          The was_correct field is cast to a Float to calculate the average accuracy as a value between 0 and 1.
          The results are returned as a dictionary containing the total samples and the calculated accuracy"""
        
        query = (
            select(
                func.count().label("samples"),
                func.avg(cast(cast(Agent_Outcomes.was_correct, Integer), Float)).label("accuracy")
            )
            .where(
                Agent_Outcomes.user_id == user_id,
                Agent_Outcomes.domain == domain,
                Agent_Outcomes.task_type == task_type
            )
        )
        result = await self.db.execute(query)
        row = result.first()

        if not row or row.samples < 5:
            return {"confidence": None,
                    "samples": row.samples if row else 0,}
        
        return {"confidence": round(row.accuracy * 100, 2),
                "samples": row.samples }