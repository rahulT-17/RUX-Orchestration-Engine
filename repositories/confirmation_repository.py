# repositories/confirmation_repository.py => this file is responsible for handling all database interactions related to the Confirmation model, 
# such as creating new confirmations, retrieving existing ones, and updating confirmation status.

import json
from sqlalchemy import select, update
from models import Confirmation


class ConfirmationRepository:
    def __init__(self, db):
        self.db = db

    
    async def get_pending(self, user_id: str):
        result = await self.db.execute(
            select(Confirmation).where(
                Confirmation.user_id == user_id,
                Confirmation.status == "pending"
            )
            .order_by(Confirmation.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    
    async def create(self, user_id: str, action: str, parameters: dict):
        confirmation = Confirmation(
            user_id=user_id,
            action=action,
            parameters=parameters,
        )
        self.db.add(confirmation)
        await self.db.commit()
        return confirmation
    

    async def mark_executed(self, confirmation_id: int):
        await self.db.execute(
            update(Confirmation)
            .where(Confirmation.confirmation_id == confirmation_id)
            .values(status="executed")
        )
        await self.db.commit()

    async def mark_rejected(self, confirmation_id: int):
        await self.db.execute(
            update(Confirmation)
            .where(Confirmation.confirmation_id == confirmation_id)
            .values(status="rejected")
        )
        await self.db.commit()