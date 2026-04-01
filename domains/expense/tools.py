# domains / expense / tools.py : This file is responsible for defining the tools for the expense domain.

# Core imports:
from core.tools import Tool
from domains.expense.schemas import ExpenseManagerParams
from domains.expense.service import ExpenseService


async def expense_manager_tool(user_id:str, params: ExpenseManagerParams, db) :
        expense_service = ExpenseService(db)
        
        result = None
         
        # SET BUDGET : 
        if params.action == "set_budget" :
           
           if params.budget is None or params.start_date is None or params.end_date is None or params.category is None :
              return "Budget, start_date, end_date and category are required."
           
           result = await expense_service.set_budget(
                user_id = user_id,
                category = params.category, # default category is general if not provided
                amount = params.budget,
                start_date = params.start_date,
                end_date = params.end_date
            )
           
        # GET BUDGET :
        elif params.action == "get_budget" :
            result = await expense_service.get_budget(user_id, category=params.category)
            
        
        # LOG EXPENSE : 
        elif params.action == "log" :
            if params.amount is None or params.category is None :
                return "amount and category required for log action"
            
            result = await expense_service.log_expense(
                user_id = user_id,
                amount = params.amount,
                category = params.category,
                note = params.note,
                mode = params.mode
            )

        # ANALYZE : 
        elif params.action == "analyze" :
            result = await expense_service.analyze_expense(
                user_id = user_id,
                period = params.period,
                category=params.category
            )
            
            if result["status"] == "success":
                total = result["total"]
                period = result.get("period") or "selected period"
                category = result.get("category")

                if category and period:
                    return f"Total expense for {category} in {period}: {total}"

                if category:
                    return f"Total expense for {category}: {total}"

                if period:
                    return f"Total expense in {period}: {total}"

                return f"Total expense: {total}"

            return "Unable to analyze expenses."
            
        
        else :
            return f"Invalid expense action : {params.action}"
        
        print("DEBUG RESULT:" , result)
        

        if not isinstance(result,dict) : 
           return f"Unexpected result format: {result}"
        
        status = result.get("status")

        if status == "logged":
          return f"Expense logged successfully."

        if status == "logged_with_warning":
          return (
            f"Expense logged but budget exceeded.\n"
            f"Current: {result['attempted_total']} / Budget: {result['budget']}")
        
        if status == "rejected":
          return (
            f"Expense rejected. Budget exceeded.\n"
            f"Current: {result['current_total']} / Budget: {result['budget']}")
        
        if status == "success":
          return result.get("message", "Success.")
        
        if status == "failed" :
           return result.get("reason" , "operation failed.")

        if status == "none":
          return result.get("message", "No data.")

        return f"Unhandled status: {status}"


# This function is responsible for building the tools for the expense domain.
def build_expense_tools() :
    return {
        "expense_manager" : Tool(
            name="expense_manager",
            function=expense_manager_tool,
            schema=ExpenseManagerParams,
            risk="low",
            requires_confirmation=False,
        )
    }