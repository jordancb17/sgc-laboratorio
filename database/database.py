"""
Conexión a base de datos.
- En la nube (Streamlit Cloud): usa PostgreSQL via DATABASE_URL en secrets.
- En local: usa SQLite.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

# ── Detectar entorno ──────────────────────────────────────────────────────────
def _get_database_url() -> tuple[str, bool]:
    """Retorna (url, es_postgres)."""
    # 1. Variable de entorno (Streamlit Cloud la inyecta desde secrets)
    url = os.environ.get("DATABASE_URL", "")
    if url:
        # Streamlit Cloud a veces usa postgres://, SQLAlchemy necesita postgresql://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url, True

    # 2. secrets.toml local
    try:
        import streamlit as st
        url = st.secrets.get("database", {}).get("url", "")
        if url:
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url, True
    except Exception:
        pass

    # 3. SQLite local (fallback)
    db_path = Path(__file__).parent.parent / "data" / "lab_qms.db"
    db_path.parent.mkdir(exist_ok=True)
    return f"sqlite:///{db_path}", False


DATABASE_URL, IS_POSTGRES = _get_database_url()

if IS_POSTGRES:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)
    if not IS_POSTGRES:
        _migrate_sqlite()


def _migrate_sqlite():
    """Agrega columnas nuevas en SQLite sin borrar datos."""
    migraciones = [
        ("controles_diarios", "turno",          "ALTER TABLE controles_diarios ADD COLUMN turno VARCHAR(20)"),
        ("controles_diarios", "es_retroactivo", "ALTER TABLE controles_diarios ADD COLUMN es_retroactivo BOOLEAN DEFAULT 0"),
    ]
    with engine.connect() as conn:
        for tabla, columna, sql in migraciones:
            try:
                cols = [row[1] for row in conn.execute(text(f"PRAGMA table_info({tabla})")).fetchall()]
                if columna not in cols:
                    conn.execute(text(sql))
                    conn.commit()
            except Exception:
                pass


def get_session() -> Session:
    return SessionLocal()
