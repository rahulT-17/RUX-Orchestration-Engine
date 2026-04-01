# domains / project / schemas.py : This file is responsible for defining the schemas for the project management tool.

from pydantic import BaseModel, ConfigDict


class CreateProjectParams(BaseModel) :
    name : str
    description : str | None = None

    model_config = ConfigDict(
        extra="forbid") 

class DeleteProjectParams(BaseModel) :
    project_id : int | None = None
    name : str | None = None

    model_config = ConfigDict(
        extra="forbid")