# repositories / budget_repository.py : This file is used for defining the functions to interact with the database for budget related operations.

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models import Budget 
from datetime import date 

class BudgetRepository :

    def __init__(self, db:AsyncSession):
        self.db = db

    async def create_budget(
        self,
        user_id: str,
        amount: float, 
        category: str, 
        start_date: date, 
        end_date: date
    ):
        
        # Prevent overlapping budget for the same category and user:
        overlap_check = await self.db.execute(
            select(Budget)
            .where(Budget.user_id == user_id,
                     Budget.category == category,
                     and_(
                            Budget.start_date <= end_date,
                            Budget.end_date >= start_date
                     )
                )
        )
        
        # If an overlapping budget exists, we should not create a new one and instead return None or raise an exception to indicate the failure due to overlap:
        if overlap_check.scalar_one_or_none():

            return None # Indicate failure due to overlap
        

        # here we are sure that there is no overlap and we can safely create the budget:

        budget = Budget(
            user_id=user_id,
            amount=amount,
            category=category.lower(),
            start_date=start_date,
            end_date=end_date
        )

        self.db.add(budget)
        await self.db.commit()
        await self.db.refresh(budget)  # Refresh to get the generated budget_id

        return budget
    
    # Get active budget for a user and category on a specific date (usually today):
    async def get_active_budget(
            self, 
            user_id: str, 
            category: str, 
            today:date
        ):

        result = await self.db.execute(
            select(Budget)
            .where(Budget.user_id == user_id)
            .where(Budget.category == category)
            .where(Budget.start_date <= today)
            .where(Budget.end_date >= today)
        )

        return result.scalar_one_or_none() 