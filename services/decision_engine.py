# Decision Engine for evaluating and selecting the best course of action :

from services.critic_service import CriticService

class DecisionEngine :

    def __init__ (self, db, critic_service) :
        self.db = db
        self.critic_service = critic_service


    async def evaluate(self, user_id, message, domain, task_type, result) :

        """
        Generates system reasoning and LLM-based critique for the given user message, action, and tool result."""

        # deterministic reasoning :
        system_analysis = await self.system_reasoning(domain, task_type, result)

        # LLM based critique :
        critic_analysis = None
        
        # Only call critic for important domains
        if domain in ["expense", "project"] :
            critic_analysis = await self.critic_service.critique(
                message,
                domain,
                task_type,
                result
            )
    
        return {
            "system_analysis" : system_analysis,
            "critic_analysis" : critic_analysis
        }
    
    async def system_reasoning(self, domain, task_type, result) :

        """
        Deterministic reasoning based on predefined rules for specific domains and task types."""

        if domain == "expense" :
             
            if task_type == "log" :
                return "Expense logged"

            elif task_type == "set_budget":
                return "Budget created successfully. Future expense will be validated."
            
            elif task_type == "analyze" :
                return "Expense analysis generated from transaction history."
            
            else :
                return "Expection : not yet "
            
        if domain == "project" :
            if task_type == "create_project" :
                return "Project creation recorded."

            elif task_type == "delete_project" :
                return "Project deletion is irreversible."
        
        return None
                
