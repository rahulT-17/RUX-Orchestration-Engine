# domains / expense / schemas.py : This file is responsible for defining the schemas for the expense manager tool.

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import date


# Schema for the input parameters of the expense manager tool :
class ExpenseManagerParams(BaseModel) :
    action : Literal["log","analyze","set_budget","get_budget"]

    amount : Optional[float] = Field(None, gt=0)
    category : Optional[str] = None
    note : Optional[str] = None

    start_date : Optional[date] = None
    end_date : Optional[date] = None

    period : Optional[str] = None
    budget : Optional[float] = Field(None, gt=0)

    mode : Literal["hard","soft"] = "soft" # Default value here 

    model_config = ConfigDict(
        extra="forbid")