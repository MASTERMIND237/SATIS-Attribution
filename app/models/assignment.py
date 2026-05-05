from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class AssignmentBase(SQLModel):
    student_id: int = Field(foreign_key="student.id")
    widget_id: int = Field(foreign_key="widget.id")


class Assignment(AssignmentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    student: "Student" = Relationship(back_populates="assignments")
    widget: "Widget" = Relationship(back_populates="assignments")


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentRead(AssignmentBase):
    id: int
    created_at: datetime
    widget: "WidgetRead"


Assignment.update_forward_refs()
