from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class StudentBase(SQLModel):
    last_name: str = Field(index=True)
    first_name: str = Field(index=True)
    email: str = Field(index=True, unique=True)


class Student(StudentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assignments: List["Assignment"] = Relationship(back_populates="student", sa_relationship_kwargs={"lazy": "selectin"})
    feedback: Optional["UsefulnessFeedback"] = Relationship(
        back_populates="student",
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )


class StudentCreate(StudentBase):
    pass


class StudentRead(StudentBase):
    id: int
    created_at: datetime


class StudentReadWithAssignments(StudentRead):
    assignments: List["AssignmentRead"] = []
