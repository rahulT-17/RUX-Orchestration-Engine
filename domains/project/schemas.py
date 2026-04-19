# domains / project / schemas.py : This file is responsible for defining the schemas for the project management tool.

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateProjectParams(BaseModel) :
    name : str = Field(..., min_length=3, max_length=99)
    description : str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(
        extra="forbid") 
    
    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None
    
class DeleteProjectParams(BaseModel) :
    project_id : int | None = None
    name : str | None = Field(default=None, max_length=99)

    model_config = ConfigDict(
        extra="forbid")
    
    @field_validator("name")
    @classmethod
    def normalize_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None