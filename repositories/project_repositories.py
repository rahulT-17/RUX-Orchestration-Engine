# repositories / project_repositories : Handles the Memorymanager project logic here :

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select , delete 
from models import Project 

class ProjectRepository :

    def __init__(self, db:AsyncSession):
        self.db = db 

    async def create_project(self, user_id: str, name: str, description: str | None = None):
        project = Project(
            user_id=user_id, 
            name=name, 
            description=description
        )
        self.db.add(project)
        await self.db.commit()

        return project.project_id
    
    async def get_project(self, user_id: str, name: str):     
        result = await self.db.execute(
            select(Project).where(
                (Project.user_id == user_id) & (Project.name == name)
            )
        )
        
        return result.scalar_one_or_none() 
    
    async def delete_project(self, project_id: int):
        result = await self.db.execute(
            delete(Project).where(Project.project_id == project_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def list_projects(self, user_id: str):
        result = await self.db.execute(
            select(Project).where(Project.user_id == user_id)
        )
        return result.scalars().all()
         