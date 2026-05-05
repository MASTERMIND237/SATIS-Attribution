from fastapi import APIRouter
from .endpoints import students, widgets, assignments, feedback

api_router = APIRouter()
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(widgets.router, prefix="/widgets", tags=["widgets"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
