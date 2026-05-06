from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ....core.security import require_admin
from ....db.database import get_session
from ....models.feedback import UsefulnessFeedback
from ....models.student import Student
from ....schemas.feedback import (
    AdminFeedbackEntry,
    AdminFeedbackSummary,
    FeedbackRead,
    FeedbackSubmission,
    USEFULNESS_QUESTION,
)

router = APIRouter()


@router.put("/students/{student_id}", response_model=FeedbackRead)
def submit_feedback(
    student_id: int,
    payload: FeedbackSubmission,
    session: Session = Depends(get_session),
):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Étudiant non trouvé")

    existing_feedback = session.exec(
        select(UsefulnessFeedback).where(UsefulnessFeedback.student_id == student_id)
    ).first()

    if payload.reaction == "none":
        if existing_feedback:
            session.delete(existing_feedback)
            session.commit()
        return FeedbackRead(student_id=student_id, reaction=None)

    now = datetime.utcnow()
    if existing_feedback:
        existing_feedback.reaction = payload.reaction
        existing_feedback.updated_at = now
        session.add(existing_feedback)
        session.commit()
        session.refresh(existing_feedback)
        return FeedbackRead(
            student_id=student_id,
            reaction=existing_feedback.reaction,
            created_at=existing_feedback.created_at,
            updated_at=existing_feedback.updated_at,
        )

    feedback = UsefulnessFeedback(
        student_id=student_id,
        reaction=payload.reaction,
        created_at=now,
        updated_at=now,
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return FeedbackRead(
        student_id=student_id,
        reaction=feedback.reaction,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
    )


@router.get("/students/{student_id}", response_model=FeedbackRead)
def get_student_feedback(student_id: int, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Étudiant non trouvé")

    feedback = session.exec(
        select(UsefulnessFeedback).where(UsefulnessFeedback.student_id == student_id)
    ).first()
    if not feedback:
        return FeedbackRead(student_id=student_id, reaction=None)

    return FeedbackRead(
        student_id=student_id,
        reaction=feedback.reaction,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
    )


@router.get("/admin/summary", response_model=AdminFeedbackSummary)
def get_feedback_summary(
    session: Session = Depends(get_session),
    _: None = Depends(require_admin),
):
    students = session.exec(select(Student)).all()
    feedbacks = session.exec(select(UsefulnessFeedback)).all()

    likes = sum(1 for feedback in feedbacks if feedback.reaction == "like")
    dislikes = sum(1 for feedback in feedbacks if feedback.reaction == "dislike")

    return AdminFeedbackSummary(
        question=USEFULNESS_QUESTION,
        total_students=len(students),
        likes=likes,
        dislikes=dislikes,
        no_response=max(len(students) - len(feedbacks), 0),
    )


@router.get("/admin/responses", response_model=List[AdminFeedbackEntry])
def list_feedback_responses(
    session: Session = Depends(get_session),
    _: None = Depends(require_admin),
):
    students = session.exec(select(Student)).all()
    feedbacks = session.exec(select(UsefulnessFeedback)).all()
    feedback_by_student_id = {feedback.student_id: feedback for feedback in feedbacks}

    return [
        AdminFeedbackEntry(
            student_id=student.id,
            student_name=f"{student.last_name} {student.first_name}",
            email=student.email,
            reaction=feedback_by_student_id.get(student.id).reaction if feedback_by_student_id.get(student.id) else None,
            question=USEFULNESS_QUESTION,
        )
        for student in students
    ]
