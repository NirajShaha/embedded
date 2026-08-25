from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class AttributeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class AttributeGroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    attributes: list[AttributeRead]


class SelectionsRead(BaseModel):
    page: int
    attribute_ids: list[int]


class SelectionsUpdate(BaseModel):
    attribute_ids: list[int]