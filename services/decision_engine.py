# Decision Engine for evaluating and selecting the best course of action :

from services.critic_service import CriticService

class DecisionEngine :

    def __init__ (self, critic_service) :
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

        status = result.get("status") if isinstance(result, dict) else None

        """
        Deterministic reasoning based on predefined rules for specific domains and task types."""

        if domain == "expense" :
             
            if task_type == "log" :
                if status == "logged_with_warning" :
                    return f"Warning: {result.get('reason')} — {result.get('attempted_total')} of {result.get('budget')} budget used."
                
                elif status == "rejected" :
                    return f"Expense rejected: {result.get('reason')} — {result.get('attempted_total')} of {result.get('budget')} budget used."
                return None # clean log no observation needed
            
            elif task_type == "set_budget":
                return "Budget set. Future expenses in this category will be validated against it."
            
            elif task_type == "analyze" :
                # raw dict came through somehow
                if isinstance(result,dict):
                    return f"Analysis complete for {result.get('category', 'all categories')} over {result.get('period', 'all time')}."
                return None  # already a formatted string, nothing to add
            
            elif task_type == "get_budget" :
                return None # result already speaks for itself
            
        if domain == "project" :
            if task_type == "create_project" :
                return None # creation successful, no observation needed.

            elif task_type == "delete_project" :
                return "Project deletion is irreversible."
        
        return None
                
