from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class UsefulnessFeedbackBase(SQLModel):
    student_id: int = Field(foreign_key="student.id", unique=True)
    reaction: str


class UsefulnessFeedback(UsefulnessFeedbackBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    student: "Student" = Relationship(back_populates="feedback")
