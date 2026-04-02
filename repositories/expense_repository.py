# STUB
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import Expense
from datetime import date

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