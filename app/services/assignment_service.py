from typing import List, Optional
from sqlmodel import Session, select
from ..models.student import Student
from ..models.widget import Widget
from ..models.assignment import Assignment


class AssignmentService:
    def __init__(self, session: Session):
        self.session = session

    def get_available_widgets(self, exclude_widget_ids: Optional[List[int]] = None) -> List[Widget]:
        statement = select(Widget)
        if exclude_widget_ids:
            statement = statement.where(Widget.id.not_in(exclude_widget_ids))
        return self.session.exec(statement).all()

    def get_assigned_widget_ids(self) -> List[int]:
        statement = select(Assignment.widget_id)
        return list(self.session.exec(statement).unique())

    def auto_assign_widgets(self, student_id: int, widget_count: int) -> List[Assignment]:
        assigned_widget_ids = self.get_assigned_widget_ids()
        available_widgets = self.get_available_widgets(assigned_widget_ids)
        
        if len(available_widgets) < widget_count:
            raise ValueError(f"Plus aucun widget disponible. Veuillez contacter l'enseignant.")
        
        assignments = []
        for i in range(widget_count):
            widget = available_widgets[i]
            assignment = Assignment(student_id=student_id, widget_id=widget.id)
            self.session.add(assignment)
            assignments.append(assignment)
        
        self.session.commit()
        for assignment in assignments:
            self.session.refresh(assignment)
        
        return assignments

    def get_student_assignments(self, student_id: int) -> List[Assignment]:
        statement = select(Assignment).where(Assignment.student_id == student_id)
        return self.session.exec(statement).all()

    def get_all_assignments(self) -> List[dict]:
        statement = select(Assignment, Student.last_name, Student.first_name, Widget.name.label("widget_name"))
        statement = statement.join(Student, Assignment.student_id == Student.id)
        statement = statement.join(Widget, Assignment.widget_id == Widget.id)
        results = self.session.exec(statement).all()

        return [
            {
                "id": r[0].id,
                "student_name": f"{r[1]} {r[2]}",
                "widget_name": r[3]
            }
            for r in results
        ]

    def reset_assignments(self) -> None:
        statement = select(Assignment)
        assignments = self.session.exec(statement).all()
        for assignment in assignments:
            self.session.delete(assignment)
        self.session.commit()
