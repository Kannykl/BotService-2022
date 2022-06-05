"""Task schemas"""

from pydantic import BaseModel, Field, EmailStr
import uuid
from typing import Literal


class Task(BaseModel):
    """Task that creates admin for create bots."""
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    owner: EmailStr
    status: str
    count: int


class BoostTask(Task):
    """Task that creates user for boost stat."""
    boost_type: str
    link: str


class BoostTaskIn(BaseModel):
    """Info for create boost task"""
    link: str
    count: int
    boost_type: Literal["like", "sub"]
