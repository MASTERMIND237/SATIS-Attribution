from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AssignmentBase(BaseModel):
    student_id: int
    widget_id: int


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentRead(AssignmentBase):
    id: int
    created_at: datetime


class AssignmentReadWithWidget(AssignmentRead):
    widget: dict
