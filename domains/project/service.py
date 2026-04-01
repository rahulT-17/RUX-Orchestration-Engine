from domains.project.repository import ProjectRepository

class ProjectService:
    # Service layer keeps project business flow and user-facing outcomes.
    def __init__(self, db):
        self.repository = ProjectRepository(db)

    # Create flow delegates persistence and returns a readable confirmation.
    async def create_project(self, user_id: str, name: str, description: str | None = None):
        project_id = await self.repository.create_project(
            user_id=user_id,
            name=name,
            description=description,
        )
        return f"Project '{name}' created successfully with ID: {project_id}"

    # Delete supports direct id deletion or user-scoped name lookup.
    async def delete_project(
        self,
        user_id: str,
        project_id: int | None = None,
        name: str | None = None,
    ):
        # Deletion by ID is straightforward and prioritized if provided.
        if project_id is not None:
            success = await self.repository.delete_project(project_id=project_id)
            if not success:
                return {"error": f"No project found with ID {project_id}"}
            
            return f"Project with ID {project_id} deleted successfully"

        # If no ID, attempt deletion by name within the user's projects.
        if name:
            project = await self.repository.get_project(user_id=user_id, name=name)
            if not project:
                return {"error": f"No project found with name '{name}' for the user."}

            await self.repository.delete_project(project.project_id)
            return f"Project '{name}' deleted successfully"

        return {"error": "Provide either project_id or name to delete a project."}
        
        