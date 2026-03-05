from pydantic import BaseModel
from typing import Optional

class JobOut(BaseModel):
    id: int
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    first_seen_at: Optional[str] = None