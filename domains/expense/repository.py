# domains / expense / repository.py : This file is responsible for defining the functions to interact with the database for expense related operations.

from typing import Optional
from datetime import date

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

# models :
from models import Expense, Budget


class ExpenseRepository :

    def __init__(self, db:AsyncSession):
        self.db = db 

    async def log_expense(self, user_id: str, amount: float,  category: str , note: str | None):
        expense = Expense(
            user_id=user_id,
            amount=amount,
            category=category,
            note=note
        )
        self.db.add(expense)
        await self.db.commit()
        await self.db.refresh(expense)  # Refresh to get the generated expense_id
        return expense 
    
    # Get total expenses for a user, optionally filtered by category and date range
    async def get_total_between(self, user_id: str, category: str, start_date: date , end_date: date ):

        result =  await self.db.execute(
            select(func.coalesce(func.sum(Expense.amount), 0.0))
            .where(Expense.user_id == user_id)
            .where(Expense.category == category.lower())
            .where(Expense.created_at >= start_date)
            .where(Expense.created_at <= end_date)  
        )
        return result.scalar()
    
    # Get total expenses for a user, optionally filtered by category
    async def get_total_by_period(
            self, 
            user_id: str, 
            category: str | None=None,
            start_date: date | None = None,
            end_date: date | None = None
        ) -> float:

        query = select(func.coalesce(func.sum(Expense.amount), 0.0))
        
        query = query.where(Expense.user_id == user_id)

        if category:
            query = query.where(Expense.category == category.lower())

        if start_date:
           query = query.where(Expense.created_at >= start_date)
        if end_date:
           query = query.where(Expense.created_at <= end_date)

        result = await self.db.execute(query)
        return result.scalar_one()


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