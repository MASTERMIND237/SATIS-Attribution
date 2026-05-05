from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ....schemas.student import StudentCreate, StudentRead, StudentReadWithAssignments
from ....models.student import Student
from ....db.database import get_session

router = APIRouter()


@router.post("/", response_model=StudentRead)
def create_student(student: StudentCreate, session: Session = Depends(get_session)):
    db_student = session.exec(select(Student).where(Student.email == student.email)).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Un étudiant avec cet email existe déjà")
    db_student = Student.from_orm(student)
    session.add(db_student)
    session.commit()
    session.refresh(db_student)
    return db_student


@router.get("/", response_model=List[StudentRead])
def list_students(session: Session = Depends(get_session)):
    students = session.exec(select(Student)).all()
    return students


@router.get("/{student_id}", response_model=StudentReadWithAssignments)
def get_student(student_id: int, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Étudiant non trouvé")
    return student
