# core / tool registry.py :

""" This file defines the tools registry which is a central place to register all the tools that the agent can use to perform actions (create project, delete project, etc.)
 Each tool is defined with its function, input schema, risk level, and whether it requires confirmation before execution. The agent core will use this registry to look up and execute the appropriate tool based on the user message and the LLM response.
 The tools registry allows us to easily manage and organize the different actions that the agent can perform, and also to add new tools in the future without having to change the core logic of the agent. """


# Project composition imports:
from domains.project.tools import build_project_tools

# Expense composition imports:
from domains.expense.tools import build_expense_tools



# schemas for the input parameters of the tools (these will be used for validation before executing the tool functions) :

## Tools Resgistry == this will hold all the tools that the agent can use to perform actions (create project, delete project, etc.)

def bulid_tools_registry(db) :
    """ Passing memory as instance to the tools registry so that the tools 
    can use it to perform actions on the database (create project, delete project, etc.) """

    
    
         
    # Compose domain bundles here; keep domain logic outside the core registry.
    tools = {}

    tools.update(build_project_tools())

    # updating the tools registry with the expense tools
    tools.update(build_expense_tools())
    return tools