# domains / expense / schemas.py : This file is responsible for defining the schemas for the expense manager tool.

from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from typing import Optional, Literal
from datetime import date


# Schema for the input parameters of the expense manager tool :
class ExpenseManagerParams(BaseModel) :
    action : Literal["log","analyze","set_budget","get_budget"]

    amount : Optional[float] = Field(None, gt=0)
    category : Optional[str] = Field(None, max_length=100)
    note : Optional[str] = Field(None, max_length=200)

    start_date : Optional[date] = None
    end_date : Optional[date] = None

    period : Optional[str] = Field(None, max_length=30)
    budget : Optional[float] = Field(None, gt=0)

    mode : Literal["hard","soft"] = "soft" # Default value here 

    model_config = ConfigDict(
        extra="forbid")
    
    @field_validator("category", "note", "period")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None
    
    @model_validator(mode="after")
    def validate_by_action(self):
        if self.action == "set_budget":
            missing = []
            if not self.category or not self.category.strip():
                missing.append("category")
            if self.budget is None:
                missing.append("budget")
            if self.start_date is None:
                missing.append("start_date")
            if self.end_date is None:
                missing.append("end_date")

            if missing:
                raise ValueError(
                    f"Missing required fields for set_budget: {', '.join(missing)}"
                )

        if self.action == "get_budget":
            missing = []
            if not self.category or not self.category.strip():
                missing.append("category")

            forbidden = []
            if self.budget is not None:
                forbidden.append("budget")
            if self.start_date is not None:
                forbidden.append("start_date")
            if self.end_date is not None:
                forbidden.append("end_date")
            if self.amount is not None:
                forbidden.append("amount")

            if missing:
                raise ValueError(
                    f"Missing required fields for get_budget: {', '.join(missing)}"
                )

            if forbidden:
                raise ValueError(
                    f"Fields not allowed for get_budget: {', '.join(forbidden)}"
                )

        return self