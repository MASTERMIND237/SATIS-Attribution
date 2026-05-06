import sys
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.database import get_database_state, initialize_database, engine
from .api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Démarrage et arrêt graceful de l'application"""
    print("=" * 60, file=sys.stderr)
    print("🚀 SATIS-Attribution API - Démarrage...", file=sys.stderr)
    
    # Tenter d'initialiser la base de données
    try:
        initialize_database()
        print("✅ Base de données initialisée avec succès", file=sys.stderr)
    except Exception as e:
        print(f"⚠️  Impossible d'initialiser la base de données: {e}", file=sys.stderr)
        print("   L'API démarre mais les routes nécessitant la DB seront indisponibles.", file=sys.stderr)
        if hasattr(e, '__cause__') and e.__cause__:
            print(f"   Cause: {e.__cause__}", file=sys.stderr)
    
    print("=" * 60, file=sys.stderr)
    
    yield  # L'application tourne ici
    
    print("👋 Arrêt de l'API SATIS-Attribution...", file=sys.stderr)


app = FastAPI(
    title="SATIS-Attribution API",
    description="API pour l'attribution automatique de widgets Flutter aux étudiants",
    version="1.0.0",
    lifespan=lifespan  # Remplacer @app.on_event("startup")
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes API
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Route racine - Test simple"""
    return {
        "status": "online",
        "app": "SATIS-Attribution API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health/database")
async def database_health():
    """
    Health check pour Render.
    Vérifie l'état de la connexion à la base de données.
    """
    state = get_database_state()
    
    # Vérifier si on peut se connecter
    db_status = "unknown"
    try:
        if engine is not None:
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            db_status = "connected"
        else:
            db_status = "not_configured"
    except Exception as e:
        db_status = "error"
        state["connection_error"] = str(e)
    
    return {
        **state,
        "connection_status": db_status,
        "timestamp": None  # Vous pouvez ajouter datetime.utcnow().isoformat() si besoin
    }














# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from .db.database import get_database_state, initialize_database
# from .api.v1 import api_router

# app = FastAPI(
#     title="SATIS-Attribution API",
#     description="API pour l'attribution automatique de widgets Flutter aux étudiants",
#     version="1.0.0"
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(api_router, prefix="/api/v1")


# @app.on_event("startup")
# def on_startup():
#     initialize_database()


# @app.get("/health/database")
# def database_health():
#     return get_database_state()
