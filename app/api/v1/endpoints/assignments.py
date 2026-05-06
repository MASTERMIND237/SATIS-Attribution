from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ....core.security import require_admin
from ....schemas.student import StudentWidgetChoice
from ....schemas.assignment import AssignmentRead
from ....models.student import Student
from ....models.assignment import Assignment
from ....services.assignment_service import AssignmentService
from ....db.database import get_session

router = APIRouter()


@router.post("/assign", response_model=List[AssignmentRead])
def assign_widgets(
    choice: StudentWidgetChoice,
    student_id: int,
    session: Session = Depends(get_session)
):
    if choice.widget_count not in [2, 3]:
        raise HTTPException(status_code=400, detail="Le nombre de widgets doit être 2 ou 3")
    
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Étudiant non trouvé")
    
    existing_assignments = session.exec(
        select(Assignment).where(Assignment.student_id == student_id)
    ).all()
    if existing_assignments:
        raise HTTPException(status_code=400, detail="Cet étudiant a déjà des widgets attribués")
    
    service = AssignmentService(session)
    try:
        assignments = service.auto_assign_widgets(student_id, choice.widget_count)
        return assignments
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summary", response_model=List[dict])
def get_assignments_summary(session: Session = Depends(get_session)):
    service = AssignmentService(session)
    return service.get_all_assignments()


@router.delete("/reset")
def reset_assignments(
    session: Session = Depends(get_session),
    _: None = Depends(require_admin),
):
    service = AssignmentService(session)
    service.reset_assignments()
    return {"message": "Toutes les attributions ont été réinitialisées"}
