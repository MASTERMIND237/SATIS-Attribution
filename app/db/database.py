import os
from typing import Any
from urllib.parse import quote_plus
from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine


# Essayer de charger le fichier .env s'il existe
try:
    from dotenv import load_dotenv
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv n'est pas installé, on utilise les variables d'environnement directement


# Configuration de la base de données
DATABASE_CONNECT_TIMEOUT = int(os.getenv("DATABASE_CONNECT_TIMEOUT", "5"))


def get_database_url() -> str:
    """
    Récupère l'URL de connexion à la base de données.
    Priorité à DATABASE_URL, sinon construction depuis les variables individuelles.
    """
    # Essayer d'abord l'URL complète (pour la compatibilité)
    database_url = os.getenv("DATABASE_URL", "").strip().strip('"').strip("'")
    
    if database_url:
        # Nettoyer l'URL des anciens formats
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql://")
        database_url = database_url.replace("postgresql+psycopg://", "postgresql://")
        
        # Vérifier le format
        if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
            return database_url
    
    # Construction depuis les variables individuelles (recommandé)
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "postgres")
    
    if not all([db_password, db_host]):
        raise RuntimeError(
            "Configuration de base de données incomplète. "
            "Définissez soit DATABASE_URL, soit DB_USER, DB_PASSWORD, DB_HOST."
        )
    
    # Échapper les caractères spéciaux dans le mot de passe
    escaped_password = quote_plus(db_password)
    
    return f"postgresql://{db_user}:{escaped_password}@{db_host}:{db_port}/{db_name}"


def _engine_kwargs() -> dict[str, Any]:
    """Configure les arguments du moteur SQLAlchemy"""
    kwargs: dict[str, Any] = {
        "echo": False,
        "pool_pre_ping": True,
        "pool_recycle": 3600,  # Recycler les connexions après 1 heure
    }
    
    # Ajouter le timeout de connexion
    kwargs["connect_args"] = {
        "connect_timeout": DATABASE_CONNECT_TIMEOUT,
        "options": "-c statement_timeout=30000"  # 30 secondes timeout par requête
    }
    
    return kwargs


def build_engine(database_url: str):
    """Construit le moteur SQLAlchemy"""
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL est requis et doit pointer vers votre base de données Supabase Postgres."
        )
    
    return create_engine(database_url, **_engine_kwargs())


# Initialisation
DATABASE_URL = get_database_url()

# Créer le moteur principal
try:
    primary_engine = build_engine(DATABASE_URL)
except Exception as e:
    raise RuntimeError(f"Impossible de créer le moteur de base de données: {e}")

engine = primary_engine

# État de la base de données
database_state = {
    "configured_url": DATABASE_URL,
    "active_url": DATABASE_URL,
    "last_error": None,
}


def get_session():
    """Fournit une session de base de données"""
    with Session(engine) as session:
        yield session


def initialize_database():
    """Initialise la base de données en créant les tables"""
    global engine
    
    try:
        SQLModel.metadata.create_all(primary_engine)
        engine = primary_engine
        database_state["active_url"] = DATABASE_URL
        database_state["last_error"] = None
    except Exception as e:
        database_state["last_error"] = str(e)
        raise RuntimeError(f"Échec de l'initialisation de la base de données: {e}")
    
    return database_state


def get_database_state() -> dict[str, Any]:
    """Retourne l'état actuel de la base de données"""
    return dict(database_state)







# import os
# from typing import Any

# from sqlmodel import SQLModel, Session, create_engine


# DATABASE_URL = os.getenv("DATABASE_URL", "")
# DATABASE_CONNECT_TIMEOUT = int(os.getenv("DATABASE_CONNECT_TIMEOUT", "5"))


# def normalize_database_url(url: str) -> str:
#     if url.startswith("postgresql://") and "+psycopg2" not in url:
#         return url.replace("postgresql://", "postgresql+psycopg2://", 1)
#     return url


# def _engine_kwargs(url: str) -> dict[str, Any]:
#     normalized_url = normalize_database_url(url)
#     kwargs: dict[str, Any] = {"echo": False, "pool_pre_ping": True}

#     if normalized_url.startswith("postgresql"):
#         kwargs["connect_args"] = {"connect_timeout": DATABASE_CONNECT_TIMEOUT}

#     return kwargs


# def build_engine(url: str):
#     if not url:
#         raise RuntimeError("DATABASE_URL is required and must point to your Supabase Postgres database.")

#     normalized_url = normalize_database_url(url)
#     return create_engine(normalized_url, **_engine_kwargs(normalized_url))


# primary_engine = build_engine(DATABASE_URL)
# engine = primary_engine
# database_state = {
#     "configured_url": normalize_database_url(DATABASE_URL),
#     "active_url": normalize_database_url(DATABASE_URL),
#     "last_error": None,
# }


# def get_session():
#     with Session(engine) as session:
#         yield session


# def initialize_database():
#     global engine

#     SQLModel.metadata.create_all(primary_engine)
#     engine = primary_engine
#     database_state["active_url"] = normalize_database_url(DATABASE_URL)
#     database_state["last_error"] = None
#     return database_state


# def get_database_state() -> dict[str, Any]:
#     return dict(database_state)
