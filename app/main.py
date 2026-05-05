from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.database import get_database_state, initialize_database
from .api.v1 import api_router

app = FastAPI(
    title="SATIS-Attribution API",
    description="API pour l'attribution automatique de widgets Flutter aux étudiants",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def on_startup():
    initialize_database()


@app.get("/health/database")
def database_health():
    return get_database_state()
