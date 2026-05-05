from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


USEFULNESS_QUESTION = "Notre plateforme vous a t'elle ete utile ?"


class FeedbackSubmission(BaseModel):
    reaction: Literal["like", "dislike", "none"]


class FeedbackRead(BaseModel):
    student_id: int
    reaction: Optional[Literal["like", "dislike"]] = None
    question: str = USEFULNESS_QUESTION
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AdminFeedbackEntry(BaseModel):
    student_id: int
    student_name: str
    email: str
    reaction: Optional[Literal["like", "dislike"]] = None
    question: str = USEFULNESS_QUESTION


class AdminFeedbackSummary(BaseModel):
    question: str = USEFULNESS_QUESTION
    total_students: int
    likes: int
    dislikes: int
    no_response: int
