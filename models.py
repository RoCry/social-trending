from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Comment(BaseModel):
    content: str
    author: str


class ViewPoint(BaseModel):
    statement: str
    support_percentage: float


class Perspective(BaseModel):
    title: str = Field(description="Concise but descriptive title")
    summary: str = Field(description="Comprehensive summary in one paragraph")
    sentiment: str = Field(description="Overall sentiment (positive/mixed/negative)")
    viewpoints: List[ViewPoint]


class Item(BaseModel):
    # Original data
    title: str
    url: str = Field(description="HN/Reddit URL, not the original URL")
    original_url: Optional[str] = Field(
        None, description="URL of the original content source, may same as url"
    )
    content: Optional[str] = Field(None, description="The original source content")
    content_html: Optional[str] = Field(
        None, description="The original source content in HTML format"
    )
    comments: List[Comment] = Field(default_factory=list)
    published_at: Optional[datetime] = None

    # System fields
    id: str = Field(description="Original ID or generated ID based on the URL")
    created_at: datetime
    updated_at: datetime

    # AI generated fields
    generated_at_comment_count: Optional[int] = Field(
        None, description="Comment count when AI generated"
    )
    ai_perspective: Optional[Perspective] = None
