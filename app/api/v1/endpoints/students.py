from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ....schemas.student import StudentCreate, StudentRead, StudentReadWithAssignments
from ....models.student import Student
from ....models.assignment import Assignment
from ....db.database import get_session

router = APIRouter()


@router.post("/", response_model=StudentRead)
def create_student(student: StudentCreate, session: Session = Depends(get_session)):
    db_student = session.exec(select(Student).where(Student.email == student.email)).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Un étudiant avec cet email existe déjà")
    db_student = Student(
        last_name=student.last_name,
        first_name=student.first_name,
        email=student.email
    )
    session.add(db_student)
    session.commit()
    session.refresh(db_student)
    return db_student


@router.get("/", response_model=List[StudentRead])
def list_students(session: Session = Depends(get_session)):
    students = session.exec(select(Student)).all()
    return students


@router.get("/{student_id}")
def get_student(student_id: int, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Étudiant non trouvé")
    
    # Construire la réponse manuellement
    assignments_data = []
    for assignment in student.assignments:
        widget = assignment.widget
        assignment_dict = {
            "id": assignment.id,
            "student_id": assignment.student_id,
            "widget_id": assignment.widget_id,
            "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
            "widget": {
                "name": widget.name if widget else f"Widget #{assignment.widget_id}",
                "description": widget.description if widget else "",
                "category": widget.category if widget else "Inconnue",
            }
        }
        assignments_data.append(assignment_dict)
    
    return {
        "id": student.id,
        "last_name": student.last_name,
        "first_name": student.first_name,
        "email": student.email,
        "created_at": student.created_at.isoformat() if student.created_at else None,
        "assignments": assignments_data,
    }