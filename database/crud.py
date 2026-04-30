"""
Operaciones CRUD para todos los modelos del sistema.
"""

from datetime import date, time, datetime
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from .models import (
    Area, Equipo, Personal, MaterialControl, Lote, NivelLote,
    ControlDiario, ControlExterno, SesionEP15, MedicionEP15, AccionCorrectiva,
    IndiceCalidad, Calibracion, Mantenimiento,
)
from modules.westgard import evaluar_westgard


# ═══════════════════════════════════════════════════════════════════════════════
# ÁREAS
# ═══════════════════════════════════════════════════════════════════════════════

def listar_areas(db: Session, solo_activos: bool = True) -> list[Area]:
    q = db.query(Area)
    if solo_activos:
        q = q.filter(Area.activo == True)
    return q.order_by(Area.nombre).all()


def crear_area(db: Session, nombre: str, descripcion: str = "") -> Area:
    area = Area(nombre=nombre.strip(), descripcion=descripcion.strip())
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


def desactivar_area(db: Session, area_id: int) -> bool:
    area = db.query(Area).filter(Area.id == area_id).first()
    if area:
        area.activo = False
        db.commit()
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# EQUIPOS
# ═══════════════════════════════════════════════════════════════════════════════

def listar_equipos(db: Session, area_id: Optional[int] = None, solo_activos: bool = True) -> list[Equipo]:
    q = db.query(Equipo).options(joinedload(Equipo.area))
    if area_id:
        q = q.filter(Equipo.area_id == area_id)
    if solo_activos:
        q = q.filter(Equipo.activo == True)
    return q.order_by(Equipo.nombre).all()


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


def desactivar_equipo(db: Session, equipo_id: int) -> bool:
    equipo = db.query(Equipo).filter(Equipo.id == equipo_id).first()
    if equipo:
        equipo.activo = False
        db.commit()
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# PERSONAL
# ═══════════════════════════════════════════════════════════════════════════════

def listar_personal(db: Session, solo_activos: bool = True) -> list[Personal]:
    q = db.query(Personal)
    if solo_activos:
        q = q.filter(Personal.activo == True)
    return q.order_by(Personal.apellido, Personal.nombre).all()


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


def desactivar_personal(db: Session, personal_id: int) -> bool:
    p = db.query(Personal).filter(Personal.id == personal_id).first()
    if p:
        p.activo = False
        db.commit()
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# MATERIALES DE CONTROL (ANALITOS)
# ═══════════════════════════════════════════════════════════════════════════════

def listar_materiales(db: Session, equipo_id: Optional[int] = None, solo_activos: bool = True) -> list[MaterialControl]:
    q = db.query(MaterialControl).options(
        joinedload(MaterialControl.equipo).joinedload(Equipo.area)
    )
    if equipo_id:
        q = q.filter(MaterialControl.equipo_id == equipo_id)
    if solo_activos:
        q = q.filter(MaterialControl.activo == True)
    return q.order_by(MaterialControl.analito).all()


