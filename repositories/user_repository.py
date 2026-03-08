# Repo / user_repositories : this file is responsible for handling all database interactions related to the User model,
#such as creating new users, retrieving user information, and updating user details.

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from models import User

class UserRepository:
    def __init__(self, db):
        self.db = db

    async def create_user(self, user_id: str, name: str | None = None):
        user = User(user_id=user_id, name=name)
        self.db.add(user)
        await self.db.commit() 
        return user

    async def get_user(self, user_id: str):
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
            )
        return result.scalar_one_or_none()
    
    
    """ this function is used to get the user if exists or create a new user if not exists,
      this will be useful in the orchestrator when we receive a message from a user, 
      we want to make sure that the user exists in the database before proceeding with the rest of the logic, 
      so we can use this function to get or create the user in one step"""
    
    async def get_or_create(self,user_id:str) :
        user = await self.get_user(user_id)

        # returns user if exists 
        if user :
            return user 
        
        # if user does not exist, we will create a new user and return it
        user = User(user_id=user_id)
        self.db.add(user)

        # We will try to commit the new user to the database, if there was a race condition.
        try :
            await self.db.commit()
            return user
        
        except IntegrityError:
            await self.db.rollback()
            return await self.get_user(user_id)


    