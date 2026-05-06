import os
import sys
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine


# Configuration
DATABASE_CONNECT_TIMEOUT = int(os.getenv("DATABASE_CONNECT_TIMEOUT", "10"))


def get_database_url() -> str:
    """
    Récupère l'URL de connexion à la base de données.
    
    Priorité :
    1. Variable DATABASE_URL
    2. Variables séparées (DB_USER, DB_PASSWORD, DB_HOST, etc.)
    """
    # Méthode 1 : URL complète
    database_url = os.getenv("DATABASE_URL", "").strip().strip('"').strip("'")
    
    if database_url:
        # Nettoyer les anciens formats SQLAlchemy
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql://")
        database_url = database_url.replace("postgresql+psycopg://", "postgresql://")
        
        # Vérifier que l'URL a un format valide
        if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
            return database_url
        
        print(f"⚠️  DATABASE_URL ignorée (format invalide): {database_url[:50]}...", file=sys.stderr)
    
    # Méthode 2 : Construction depuis variables individuelles
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "postgres")
    
    if not db_password or not db_host:
        raise RuntimeError(
            "❌ Configuration de base de données incomplète.\n"
            "   Définissez soit:\n"
            "   - DATABASE_URL=postgresql://user:password@host:port/dbname\n"
            "   - Ou DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME"
        )
    
    # Échapper les caractères spéciaux dans le mot de passe
    escaped_password = quote_plus(db_password)
    
    constructed_url = f"postgresql://{db_user}:{escaped_password}@{db_host}:{db_port}/{db_name}"
    return constructed_url


def _engine_kwargs() -> dict[str, Any]:
    """Configure les arguments du moteur SQLAlchemy"""
    return {
        "echo": False,  # Mettre True pour debug SQL
        "pool_pre_ping": True,  # Vérifier la connexion avant utilisation
        "pool_recycle": 3600,   # Recycler les connexions après 1h
        "pool_size": 5,         # Nombre de connexions dans le pool
        "max_overflow": 10,     # Connexions supplémentaires si besoin
        "connect_args": {
            "connect_timeout": DATABASE_CONNECT_TIMEOUT,
            "options": "-c statement_timeout=30000"  # 30s timeout par requête
        }
    }


def build_engine(database_url: str):
    """Construit et teste le moteur SQLAlchemy"""
    if not database_url:
        raise RuntimeError("DATABASE_URL est requis")
    
    # Masquer le password dans les logs
    safe_url = database_url.split('@')[1] if '@' in database_url else 'URL configurée'
    print(f"🔗 Tentative de connexion à: {safe_url}", file=sys.stderr)
    
    try:
        engine = create_engine(database_url, **_engine_kwargs())
        
        # Test de connexion immédiat - CORRIGÉ avec text()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
            
        print("✅ Connexion à la base de données réussie", file=sys.stderr)
        return engine
        
    except Exception as e:
        print(f"❌ Échec de connexion à la base de données: {e}", file=sys.stderr)
        raise


# =============================================
# INITIALISATION
# =============================================

print("=" * 60, file=sys.stderr)
print("📦 Initialisation du module database...", file=sys.stderr)

# Étape 1 : Récupérer l'URL
try:
    DATABASE_URL = get_database_url()
    # Log sécurisé (masquer le mot de passe)
    if '@' in DATABASE_URL:
        safe_display = DATABASE_URL.split('@')[1]
        print(f"✓ URL configurée: ...@{safe_display}", file=sys.stderr)
    else:
        print("✓ URL configurée", file=sys.stderr)
except RuntimeError as e:
    print(str(e), file=sys.stderr)
    DATABASE_URL = None

# Étape 2 : Créer l'engine
if DATABASE_URL:
    try:
        primary_engine = build_engine(DATABASE_URL)
    except Exception as e:
        print(f"⚠️  Impossible de créer l'engine maintenant: {e}", file=sys.stderr)
        print("   L'API démarrera mais nécessitera une reconfiguration.", file=sys.stderr)
        primary_engine = None
else:
    print("⚠️  Pas d'URL de base de données configurée.", file=sys.stderr)
    primary_engine = None

engine = primary_engine

# État de la base de données
database_state = {
    "configured_url": DATABASE_URL.split('@')[1] if DATABASE_URL and '@' in DATABASE_URL else (DATABASE_URL or "Non configurée"),
    "active_url": None,
    "last_error": None,
    "initialized": False,
}

print("=" * 60, file=sys.stderr)


# =============================================
# FONCTIONS PUBLIQUES
# =============================================

def get_database_state() -> dict[str, Any]:
    """Retourne l'état actuel de la base de données"""
    state = dict(database_state)
    
    # Ajouter des informations de diagnostic
    state["engine_status"] = "active" if engine is not None else "not_initialized"
    
    # Vérifier la connexion si l'engine existe
    if engine is not None:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))  # CORRIGÉ avec text()
                conn.commit()
            state["connection_check"] = "passed"
        except Exception as e:
            state["connection_check"] = "failed"
            state["connection_error"] = str(e)
    
    return state


def get_session():
    """Fournit une session de base de données (générateur pour FastAPI)"""
    if engine is None:
        raise RuntimeError(
            "Base de données non initialisée. Vérifiez la configuration DATABASE_URL."
        )
    
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()


def initialize_database():
    """Initialise la base de données en créant toutes les tables"""
    global engine, database_state
    
    if engine is None:
        error_msg = "Impossible d'initialiser : engine non disponible. Vérifiez DATABASE_URL."
        database_state["last_error"] = error_msg
        raise RuntimeError(error_msg)
    
    try:
        print("🏗️  Création des tables dans la base de données...", file=sys.stderr)
        SQLModel.metadata.create_all(engine)
        
        database_state["active_url"] = DATABASE_URL.split('@')[1] if DATABASE_URL and '@' in DATABASE_URL else DATABASE_URL
        database_state["last_error"] = None
        database_state["initialized"] = True
        
        print("✅ Tables créées avec succès", file=sys.stderr)
        
    except Exception as e:
        database_state["last_error"] = str(e)
        database_state["initialized"] = False
        
        raise RuntimeError(f"Échec de l'initialisation de la base de données: {e}")
    
    return dict(database_state)