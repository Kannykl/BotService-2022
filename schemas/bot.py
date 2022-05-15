"""Bot schemas"""

import uuid

from pydantic import BaseModel, Field


class Bot(BaseModel):
    """Bot representation in database"""
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    username: str
    password: str
    is_busy: bool = False


class BotIn(BaseModel):
    """Bot data for creating an instance."""
    username: str
    password: str
