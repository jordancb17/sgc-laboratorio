"""
Caché compartido de datos de referencia para todas las páginas.
Devuelve listas de dicts planos (serializables por Streamlit cache).
TTL de 5 minutos — adecuado para datos de configuración que cambian poco.

Uso:
    from modules.cache import (
        cached_personal, cached_areas,
        cached_equipos, cached_materiales,
        invalidate_all,
    )

Llama a invalidate_all() después de cualquier operación CRUD que modifique
áreas, equipos, personal o analitos para que los demás páginas vean los
datos frescos en el siguiente rerun.
"""
import streamlit as st
from database.database import get_session
from database import crud


# ── Fuentes cacheadas ─────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def cached_personal() -> list[dict]:
    """Personal activo — lista de dicts {id, nombre, apellido, cargo, codigo}."""
    db = get_session()
    try:
        return [
            {
                "id":       p.id,
                "nombre":   p.nombre,
                "apellido": p.apellido,
                "cargo":    p.cargo or "",
                "codigo":   p.codigo or "",
            }
            for p in crud.listar_personal(db)
        ]
    finally:
        db.close()


@st.cache_data(ttl=300, show_spinner=False)
def cached_areas() -> list[dict]:
    """Áreas activas — lista de dicts {id, nombre}."""
    db = get_session()
    try:
        return [{"id": a.id, "nombre": a.nombre} for a in crud.listar_areas(db)]
    finally:
        db.close()


@st.cache_data(ttl=300, show_spinner=False)
def _cached_all_equipos() -> list[dict]:
    """TODOS los equipos activos — fuente única cacheada (no filtrada)."""
    db = get_session()
    try:
        return [
            {"id": e.id, "nombre": e.nombre, "area_id": e.area_id}
            for e in crud.listar_equipos(db)
        ]
    finally:
        db.close()


@st.cache_data(ttl=300, show_spinner=False)
def _cached_all_materiales() -> list[dict]:
    """TODOS los materiales activos — fuente única cacheada (no filtrada)."""
    db = get_session()
    try:
        return [
            {
                "id":            m.id,
                "analito":       m.analito,
                "unidad":        m.unidad or "",
                "proveedor":     m.proveedor,
                "equipo_id":     m.equipo_id,
                "equipo_nombre": m.equipo.nombre,
                "area_id":       m.equipo.area_id,
                "area_nombre":   m.equipo.area.nombre,
            }
            for m in crud.listar_materiales(db)
        ]
    finally:
        db.close()


# ── Wrappers con filtrado Python-side ─────────────────────────────────────────
# Un solo hit a BD cacheado; el filtro Python es O(n) con n pequeño (<200).

def cached_equipos(area_id: int | None = None) -> list[dict]:
    """Equipos activos. Si area_id es None devuelve todos; si no, filtra en Python."""
    all_eq = _cached_all_equipos()
    if area_id is None:
        return all_eq
    return [e for e in all_eq if e["area_id"] == area_id]


def cached_materiales(equipo_id: int | None = None) -> list[dict]:
    """Materiales activos. Si equipo_id es None devuelve todos; si no, filtra en Python."""
    all_mat = _cached_all_materiales()
    if equipo_id is None:
        return all_mat
    return [m for m in all_mat if m["equipo_id"] == equipo_id]


# ── Invalidación ──────────────────────────────────────────────────────────────

def invalidate_all() -> None:
    """Limpia el caché de todos los datos de referencia.

    Debe llamarse después de cualquier operación CRUD que modifique
    áreas, equipos, personal o analitos.
    """
    cached_personal.clear()
    cached_areas.clear()
    _cached_all_equipos.clear()
    _cached_all_materiales.clear()
