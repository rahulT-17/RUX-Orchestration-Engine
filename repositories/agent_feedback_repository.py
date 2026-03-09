# AgentFeedbackRepository is responsible for storing and retrieving feedback on agent actions, which can be used for improving the agent's performance over time. It interacts with the database to save feedback entries and fetch them when needed for analysis or training purposes.

from models import AgentFeedback

class AgentFeedbackRepository :

    def __init__(self, db) :
        self.db = db
    
    async def record_feedback(
            self,
            user_id: str, 
            run_id: int, 
            domain: str, 
            task_type: str,
            was_correct: bool,
            correction: str | None = None) :
        
        feedback = AgentFeedback(
            user_id = user_id,
            run_id = run_id,
            domain = domain,
            task_type = task_type,
            was_correct = was_correct,
            correction = correction
        )
        self.db.add(feedback)
        await self.db.commit()