def crear_material(
    db: Session,
    equipo_id: int,
    analito: str,
    proveedor: str,
    unidad: str = "",
    nombre_material: str = "",
) -> MaterialControl:
    m = MaterialControl(
        equipo_id=equipo_id,
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
    m = db.query(MaterialControl).filter(MaterialControl.id == material_id).first()
    if m:
        m.activo = False
        db.commit()
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# LOTES Y NIVELES
# ═══════════════════════════════════════════════════════════════════════════════

def listar_lotes(db: Session, material_id: int, solo_activos: bool = True) -> list[Lote]:
    q = db.query(Lote).filter(Lote.material_id == material_id)
    if solo_activos:
        q = q.filter(Lote.activo == True)
    return q.order_by(Lote.fecha_vencimiento.desc()).all()


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


def get_lote_activo(db: Session, material_id: int) -> Optional[Lote]:
    """Devuelve el lote activo no vencido más reciente para un material."""
    hoy = date.today()
    return (
        db.query(Lote)
        .filter(
            Lote.material_id == material_id,
            Lote.activo == True,
            Lote.fecha_vencimiento >= hoy,
        )
        .order_by(Lote.fecha_vencimiento.desc())
        .first()
    )


def get_nivel_lote(db: Session, lote_id: int, nivel: int) -> Optional[NivelLote]:
    return (
        db.query(NivelLote)
        .filter(NivelLote.lote_id == lote_id, NivelLote.nivel == nivel)
        .first()
    )


def lotes_por_vencer(db: Session, dias: int = 30) -> list[Lote]:
    from datetime import timedelta
    hoy = date.today()
    limite = hoy + timedelta(days=dias)
    return (
        db.query(Lote)
        .filter(Lote.activo == True, Lote.fecha_vencimiento <= limite, Lote.fecha_vencimiento >= hoy)
        .order_by(Lote.fecha_vencimiento)
        .all()
    )


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
    q = (
        db.query(ControlDiario)
        .filter(ControlDiario.nivel_lote_id == nivel_lote_id)
    )
    if excluir_id:
        q = q.filter(ControlDiario.id != excluir_id)
    controles = q.order_by(ControlDiario.fecha.desc(), ControlDiario.hora.desc()).limit(limite).all()
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
    controles = (
        db.query(ControlDiario)
        .join(NivelLote)
        .filter(
            ControlDiario.material_id == material_id,
            ControlDiario.fecha == fecha,
            ControlDiario.lote_id == lote_id,
            NivelLote.nivel != nivel_excluido,
        )
        .all()
    )
    return [c.zscore for c in controles if c.zscore is not None]


def existe_control_diario(
    db: Session,
    material_id: int,
    nivel_lote_id: int,
    fecha: date,
    hora: time,
) -> bool:
    return (
        db.query(ControlDiario)
        .filter(
            ControlDiario.material_id == material_id,
            ControlDiario.nivel_lote_id == nivel_lote_id,
            ControlDiario.fecha == fecha,
            ControlDiario.hora == hora,
        )
        .first()
    ) is not None


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

    nivel_lote = db.query(NivelLote).filter(NivelLote.id == nivel_lote_id).first()
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
) -> list[ControlDiario]:
    q = db.query(ControlDiario).options(
        joinedload(ControlDiario.nivel_lote),
        joinedload(ControlDiario.personal),
        joinedload(ControlDiario.accion_correctiva),
        joinedload(ControlDiario.material).joinedload(MaterialControl.equipo).joinedload(Equipo.area),
    )
    if material_id:
        q = q.filter(ControlDiario.material_id == material_id)
    if fecha_desde:
        q = q.filter(ControlDiario.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(ControlDiario.fecha <= fecha_hasta)
    if nivel is not None:
        q = q.join(NivelLote).filter(NivelLote.nivel == nivel)
    if personal_id:
        q = q.filter(ControlDiario.personal_id == personal_id)
    return q.order_by(ControlDiario.fecha.asc(), ControlDiario.hora.asc()).all()


def eliminar_control_diario(db: Session, control_id: int) -> bool:
    c = db.query(ControlDiario).filter(ControlDiario.id == control_id).first()
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
    existe = (
        db.query(ControlExterno)
        .filter(
            ControlExterno.material_id == material_id,
            ControlExterno.proveedor_externo == proveedor_externo,
            ControlExterno.periodo == periodo,
            ControlExterno.nivel == nivel,
        )
        .first()
    )
    if existe:
        return None, f"Ya existe un control externo para ese analito, proveedor, período y nivel."

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
    q = db.query(ControlExterno)
    if material_id:
        q = q.filter(ControlExterno.material_id == material_id)
    if proveedor:
        q = q.filter(ControlExterno.proveedor_externo == proveedor)
    return q.order_by(ControlExterno.periodo.asc()).all()


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
    existe = (
        db.query(MedicionEP15)
        .filter(
            MedicionEP15.sesion_id == sesion_id,
            MedicionEP15.dia == dia,
            MedicionEP15.replicado == replicado,
        )
        .first()
    )
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

    sesion = db.query(SesionEP15).filter(SesionEP15.id == sesion_id).first()
    if not sesion:
        return None, "Sesión no encontrada."

    mediciones = (
        db.query(MedicionEP15)
        .filter(MedicionEP15.sesion_id == sesion_id)
        .order_by(MedicionEP15.dia, MedicionEP15.replicado)
        .all()
    )

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
    q = db.query(SesionEP15)
    if material_id:
        q = q.filter(SesionEP15.material_id == material_id)
    return q.order_by(SesionEP15.registrado_en.desc()).all()


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
    existe = db.query(AccionCorrectiva).filter(AccionCorrectiva.control_id == control_id).first()
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
    q = db.query(AccionCorrectiva)
    if resultado:
        q = q.filter(AccionCorrectiva.resultado == resultado)
    if fecha_desde:
        q = q.filter(AccionCorrectiva.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(AccionCorrectiva.fecha <= fecha_hasta)
    return q.order_by(AccionCorrectiva.fecha.desc(), AccionCorrectiva.hora.desc()).all()


def get_accion_correctiva_por_control(db: Session, control_id: int) -> Optional[AccionCorrectiva]:
    return db.query(AccionCorrectiva).filter(AccionCorrectiva.control_id == control_id).first()


def controles_sin_accion_correctiva(db: Session) -> list[ControlDiario]:
    """Devuelve controles rechazados que aún no tienen acción correctiva registrada."""
    from sqlalchemy import not_, exists
    return (
        db.query(ControlDiario)
        .filter(
            ControlDiario.resultado == "RECHAZO",
            ~exists().where(AccionCorrectiva.control_id == ControlDiario.id),
        )
        .order_by(ControlDiario.fecha.desc())
        .all()
    )


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
    ic = db.query(IndiceCalidad).filter(IndiceCalidad.material_id == material_id).first()
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
    return db.query(IndiceCalidad).filter(IndiceCalidad.material_id == material_id).first()


def listar_indices_calidad(db: Session) -> list[IndiceCalidad]:
    return db.query(IndiceCalidad).all()


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
    q = db.query(Calibracion).options(
        joinedload(Calibracion.equipo).joinedload(Equipo.area),
        joinedload(Calibracion.personal),
    )
    if equipo_id:
        q = q.filter(Calibracion.equipo_id == equipo_id)
    if fecha_desde:
        q = q.filter(Calibracion.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(Calibracion.fecha <= fecha_hasta)
    return q.order_by(Calibracion.fecha.desc()).all()


def proximas_calibraciones(db: Session, dias: int = 30) -> list[Calibracion]:
    desde = date.today()
    hasta = date.today().__class__.fromordinal(date.today().toordinal() + dias)
    return (
        db.query(Calibracion)
        .options(joinedload(Calibracion.equipo).joinedload(Equipo.area))
        .filter(Calibracion.proxima_calibracion.between(desde, hasta))
        .order_by(Calibracion.proxima_calibracion.asc())
        .all()
    )


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
    q = db.query(Mantenimiento).options(
        joinedload(Mantenimiento.equipo).joinedload(Equipo.area),
        joinedload(Mantenimiento.personal),
    )
    if equipo_id:
        q = q.filter(Mantenimiento.equipo_id == equipo_id)
    if fecha_desde:
        q = q.filter(Mantenimiento.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(Mantenimiento.fecha <= fecha_hasta)
    return q.order_by(Mantenimiento.fecha.desc()).all()


def proximos_mantenimientos(db: Session, dias: int = 30) -> list[Mantenimiento]:
    desde = date.today()
    hasta = date.today().__class__.fromordinal(date.today().toordinal() + dias)
    return (
        db.query(Mantenimiento)
        .options(joinedload(Mantenimiento.equipo).joinedload(Equipo.area))
        .filter(Mantenimiento.proxima_fecha.between(desde, hasta))
        .order_by(Mantenimiento.proxima_fecha.asc())
        .all()
    )


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
            material_id  = reg["material_id"]
            nivel_lote_id= reg["nivel_lote_id"]
            fecha        = reg["fecha"]
            hora         = reg["hora"]

            if existe_control_diario(db, material_id, nivel_lote_id, fecha, hora):
                omitidos += 1
                continue

            nivel_lote = db.query(NivelLote).filter(NivelLote.id == nivel_lote_id).first()
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
