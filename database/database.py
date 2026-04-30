"""
Conexión a base de datos con caché de motor para máxima performance en Streamlit Cloud.
- En la nube: PostgreSQL via DATABASE_URL en secrets.
- En local: SQLite.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session


def _get_database_url() -> tuple[str, bool]:
    url = os.environ.get("DATABASE_URL", "")
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url, True
    try:
        import streamlit as st
        url = st.secrets.get("database", {}).get("url", "")
        if url:
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url, True
    except Exception:
        pass
    db_path = Path(__file__).parent.parent / "data" / "lab_qms.db"
    db_path.parent.mkdir(exist_ok=True)
    return f"sqlite:///{db_path}", False


def _build_engine():
    url, is_pg = _get_database_url()
    if is_pg:
        return create_engine(
            url,
            pool_pre_ping=True,
            pool_size=3,
            max_overflow=5,
            pool_timeout=20,
            pool_recycle=1800,
        ), True
    return create_engine(url, connect_args={"check_same_thread": False}), False


# ── Motor cacheado — se crea UNA sola vez por proceso ────────────────────────
try:
    import streamlit as st

    @st.cache_resource
    def _get_cached_engine():
        eng, is_pg = _build_engine()
        return eng, is_pg

    engine, IS_POSTGRES = _get_cached_engine()

except Exception:
    engine, IS_POSTGRES = _build_engine()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    from .models import Base
    Base.metadata.create_all(bind=engine)
    if not IS_POSTGRES:
        _migrate_sqlite()


def _migrate_sqlite():
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
