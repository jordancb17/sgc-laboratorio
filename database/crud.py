"""
Operaciones CRUD para todos los modelos del sistema.
Usa SQLAlchemy 2.x nativo: select() + db.scalars() / db.get()
"""

from datetime import date, time, datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import select, and_, exists

from .models import (
    Area, Equipo, Personal, GrupoAnalitos, MaterialControl, Lote, NivelLote,
    ControlDiario, ControlExterno, SesionEP15, MedicionEP15, AccionCorrectiva,
    IndiceCalidad, Calibracion, Mantenimiento,
)
from modules.westgard import evaluar_westgard


# ═══════════════════════════════════════════════════════════════════════════════
# ÁREAS
# ═══════════════════════════════════════════════════════════════════════════════

def listar_areas(db: Session, solo_activos: bool = True) -> list[Area]:
    stmt = select(Area)
    if solo_activos:
        stmt = stmt.where(Area.activo == True)
    return list(db.scalars(stmt.order_by(Area.nombre)))


def crear_area(db: Session, nombre: str, descripcion: str = "") -> Area:
    area = Area(nombre=nombre.strip(), descripcion=descripcion.strip())
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


def actualizar_area(db: Session, area_id: int, nombre: str, descripcion: str = "") -> Optional[Area]:
    area = db.get(Area, area_id)
    if area:
        area.nombre = nombre.strip()
        area.descripcion = descripcion.strip()
        db.commit()
        db.refresh(area)
    return area


def toggle_activo_area(db: Session, area_id: int) -> bool:
    area = db.get(Area, area_id)
    if area:
        area.activo = not area.activo
        db.commit()
        return area.activo
    return False


def desactivar_area(db: Session, area_id: int) -> bool:
    area = db.get(Area, area_id)
    if area:
        area.activo = False
        db.commit()
        return True
    return False


def eliminar_area(db: Session, area_id: int) -> tuple[bool, str]:
    """Elimina un área sólo si no tiene equipos asociados."""
    area = db.get(Area, area_id)
    if not area:
        return False, "Área no encontrada."
    equipos = db.scalars(select(Equipo).where(Equipo.area_id == area_id)).all()
    if equipos:
        return False, f"No se puede eliminar: el área tiene {len(equipos)} equipo(s) asociado(s). Elimine o reasigne los equipos primero."
    db.delete(area)
    db.commit()
    return True, "Área eliminada correctamente."


# ═══════════════════════════════════════════════════════════════════════════════
# EQUIPOS
# ═══════════════════════════════════════════════════════════════════════════════

def listar_equipos(db: Session, area_id: Optional[int] = None, solo_activos: bool = True) -> list[Equipo]:
    stmt = select(Equipo).options(joinedload(Equipo.area))
    if area_id:
        stmt = stmt.where(Equipo.area_id == area_id)
    if solo_activos:
        stmt = stmt.where(Equipo.activo == True)
    return list(db.scalars(stmt.order_by(Equipo.nombre)))


def crear_equipo(db: Session, area_id: int, nombre: str, marca: str = "", modelo: str = "", numero_serie: str = "") -> Equipo:
    equipo = Equipo(
        area_id=area_id,
        nombre=nombre.strip(),
        marca=marca.strip(),
        modelo=modelo.strip(),
        numero_serie=numero_serie.strip(),
    )
    db.add(equipo)
    db.commit()
    db.refresh(equipo)
    return equipo


def actualizar_equipo(db: Session, equipo_id: int, area_id: int, nombre: str, marca: str = "", modelo: str = "", numero_serie: str = "") -> Optional[Equipo]:
    equipo = db.get(Equipo, equipo_id)
    if equipo:
        equipo.area_id = area_id
        equipo.nombre = nombre.strip()
        equipo.marca = marca.strip()
        equipo.modelo = modelo.strip()
        equipo.numero_serie = numero_serie.strip()
        db.commit()
        db.refresh(equipo)
    return equipo


def toggle_activo_equipo(db: Session, equipo_id: int) -> bool:
    equipo = db.get(Equipo, equipo_id)
    if equipo:
        equipo.activo = not equipo.activo
        db.commit()
        return equipo.activo
    return False


def desactivar_equipo(db: Session, equipo_id: int) -> bool:
    equipo = db.get(Equipo, equipo_id)
    if equipo:
        equipo.activo = False
        db.commit()
        return True
    return False


def eliminar_equipo(db: Session, equipo_id: int) -> tuple[bool, str]:
    """Elimina un equipo sólo si no tiene analitos asociados."""
    equipo = db.get(Equipo, equipo_id)
    if not equipo:
        return False, "Equipo no encontrado."
    mats = db.scalars(select(MaterialControl).where(MaterialControl.equipo_id == equipo_id)).all()
    if mats:
        return False, f"No se puede eliminar: el equipo tiene {len(mats)} analito(s) asociado(s). Elimínelos primero."
    db.delete(equipo)
    db.commit()
    return True, "Equipo eliminado correctamente."


# ═══════════════════════════════════════════════════════════════════════════════
# PERSONAL
# ═══════════════════════════════════════════════════════════════════════════════

def listar_personal(db: Session, solo_activos: bool = True) -> list[Personal]:
    stmt = select(Personal)
    if solo_activos:
        stmt = stmt.where(Personal.activo == True)
    return list(db.scalars(stmt.order_by(Personal.apellido, Personal.nombre)))


