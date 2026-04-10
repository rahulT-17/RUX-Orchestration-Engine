# domains / expense / tools.py : This file is responsible for defining the tools for the expense domain.

# Core imports:
from core.tools import Tool
from core.tool_response import ToolResponse, ToolStatus
from domains.expense.schemas import ExpenseManagerParams
from domains.expense.service import ExpenseService


async def expense_manager_tool(user_id:str, params: ExpenseManagerParams, db) :
        expense_service = ExpenseService(db)
         
        # SET BUDGET : 
        if params.action == "set_budget" :
           
           if (params.budget is None
                or params.start_date is None 
                or params.end_date is None 
                or params.category is None
                ):
              return ToolResponse(
                status=ToolStatus.FAILED,
                message="budget, category, start_date and end_date are required for set_budget action", 
                error="Missing required parameters for set_budget action"
                )
           
           result = await expense_service.set_budget(
                user_id = user_id,
                category = params.category, # default category is general if not provided
                amount = params.budget,
                start_date = params.start_date,
                end_date = params.end_date
            )
           
        # GET BUDGET :
        elif params.action == "get_budget" :
            result = await expense_service.get_budget(
                user_id,
                category=params.category
                )
            
        
        # LOG EXPENSE : 
        elif params.action == "log" :
            if params.amount is None or params.category is None :
                return ToolResponse(
                    status=ToolStatus.FAILED,   
                    message="amount and category are required for log action",
                    error="Missing required parameters for log action",
                )

            
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
                    return ToolResponse(
                        status=ToolStatus.SUCCESS,
                        message=f"Total expense for {category} in {period}: {total}",
                        data=result
                    )

                if category:
                    return ToolResponse(
                        status=ToolStatus.SUCCESS,
                        message=f"Total expense for {category}: {total}",
                        data=result 
                    )

                if period:
                    return ToolResponse(
                        status=ToolStatus.SUCCESS,
                        message=f"Total expense in {period}: {total}",
                        data=result 
                    )

                return ToolResponse(
                    status=ToolStatus.SUCCESS,
                    message=f"Total expense: {total}",
                    data = result
                )

            return ToolResponse(
                status=ToolStatus.FAILED,
                message="Unable to analyze expenses. Please try again later.",
                error= "Analaysis failed"
            )
            
        
        else :
            return ToolResponse(
                status=ToolStatus.FAILED,
                message=f"Invalid action: {params.action}",
                error="Unsupported action"
            )   
        

        if not isinstance(result,dict) : 
           return ToolResponse(
            status=ToolStatus.FAILED,
            message="Unexpected result format {result} ",
            error="Service returned non-dict result"
           )
        
        status = result.get("status")

        if status == "logged":
          return ToolResponse(
            status=ToolStatus.SUCCESS,
            message="Expense logged successfully.",
            data=result
          )

        if status == "logged_with_warning":
          return ToolResponse(
            status=ToolStatus.PARTIAL,
            message=(
                "Expense logged but budget exceeded.\n"
                f"Current: {result['attempted_total']} / Budget: {result['budget']}"
            ),
            data=result,
            metadata={"warning": result.get("reason")},
        )
        
        if status == "rejected":
          return ToolResponse(
            status=ToolStatus.FAILED,
            message=(
                "Expense rejected. Budget exceeded.\n"
                f"Current: {result['current_total']} / Budget: {result['budget']}"
            ),
            error=result.get("reason", "Budget exceeded"),
            data=result
          )
        
        if status == "success":
          return ToolResponse(
            status=ToolStatus.SUCCESS,
            message=result.get("message", "Success."),
            data=result
          )
        
        if status == "failed" :
           return ToolResponse(
             status=ToolStatus.FAILED,
             message=result.get("reason", "Operation failed."),
             error=result.get("error", "Operation failed"),
             data=result
           )

        if status == "none":
          return ToolResponse(
            status=ToolStatus.PARTIAL,
            message=result.get("message", "No data."),
            data=result
          )

        return ToolResponse(
            status=ToolStatus.FAILED,
            message= f"Unexpected result status: {status}",
            error="Service returned unexpected status",
            data=result
        )

# This function is responsible for building the tools for the expense domain.
def build_expense_tools() :
    return {
        "expense_manager" : Tool(
            name="expense_manager",
            function=expense_manager_tool,
            schema=ExpenseManagerParams,    
            domain="expense",
            task_type=None,
            risk="low",
            requires_confirmation=False,
        )
    }