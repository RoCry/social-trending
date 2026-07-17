from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class Comment(BaseModel):
    content: str
    author: str


class Viewpoint(BaseModel):
    statement: str
    support_percentage: float


class Perspective(BaseModel):
    title: str = Field(description="Concise but descriptive title")
    summary: str = Field(description="Comprehensive summary in one paragraph")
    sentiment: str = Field(description="Overall sentiment (positive/mixed/negative)")
    viewpoints: list[Viewpoint]


class Item(BaseModel):
    # Original data
    title: str
    url: str = Field(description="HN/Reddit URL, not the original URL")
    original_url: Annotated[
        str | None,
        Field(description="URL of the original content source; may match url"),
    ] = None
    content: Annotated[str | None, Field(description="The original source content")] = None
    content_html: Annotated[str | None, Field(description="The original source content in HTML format")] = None
    comments: list[Comment] = Field(default_factory=list)
    published_at: datetime | None = None

    # System fields
    id: str = Field(description="Original ID or generated ID based on the URL")
    created_at: datetime
    updated_at: datetime

    # AI generated fields
    generated_at_comment_count: Annotated[int | None, Field(description="Comment count when AI generated")] = None
    ai_perspective: Perspective | None = None
