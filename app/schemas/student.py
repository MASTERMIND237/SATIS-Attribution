from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


class StudentBase(BaseModel):
    last_name: str
    first_name: str
    email: EmailStr


class StudentCreate(StudentBase):
    pass


class StudentRead(StudentBase):
    id: int
    created_at: datetime


class StudentReadWithAssignments(StudentRead):
    assignments: List[dict] = []


class StudentWidgetChoice(BaseModel):
    widget_count: int
