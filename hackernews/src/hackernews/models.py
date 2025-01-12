from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class Comment(BaseModel):
    id: int
    text: str
    by: Optional[str] = None
    time: datetime
    kids: List[int] = Field(default_factory=list)
    parent: Optional[int] = None
    deleted: bool = False
    dead: bool = False
    replies: List['Comment'] = Field(default_factory=list)

class Story(BaseModel):
    id: int
    title: str
    url: Optional[str] = None
    text: Optional[str] = None
    by: str
    time: datetime
    score: int
    descendants: int = 0
    kids: List[int] = Field(default_factory=list)
    comments: List[Comment] = Field(default_factory=list)

class HNResponse(BaseModel):
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    stories: List[Story] = Field(default_factory=list) 