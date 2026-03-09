# Core / confirmation_manager.py => defines the ConfirmationManager class which is responsible for handling the confirmation process for high-risk actions which is sent by the "Executator" when a tool that requires confirmation is about to be executed. 
# It manages the pending confirmations in the memory and processes the user's response to either confirm or reject the action.
import json 
from repositories.confirmation_repository import ConfirmationRepository
from repositories.agent_run_repository import AgentRunRepository

class ConfirmationManager: 

    async def handle(self, state, db, tools_registry) :

        repo = ConfirmationRepository(db)

        pending = await repo.get_pending(state.user_id)

        if not pending :
            return None 
        
        reply = state.message.strip().lower()

        if reply == "yes" :
            tool = tools_registry.get(pending.action)    
            
            if not tool :
                return f"Unknown action '{pending.action}'"
            
            parameters = pending.parameters

            # FIX : ENSURES parameters are dict 
            if isinstance(parameters,str) :
                try :
                    parameters = json.loads(parameters)
                except Exception as e :
                    return "Stored confirmation parameters are corrupted"

            try :
                validated = tool.schema(**parameters)
            except Exception as e :
                return f"Invalid parameters during confirmation, Details : {e} "
            
            result = await tool.function(state.user_id, validated, db)

            # log the confirmed execution
            agentrun_repo = AgentRunRepository(db)
            await agentrun_repo.log_run(
                user_id=state.user_id,
                message=state.message,
                action=pending.action,
                parameters=parameters,
                result=result,
                latency=0.0  # confirmation flow doesn't track latency, use 0
            )


            await repo.mark_executed(pending.confirmation_id)
            return result
        
        elif reply == "no" :
            await repo.mark_rejected(pending.confirmation_id)
            return "Action cancelled as per your request."
        
        else :
            return "You have a pending confirmation. Please reply with 'yes' or 'no'."

 
    