def crear_personal(db: Session, nombre: str, apellido: str, codigo: str = "", cargo: str = "") -> Personal:
    p = Personal(
        nombre=nombre.strip(),
        apellido=apellido.strip(),
        codigo=codigo.strip() or None,
        cargo=cargo.strip(),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def actualizar_personal(db: Session, personal_id: int, nombre: str, apellido: str, codigo: str = "", cargo: str = "") -> Optional[Personal]:
    p = db.get(Personal, personal_id)
    if p:
        p.nombre = nombre.strip()
        p.apellido = apellido.strip()
        p.codigo = codigo.strip() or None
        p.cargo = cargo.strip()
        db.commit()
        db.refresh(p)
    return p


def toggle_activo_personal(db: Session, personal_id: int) -> bool:
    p = db.get(Personal, personal_id)
    if p:
        p.activo = not p.activo
        db.commit()
        return p.activo
    return False


def desactivar_personal(db: Session, personal_id: int) -> bool:
    p = db.get(Personal, personal_id)
    if p:
        p.activo = False
        db.commit()
        return True
    return False


def eliminar_personal(db: Session, personal_id: int) -> tuple[bool, str]:
    """Elimina personal sólo si no tiene controles registrados."""
    p = db.get(Personal, personal_id)
    if not p:
        return False, "Personal no encontrado."
    tiene = db.scalars(select(ControlDiario).where(ControlDiario.personal_id == personal_id)).first()
    if tiene:
        return False, "No se puede eliminar: tiene controles registrados. Use 'Desactivar' en su lugar."
    db.delete(p)
    db.commit()
    return True, "Personal eliminado correctamente."


# ═══════════════════════════════════════════════════════════════════════════════
# GRUPOS DE ANALITOS (PANELES DE PRUEBAS)
# ═══════════════════════════════════════════════════════════════════════════════

def listar_grupos(db: Session, equipo_id: Optional[int] = None, solo_activos: bool = True) -> list[GrupoAnalitos]:
    stmt = select(GrupoAnalitos).options(
        joinedload(GrupoAnalitos.equipo).joinedload(Equipo.area),
        selectinload(GrupoAnalitos.materiales),   # colección → selectinload evita duplicados
    )
    if equipo_id:
        stmt = stmt.where(GrupoAnalitos.equipo_id == equipo_id)
    if solo_activos:
        stmt = stmt.where(GrupoAnalitos.activo == True)
    return list(db.scalars(stmt.order_by(GrupoAnalitos.nombre)))


def crear_grupo(db: Session, equipo_id: int, nombre: str, descripcion: str = "") -> GrupoAnalitos:
    g = GrupoAnalitos(equipo_id=equipo_id, nombre=nombre.strip(), descripcion=descripcion.strip())
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


def actualizar_grupo(db: Session, grupo_id: int, equipo_id: int, nombre: str, descripcion: str = "") -> Optional[GrupoAnalitos]:
    g = db.get(GrupoAnalitos, grupo_id)
    if g:
        g.equipo_id = equipo_id
        g.nombre = nombre.strip()
        g.descripcion = descripcion.strip()
        db.commit()
        db.refresh(g)
    return g


def toggle_activo_grupo(db: Session, grupo_id: int) -> bool:
    g = db.get(GrupoAnalitos, grupo_id)
    if g:
        g.activo = not g.activo
        db.commit()
        return g.activo
    return False


def eliminar_grupo(db: Session, grupo_id: int, eliminar_analitos: bool = False) -> tuple[bool, str]:
    """
    Elimina el grupo.
    Si eliminar_analitos=True también borra los MaterialControl del grupo (si no tienen controles).
    Si eliminar_analitos=False los desvincula (grupo_id=None) pero los conserva.
    """
    g = db.get(GrupoAnalitos, grupo_id)
    if not g:
        return False, "Grupo no encontrado."
    mats = db.scalars(select(MaterialControl).where(MaterialControl.grupo_id == grupo_id)).all()
    n = len(mats)
    if eliminar_analitos:
        eliminados = 0
        no_eliminados = 0
        for m in mats:
            # Solo borra si no tiene controles ni lotes
            tiene_ctrl = db.scalars(select(ControlDiario).where(ControlDiario.material_id == m.id)).first()
            tiene_lote = db.scalars(select(Lote).where(Lote.material_id == m.id)).first()
            if tiene_ctrl or tiene_lote:
                m.grupo_id = None  # desvincula en lugar de borrar
                no_eliminados += 1
            else:
                db.delete(m)
                eliminados += 1
        db.delete(g)
        db.commit()
        msg = f"Grupo eliminado. {eliminados} analito(s) borrado(s)"
        if no_eliminados:
            msg += f", {no_eliminados} conservado(s) por tener historial (solo desvinculados)."
        return True, msg
    else:
        for m in mats:
            m.grupo_id = None
        db.delete(g)
        db.commit()
        return True, f"Grupo eliminado. {n} analito(s) desvinculado(s) del grupo (se conservan en Analitos)."


def crear_panel_desde_plantilla(
    db: Session,
    equipo_id: int,
    nombre_grupo: str,
    descripcion: str,
    proveedor: str,
    parametros: list[tuple[str, str]],
) -> tuple[GrupoAnalitos, list[MaterialControl]]:
    """Crea un GrupoAnalitos y todos sus MaterialControl de una lista (analito, unidad)."""
    grupo = crear_grupo(db, equipo_id, nombre_grupo, descripcion)
    materiales = []
    for analito, unidad in parametros:
        m = MaterialControl(
            equipo_id=equipo_id,
            grupo_id=grupo.id,
            analito=analito,
            proveedor=proveedor.strip(),
            unidad=unidad,
            nombre_material="",
        )
        db.add(m)
        materiales.append(m)
    db.commit()
    for m in materiales:
        db.refresh(m)
    return grupo, materiales


# ═══════════════════════════════════════════════════════════════════════════════
# MATERIALES DE CONTROL (ANALITOS)
# ═══════════════════════════════════════════════════════════════════════════════

def listar_materiales(db: Session, equipo_id: Optional[int] = None, solo_activos: bool = True) -> list[MaterialControl]:
    stmt = select(MaterialControl).options(
        joinedload(MaterialControl.equipo).joinedload(Equipo.area),
        joinedload(MaterialControl.grupo),
    )
    if equipo_id:
        stmt = stmt.where(MaterialControl.equipo_id == equipo_id)
    if solo_activos:
        stmt = stmt.where(MaterialControl.activo == True)
    return list(db.scalars(stmt.order_by(MaterialControl.analito)).unique())


def crear_material(
    db: Session,
    equipo_id: int,
    analito: str,
    proveedor: str,
    unidad: str = "",
    nombre_material: str = "",
    grupo_id: Optional[int] = None,
) -> MaterialControl:
    m = MaterialControl(
        equipo_id=equipo_id,
        grupo_id=grupo_id,
        analito=analito.strip(),
        proveedor=proveedor.strip(),
        unidad=unidad.strip(),
        nombre_material=nombre_material.strip(),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def desactivar_material(db: Session, material_id: int) -> bool:
    m = db.get(MaterialControl, material_id)
    if m:
        m.activo = False
        db.commit()
        return True
    return False


def actualizar_material(
    db: Session,
    material_id: int,
    equipo_id: int,
    analito: str,
    proveedor: str,
    unidad: str = "",
    nombre_material: str = "",
    grupo_id: Optional[int] = None,
) -> Optional[MaterialControl]:
    m = db.get(MaterialControl, material_id)
    if m:
        m.equipo_id = equipo_id
        m.grupo_id = grupo_id
        m.analito = analito.strip()
        m.proveedor = proveedor.strip()
        m.unidad = unidad.strip()
        m.nombre_material = nombre_material.strip()
        db.commit()
        db.refresh(m)
    return m


def toggle_activo_material(db: Session, material_id: int) -> bool:
    m = db.get(MaterialControl, material_id)
    if m:
        m.activo = not m.activo
        db.commit()
        return m.activo
    return False


def eliminar_material(db: Session, material_id: int) -> tuple[bool, str]:
    """Elimina un analito sólo si no tiene lotes ni controles asociados."""
    m = db.get(MaterialControl, material_id)
    if not m:
        return False, "Analito no encontrado."
    lotes = db.scalars(select(Lote).where(Lote.material_id == material_id)).all()
    if lotes:
        return False, f"No se puede eliminar: el analito tiene {len(lotes)} lote(s) asociado(s). Elimínelos primero."
    controles = db.scalars(select(ControlDiario).where(ControlDiario.material_id == material_id)).first()
    if controles:
        return False, "No se puede eliminar: el analito tiene controles registrados. Use 'Desactivar' en su lugar."
    db.delete(m)
    db.commit()
    return True, "Analito eliminado correctamente."


# ═══════════════════════════════════════════════════════════════════════════════
# LOTES Y NIVELES
# ═══════════════════════════════════════════════════════════════════════════════

def listar_lotes(db: Session, material_id: int, solo_activos: bool = False) -> list[Lote]:
    """Devuelve todos los lotes de un material (por defecto incluye activos e inactivos)."""
    stmt = (
        select(Lote)
        .options(selectinload(Lote.niveles))
        .where(Lote.material_id == material_id)
    )
    if solo_activos:
        stmt = stmt.where(Lote.activo == True)
    return list(db.scalars(stmt.order_by(Lote.fecha_vencimiento.desc())))


def activar_lote(db: Session, lote_id: int) -> bool:
    """Marca este lote como activo y desactiva todos los demás del mismo material (one-at-a-time)."""
    lote = db.get(Lote, lote_id)
    if not lote:
        return False
    # Desactivar todos los demás del mismo material
    otros = db.scalars(
        select(Lote).where(Lote.material_id == lote.material_id, Lote.id != lote_id)
    ).all()
    for o in otros:
        o.activo = False
    lote.activo = True
    db.commit()
    return True


def toggle_activo_lote(db: Session, lote_id: int) -> bool:
    lote = db.get(Lote, lote_id)
    if lote:
        lote.activo = not lote.activo
        db.commit()
        return lote.activo
    return False


def eliminar_lote(db: Session, lote_id: int) -> tuple[bool, str]:
    """Elimina un lote sólo si no tiene controles registrados."""
    lote = db.get(Lote, lote_id)
    if not lote:
        return False, "Lote no encontrado."
    tiene = db.scalars(select(ControlDiario).where(ControlDiario.lote_id == lote_id)).first()
    if tiene:
        return False, "No se puede eliminar: el lote tiene controles registrados. Desactívelo en su lugar."
    db.delete(lote)
    db.commit()
    return True, "Lote eliminado correctamente."


def crear_lote(
    db: Session,
    material_id: int,
    numero_lote: str,
    fecha_vencimiento: date,
    niveles: list[dict],   # [{"nivel": 1, "media": X, "de": Y, "min": A, "max": B}, ...]
) -> Lote:
    lote = Lote(
        material_id=material_id,
        numero_lote=numero_lote.strip(),
        fecha_vencimiento=fecha_vencimiento,
    )
    db.add(lote)
    db.flush()
    for nv in niveles:
        nl = NivelLote(
            lote_id=lote.id,
            nivel=nv["nivel"],
            media=nv["media"],
            de=nv["de"],
            valor_minimo=nv["min"],
            valor_maximo=nv["max"],
        )
        db.add(nl)
    db.commit()
    db.refresh(lote)
    return lote


def crear_lotes_grupo(
    db: Session,
    grupo_id: int,
    numero_lote: str,
    fecha_vencimiento: date,
    targets: dict,  # {material_id: [{"nivel": N, "media": X, "de": S, "min": A, "max": B}, ...]}
) -> tuple[int, list[str]]:
    """
    Crea lotes para todos los analitos de un grupo con el mismo número de lote.
    targets: dict keyed por material_id con lista de dicts por nivel.
    Returns (cantidad_creados, errores[]).
    """
    creados = 0
    errores = []
    for mat_id, niveles in targets.items():
        if not niveles:
            continue
        try:
            # Si ya existe ese número de lote para ese material, actualizamos niveles
            stmt = select(Lote).where(Lote.material_id == mat_id, Lote.numero_lote == numero_lote.strip())
            lote_existente = db.scalars(stmt).first()
            if lote_existente:
                lote = lote_existente
                lote.fecha_vencimiento = fecha_vencimiento
            else:
                lote = Lote(
                    material_id=mat_id,
                    numero_lote=numero_lote.strip(),
                    fecha_vencimiento=fecha_vencimiento,
                )
                db.add(lote)
                db.flush()

            for nv in niveles:
                stmt_nv = select(NivelLote).where(
                    NivelLote.lote_id == lote.id, NivelLote.nivel == nv["nivel"]
                )
                nl = db.scalars(stmt_nv).first()
                if nl:
                    nl.media = nv["media"]
                    nl.de = nv["de"]
                    nl.valor_minimo = nv["min"]
                    nl.valor_maximo = nv["max"]
                else:
                    nl = NivelLote(
                        lote_id=lote.id,
                        nivel=nv["nivel"],
                        media=nv["media"],
                        de=nv["de"],
                        valor_minimo=nv["min"],
                        valor_maximo=nv["max"],
                    )
                    db.add(nl)
            creados += 1
        except Exception as e:
            errores.append(f"Material ID {mat_id}: {e}")
    db.commit()
    return creados, errores


def material_ids_con_lote_activo(db: Session) -> set:
    """Una sola query: devuelve el set de material_ids que tienen lote activo vigente."""
    hoy = date.today()
    stmt = select(Lote.material_id).where(
        Lote.activo == True,
        Lote.fecha_vencimiento >= hoy,
    ).distinct()
    return set(db.scalars(stmt))


def get_lotes_activos_bulk(db: Session, material_ids: list) -> dict:
    """Una sola query: devuelve {material_id: Lote} para todos los ids dados (con niveles precargados)."""
    if not material_ids:
        return {}
    hoy = date.today()
    stmt = (
        select(Lote)
        .options(selectinload(Lote.niveles))
        .where(
            Lote.material_id.in_(material_ids),
            Lote.activo == True,
            Lote.fecha_vencimiento >= hoy,
        )
        .order_by(Lote.fecha_vencimiento.desc())
    )
    result: dict = {}
    for lote in db.scalars(stmt).all():
        if lote.material_id not in result:          # keep most-recent
            result[lote.material_id] = lote
    return result


def get_lote_activo(db: Session, material_id: int) -> Optional[Lote]:
    """Devuelve el lote activo no vencido más reciente para un material."""
    hoy = date.today()
    stmt = (
        select(Lote)
        .where(
            Lote.material_id == material_id,
            Lote.activo == True,
            Lote.fecha_vencimiento >= hoy,
        )
        .order_by(Lote.fecha_vencimiento.desc())
    )
    return db.scalars(stmt).first()


def get_nivel_lote(db: Session, lote_id: int, nivel: int) -> Optional[NivelLote]:
    stmt = select(NivelLote).where(
        NivelLote.lote_id == lote_id,
        NivelLote.nivel == nivel,
    )
    return db.scalars(stmt).first()


def lotes_por_vencer(db: Session, dias: int = 30) -> list[Lote]:
    hoy = date.today()
    limite = hoy + timedelta(days=dias)
    stmt = (
        select(Lote)
        .where(
            Lote.activo == True,
            Lote.fecha_vencimiento <= limite,
            Lote.fecha_vencimiento >= hoy,
        )
        .order_by(Lote.fecha_vencimiento)
    )
    return list(db.scalars(stmt))


# ═══════════════════════════════════════════════════════════════════════════════
# CONTROLES DIARIOS
# ═══════════════════════════════════════════════════════════════════════════════

def historial_zscores(
    db: Session,
    nivel_lote_id: int,
    limite: int = 10,
    excluir_id: Optional[int] = None,
) -> list[float]:
    """Devuelve los últimos z-scores del mismo nivel (más reciente primero)."""
    stmt = select(ControlDiario).where(ControlDiario.nivel_lote_id == nivel_lote_id)
    if excluir_id:
        stmt = stmt.where(ControlDiario.id != excluir_id)
    stmt = stmt.order_by(ControlDiario.fecha.desc(), ControlDiario.hora.desc()).limit(limite)
    controles = db.scalars(stmt).all()
    return [c.zscore for c in controles if c.zscore is not None]


def zscores_mismo_run(
    db: Session,
    material_id: int,
    fecha: date,
    hora: time,
    nivel_excluido: int,
    lote_id: int,
) -> list[float]:
    """Z-scores de otros niveles del mismo equipo/fecha para R-4s inter-nivel."""
    stmt = (
        select(ControlDiario)
        .join(NivelLote)
        .where(
            ControlDiario.material_id == material_id,
            ControlDiario.fecha == fecha,
            ControlDiario.lote_id == lote_id,
            NivelLote.nivel != nivel_excluido,
        )
    )
    controles = db.scalars(stmt).all()
    return [c.zscore for c in controles if c.zscore is not None]


def existe_control_diario(
    db: Session,
    material_id: int,
    nivel_lote_id: int,
    fecha: date,
    hora: time,
) -> bool:
    stmt = select(ControlDiario).where(
        ControlDiario.material_id == material_id,
        ControlDiario.nivel_lote_id == nivel_lote_id,
        ControlDiario.fecha == fecha,
        ControlDiario.hora == hora,
    )
    return db.scalars(stmt).first() is not None


def registrar_control_diario(
    db: Session,
    material_id: int,
    lote_id: int,
    nivel_lote_id: int,
    personal_id: int,
    fecha: date,
    hora: time,
    valor: float,
    comentario: str = "",
    es_retroactivo: bool = False,
    turno: Optional[str] = None,
) -> tuple[ControlDiario, str]:
    """
    Registra un control diario y aplica las reglas de Westgard.

    Returns
    -------
    (ControlDiario, mensaje_error)
        Si hay conflicto de fecha/hora, devuelve (None, mensaje).
    """
    # Verificar duplicado exacto
    if existe_control_diario(db, material_id, nivel_lote_id, fecha, hora):
        return None, "Ya existe un control registrado para este analito/nivel en esa fecha y hora exactas."

    nivel_lote = db.get(NivelLote, nivel_lote_id)
    if not nivel_lote:
        return None, "Nivel de lote no encontrado."

    # Historial para Westgard
    hist_zs = historial_zscores(db, nivel_lote_id)
    otros_zs = zscores_mismo_run(db, material_id, fecha, hora, nivel_lote.nivel, lote_id)

    resultado_wg = evaluar_westgard(
        valor_nuevo=valor,
        media=nivel_lote.media,
        de=nivel_lote.de,
        historial_zscores=hist_zs,
        historial_zscores_otros_niveles=otros_zs if otros_zs else None,
    )

    control = ControlDiario(
        material_id=material_id,
        lote_id=lote_id,
        nivel_lote_id=nivel_lote_id,
        personal_id=personal_id,
        fecha=fecha,
        turno=turno,
        hora=hora,
        valor=valor,
        zscore=resultado_wg.zscore,
        resultado=resultado_wg.resultado,
        regla_violada=resultado_wg.regla_violada,
        es_retroactivo=es_retroactivo,
        comentario=comentario.strip(),
    )
    db.add(control)
    db.commit()
    db.refresh(control)
    return control, ""


def listar_controles_diarios(
    db: Session,
    material_id: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    nivel: Optional[int] = None,
    personal_id: Optional[int] = None,
    equipo_id: Optional[int] = None,
    area_id: Optional[int] = None,
) -> list[ControlDiario]:
    stmt = select(ControlDiario).options(
        joinedload(ControlDiario.lote),                          # evita N+1 en informe corrida
        joinedload(ControlDiario.material)
            .joinedload(MaterialControl.equipo)
            .joinedload(Equipo.area),
        joinedload(ControlDiario.nivel_lote),
        joinedload(ControlDiario.personal),
        joinedload(ControlDiario.accion_correctiva),
    )
    if material_id:
        stmt = stmt.where(ControlDiario.material_id == material_id)
    if fecha_desde:
        stmt = stmt.where(ControlDiario.fecha >= fecha_desde)
    if fecha_hasta:
        stmt = stmt.where(ControlDiario.fecha <= fecha_hasta)
    if nivel is not None:
        stmt = stmt.join(NivelLote, ControlDiario.nivel_lote_id == NivelLote.id).where(NivelLote.nivel == nivel)
    if personal_id:
        stmt = stmt.where(ControlDiario.personal_id == personal_id)
    # Filtros por equipo / área — se resuelven con subconsultas para no chocar con joinedload
    if equipo_id:
        stmt = stmt.where(
            ControlDiario.material_id.in_(
                select(MaterialControl.id).where(MaterialControl.equipo_id == equipo_id)
            )
        )
    if area_id:
        stmt = stmt.where(
            ControlDiario.material_id.in_(
                select(MaterialControl.id)
                .join(Equipo, MaterialControl.equipo_id == Equipo.id)
                .where(Equipo.area_id == area_id)
            )
        )
    return list(
        db.scalars(stmt.order_by(ControlDiario.fecha.asc(), ControlDiario.hora.asc())).unique()
    )


def eliminar_control_diario(db: Session, control_id: int) -> bool:
    c = db.get(ControlDiario, control_id)
    if c:
        db.delete(c)
        db.commit()
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# CONTROL EXTERNO
# ═══════════════════════════════════════════════════════════════════════════════

def _clasificar_externo(zscore: float) -> str:
    az = abs(zscore)
    if az <= 2.0:
        return "ACEPTABLE"
    if az <= 3.0:
        return "ADVERTENCIA"
    return "INACEPTABLE"


def registrar_control_externo(
    db: Session,
    material_id: int,
    personal_id: int,
    proveedor_externo: str,
    periodo: str,
    nivel: int,
    valor_obtenido: float,
    valor_diana: Optional[float] = None,
    de_grupo: Optional[float] = None,
    n_participantes: Optional[int] = None,
    percentil: Optional[float] = None,
    comentario: str = "",
) -> tuple[ControlExterno, str]:
    # Verificar duplicado
    stmt = select(ControlExterno).where(
        ControlExterno.material_id == material_id,
        ControlExterno.proveedor_externo == proveedor_externo,
        ControlExterno.periodo == periodo,
        ControlExterno.nivel == nivel,
    )
    existe = db.scalars(stmt).first()
    if existe:
        return None, "Ya existe un control externo para ese analito, proveedor, período y nivel."

    zscore = None
    resultado = "SIN EVALUAR"
    if valor_diana is not None and de_grupo and de_grupo > 0:
        zscore = (valor_obtenido - valor_diana) / de_grupo
        resultado = _clasificar_externo(zscore)

    ce = ControlExterno(
        material_id=material_id,
        personal_id=personal_id,
        proveedor_externo=proveedor_externo.strip(),
        periodo=periodo.strip(),
        nivel=nivel,
        valor_obtenido=valor_obtenido,
        valor_diana=valor_diana,
        de_grupo=de_grupo,
        n_participantes=n_participantes,
        zscore=zscore,
        percentil=percentil,
        resultado=resultado,
        comentario=comentario.strip(),
    )
    db.add(ce)
    db.commit()
    db.refresh(ce)
    return ce, ""


def listar_controles_externos(
    db: Session,
    material_id: Optional[int] = None,
    proveedor: Optional[str] = None,
) -> list[ControlExterno]:
    stmt = select(ControlExterno)
    if material_id:
        stmt = stmt.where(ControlExterno.material_id == material_id)
    if proveedor:
        stmt = stmt.where(ControlExterno.proveedor_externo == proveedor)
    return list(db.scalars(stmt.order_by(ControlExterno.periodo.asc())))


# ═══════════════════════════════════════════════════════════════════════════════
# EP15-A3
# ═══════════════════════════════════════════════════════════════════════════════

def crear_sesion_ep15(
    db: Session,
    material_id: int,
    nombre_sesion: str,
    nivel: int,
    n_dias: int,
    n_replicados: int,
    cv_r_fabricante: Optional[float] = None,
    cv_ip_fabricante: Optional[float] = None,
    sesgo_permitido: Optional[float] = None,
    valor_referencia: Optional[float] = None,
) -> SesionEP15:
    sesion = SesionEP15(
        material_id=material_id,
        nombre_sesion=nombre_sesion.strip(),
        nivel=nivel,
        n_dias=n_dias,
        n_replicados=n_replicados,
        cv_r_fabricante=cv_r_fabricante,
        cv_ip_fabricante=cv_ip_fabricante,
        sesgo_permitido=sesgo_permitido,
        valor_referencia=valor_referencia,
    )
    db.add(sesion)
    db.commit()
    db.refresh(sesion)
    return sesion


def agregar_medicion_ep15(
    db: Session,
    sesion_id: int,
    dia: int,
    replicado: int,
    valor: float,
    fecha: Optional[date] = None,
) -> tuple[MedicionEP15, str]:
    stmt = select(MedicionEP15).where(
        MedicionEP15.sesion_id == sesion_id,
        MedicionEP15.dia == dia,
        MedicionEP15.replicado == replicado,
    )
    existe = db.scalars(stmt).first()
    if existe:
        existe.valor = valor
        existe.fecha = fecha
        db.commit()
        db.refresh(existe)
        return existe, ""

    med = MedicionEP15(sesion_id=sesion_id, dia=dia, replicado=replicado, valor=valor, fecha=fecha)
    db.add(med)
    db.commit()
    db.refresh(med)
    return med, ""


def calcular_y_guardar_ep15(db: Session, sesion_id: int) -> tuple[SesionEP15, str]:
    """Calcula los estadísticos EP15-A3 y los guarda en la sesión."""
    from modules.ep15 import calcular_ep15

    sesion = db.get(SesionEP15, sesion_id)
    if not sesion:
        return None, "Sesión no encontrada."

    stmt = (
        select(MedicionEP15)
        .where(MedicionEP15.sesion_id == sesion_id)
        .order_by(MedicionEP15.dia, MedicionEP15.replicado)
    )
    mediciones = db.scalars(stmt).all()

    # Construir matriz [dia][replicado]
    datos: dict[int, dict[int, float]] = {}
    for m in mediciones:
        datos.setdefault(m.dia, {})[m.replicado] = m.valor

    n_dias = sesion.n_dias
    n_reps = sesion.n_replicados
    matriz = []
    for d in range(1, n_dias + 1):
        fila = []
        for r in range(1, n_reps + 1):
            v = datos.get(d, {}).get(r)
            if v is None:
                return None, f"Falta la medición del Día {d}, Replicado {r}."
            fila.append(v)
        matriz.append(fila)

    res = calcular_ep15(
        datos=matriz,
        valor_referencia=sesion.valor_referencia,
        cv_r_fabricante=sesion.cv_r_fabricante,
        cv_ip_fabricante=sesion.cv_ip_fabricante,
        sesgo_permitido=sesion.sesgo_permitido,
    )

    sesion.grand_mean = res.grand_mean
    sesion.de_r = res.de_r
    sesion.cv_r = res.cv_r
    sesion.de_ip = res.de_ip
    sesion.cv_ip = res.cv_ip
    sesion.sesgo_absoluto = res.sesgo_absoluto
    sesion.sesgo_porcentual = res.sesgo_porcentual
    sesion.verificacion_precision_r = res.verificacion_precision_r
    sesion.verificacion_precision_ip = res.verificacion_precision_ip
    sesion.verificacion_sesgo = res.verificacion_sesgo
    sesion.completada = True
    db.commit()
    db.refresh(sesion)
    return sesion, ""


def listar_sesiones_ep15(db: Session, material_id: Optional[int] = None) -> list[SesionEP15]:
    stmt = select(SesionEP15)
    if material_id:
        stmt = stmt.where(SesionEP15.material_id == material_id)
    return list(db.scalars(stmt.order_by(SesionEP15.registrado_en.desc())))


# ═══════════════════════════════════════════════════════════════════════════════
# ACCIONES CORRECTIVAS
# ═══════════════════════════════════════════════════════════════════════════════

def registrar_accion_correctiva(
    db: Session,
    control_id: int,
    personal_id: int,
    fecha: date,
    hora: time,
    causa_probable: str,
    accion_tomada: str,
    resultado: str = "PENDIENTE",
    requiere_repeticion: bool = False,
    observaciones: str = "",
) -> tuple[AccionCorrectiva, str]:
    stmt = select(AccionCorrectiva).where(AccionCorrectiva.control_id == control_id)
    existe = db.scalars(stmt).first()
    if existe:
        # Actualizar en lugar de duplicar
        existe.causa_probable = causa_probable
        existe.accion_tomada = accion_tomada
        existe.resultado = resultado
        existe.requiere_repeticion_control = requiere_repeticion
        existe.observaciones = observaciones
        existe.personal_id = personal_id
        existe.fecha = fecha
        existe.hora = hora
        db.commit()
        db.refresh(existe)
        return existe, ""

    ac = AccionCorrectiva(
        control_id=control_id,
        personal_id=personal_id,
        fecha=fecha,
        hora=hora,
        causa_probable=causa_probable,
        accion_tomada=accion_tomada.strip(),
        resultado=resultado,
        requiere_repeticion_control=requiere_repeticion,
        observaciones=observaciones.strip(),
    )
    db.add(ac)
    db.commit()
    db.refresh(ac)
    return ac, ""


def listar_acciones_correctivas(
    db: Session,
    resultado: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> list[AccionCorrectiva]:
    stmt = select(AccionCorrectiva).options(
        joinedload(AccionCorrectiva.control)
            .joinedload(ControlDiario.material)
            .joinedload(MaterialControl.equipo)
            .joinedload(Equipo.area),
        joinedload(AccionCorrectiva.control)
            .joinedload(ControlDiario.nivel_lote),
        joinedload(AccionCorrectiva.personal),
    )
    if resultado:
        stmt = stmt.where(AccionCorrectiva.resultado == resultado)
    if fecha_desde:
        stmt = stmt.where(AccionCorrectiva.fecha >= fecha_desde)
    if fecha_hasta:
        stmt = stmt.where(AccionCorrectiva.fecha <= fecha_hasta)
    return list(
        db.scalars(stmt.order_by(AccionCorrectiva.fecha.desc(), AccionCorrectiva.hora.desc())).unique()
    )


def get_accion_correctiva_por_control(db: Session, control_id: int) -> Optional[AccionCorrectiva]:
    stmt = select(AccionCorrectiva).where(AccionCorrectiva.control_id == control_id)
    return db.scalars(stmt).first()


def controles_sin_accion_correctiva(db: Session) -> list[ControlDiario]:
    """Devuelve controles rechazados que aún no tienen acción correctiva registrada."""
    stmt = (
        select(ControlDiario)
        .options(
            joinedload(ControlDiario.material)
                .joinedload(MaterialControl.equipo)
                .joinedload(Equipo.area),
            joinedload(ControlDiario.nivel_lote),
            joinedload(ControlDiario.personal),
        )
        .where(
            ControlDiario.resultado == "RECHAZO",
            ~exists().where(AccionCorrectiva.control_id == ControlDiario.id),
        )
        .order_by(ControlDiario.fecha.desc())
    )
    return list(db.scalars(stmt).unique())


# ═══════════════════════════════════════════════════════════════════════════════
# ÍNDICE DE CALIDAD (TEa / Sigma)
# ═══════════════════════════════════════════════════════════════════════════════

def guardar_indice_calidad(
    db: Session,
    material_id: int,
    tea: float,
    sesgo_porcentual: float = 0.0,
    fuente_tea: str = "",
) -> IndiceCalidad:
    stmt = select(IndiceCalidad).where(IndiceCalidad.material_id == material_id)
    ic = db.scalars(stmt).first()
    if ic:
        ic.tea = tea
        ic.sesgo_porcentual = sesgo_porcentual
        ic.fuente_tea = fuente_tea.strip()
    else:
        ic = IndiceCalidad(
            material_id=material_id,
            tea=tea,
            sesgo_porcentual=sesgo_porcentual,
            fuente_tea=fuente_tea.strip(),
        )
        db.add(ic)
    db.commit()
    db.refresh(ic)
    return ic


def obtener_indice_calidad(db: Session, material_id: int) -> Optional[IndiceCalidad]:
    stmt = select(IndiceCalidad).where(IndiceCalidad.material_id == material_id)
    return db.scalars(stmt).first()


def listar_indices_calidad(db: Session) -> list[IndiceCalidad]:
    return list(db.scalars(select(IndiceCalidad)))


# ═══════════════════════════════════════════════════════════════════════════════
# CALIBRACIONES
# ═══════════════════════════════════════════════════════════════════════════════

def registrar_calibracion(
    db: Session,
    equipo_id: int,
    personal_id: Optional[int],
    fecha: date,
    tipo: str,
    lote_calibrador: str = "",
    resultado: str = "APROBADA",
    observaciones: str = "",
    proxima_calibracion: Optional[date] = None,
) -> Calibracion:
    cal = Calibracion(
        equipo_id=equipo_id,
        personal_id=personal_id,
        fecha=fecha,
        tipo=tipo,
        lote_calibrador=lote_calibrador.strip(),
        resultado=resultado,
        observaciones=observaciones.strip(),
        proxima_calibracion=proxima_calibracion,
    )
    db.add(cal)
    db.commit()
    db.refresh(cal)
    return cal


def listar_calibraciones(
    db: Session,
    equipo_id: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> list[Calibracion]:
    stmt = select(Calibracion)
    if equipo_id:
        stmt = stmt.where(Calibracion.equipo_id == equipo_id)
    if fecha_desde:
        stmt = stmt.where(Calibracion.fecha >= fecha_desde)
    if fecha_hasta:
        stmt = stmt.where(Calibracion.fecha <= fecha_hasta)
    return list(db.scalars(stmt.order_by(Calibracion.fecha.desc())))


def proximas_calibraciones(db: Session, dias: int = 30) -> list[Calibracion]:
    desde = date.today()
    hasta = desde + timedelta(days=dias)
    stmt = (
        select(Calibracion)
        .where(Calibracion.proxima_calibracion.between(desde, hasta))
        .order_by(Calibracion.proxima_calibracion.asc())
    )
    return list(db.scalars(stmt))


# ═══════════════════════════════════════════════════════════════════════════════
# MANTENIMIENTO
# ═══════════════════════════════════════════════════════════════════════════════

def registrar_mantenimiento(
    db: Session,
    equipo_id: int,
    personal_id: Optional[int],
    fecha: date,
    tipo: str,
    descripcion: str,
    resultado: str = "COMPLETADO",
    proxima_fecha: Optional[date] = None,
) -> Mantenimiento:
    mant = Mantenimiento(
        equipo_id=equipo_id,
        personal_id=personal_id,
        fecha=fecha,
        tipo=tipo,
        descripcion=descripcion.strip(),
        resultado=resultado,
        proxima_fecha=proxima_fecha,
    )
    db.add(mant)
    db.commit()
    db.refresh(mant)
    return mant


def listar_mantenimientos(
    db: Session,
    equipo_id: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
) -> list[Mantenimiento]:
    stmt = select(Mantenimiento)
    if equipo_id:
        stmt = stmt.where(Mantenimiento.equipo_id == equipo_id)
    if fecha_desde:
        stmt = stmt.where(Mantenimiento.fecha >= fecha_desde)
    if fecha_hasta:
        stmt = stmt.where(Mantenimiento.fecha <= fecha_hasta)
    return list(db.scalars(stmt.order_by(Mantenimiento.fecha.desc())))


def proximos_mantenimientos(db: Session, dias: int = 30) -> list[Mantenimiento]:
    desde = date.today()
    hasta = desde + timedelta(days=dias)
    stmt = (
        select(Mantenimiento)
        .where(Mantenimiento.proxima_fecha.between(desde, hasta))
        .order_by(Mantenimiento.proxima_fecha.asc())
    )
    return list(db.scalars(stmt))


# ═══════════════════════════════════════════════════════════════════════════════
# CARGA MASIVA DE CONTROLES
# ═══════════════════════════════════════════════════════════════════════════════

def insertar_controles_masivo(
    db: Session,
    registros: list[dict],
) -> tuple[int, int, list[str]]:
    """
    Inserta múltiples controles en lote.
    Cada dict en registros tiene:
        material_id, lote_id, nivel_lote_id, personal_id,
        fecha, hora, turno, valor, comentario, es_retroactivo
    Retorna (insertados, omitidos, errores[])
    """
    insertados = 0
    omitidos   = 0
    errores    = []

    for i, reg in enumerate(registros):
        try:
            material_id   = reg["material_id"]
            nivel_lote_id = reg["nivel_lote_id"]
            fecha         = reg["fecha"]
            hora          = reg["hora"]

            if existe_control_diario(db, material_id, nivel_lote_id, fecha, hora):
                omitidos += 1
                continue

            nivel_lote = db.get(NivelLote, nivel_lote_id)
            if not nivel_lote:
                errores.append(f"Fila {i+1}: nivel de lote no encontrado.")
                continue

            hist_zs  = historial_zscores(db, nivel_lote_id)
            otros_zs = zscores_mismo_run(db, material_id, fecha, hora, nivel_lote.nivel, reg["lote_id"])

            resultado_wg = evaluar_westgard(
                valor_nuevo=reg["valor"],
                media=nivel_lote.media,
                de=nivel_lote.de,
                historial_zscores=hist_zs,
                historial_zscores_otros_niveles=otros_zs if otros_zs else None,
            )

            control = ControlDiario(
                material_id=material_id,
                lote_id=reg["lote_id"],
                nivel_lote_id=nivel_lote_id,
                personal_id=reg["personal_id"],
                fecha=fecha,
                hora=hora,
                turno=reg.get("turno"),
                valor=reg["valor"],
                zscore=resultado_wg.zscore,
                resultado=resultado_wg.resultado,
                regla_violada=resultado_wg.regla_violada,
                es_retroactivo=reg.get("es_retroactivo", True),
                comentario=reg.get("comentario", "").strip(),
            )
            db.add(control)
            insertados += 1

        except Exception as e:
            errores.append(f"Fila {i+1}: {e}")

    if insertados:
        db.commit()
    return insertados, omitidos, errores
