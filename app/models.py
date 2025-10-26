from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    @classmethod
    def validate(cls, v):
        return ObjectId(str(v))

class Blog(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str
    slug: str
    content_md: str
    cover_url: Optional[str] = None
    tags: List[str] = []
    published_at: datetime = Field(default_factory=datetime.utcnow)

class Profile(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    employment_history: List[dict] = []  # [{role, company, start, end, description}]
    contact_email: Optional[EmailStr] = None
    socials: dict = {}  # e.g. {"github": "...", "linkedin": "..."}
