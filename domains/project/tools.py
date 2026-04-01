from core.tools import Tool
from domains.project.schemas import CreateProjectParams, DeleteProjectParams
from domains.project.service import ProjectService


# Tool adapters map validated planner params to service calls.
async def create_project_tool(user_id: str, params: CreateProjectParams, db):
    service = ProjectService(db)
    return await service.create_project(
        user_id=user_id,
        name=params.name,
        description=params.description,
    )


async def delete_project_tool(user_id: str, params: DeleteProjectParams, db):
    service = ProjectService(db)
    return await service.delete_project(
        user_id=user_id,
        project_id=params.project_id,
        name=params.name,
    )


# Registers project tools with risk and confirmation metadata.
def build_project_tools():
    return {
        "create_project": Tool(
            name="create_project",
            function=create_project_tool,
            schema=CreateProjectParams,
            risk="low",
            requires_confirmation=False,
        ),
        "delete_project": Tool(
            name="delete_project",
            function=delete_project_tool,
            schema=DeleteProjectParams,
            risk="high",
            requires_confirmation=True,
        ),
    }