from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey,
    Boolean, Date, Time, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

TURNOS = ["MAÑANA", "TARDE", "NOCHE", "GUARDIA"]

CAUSAS_PROBABLES = [
    "Error de operador",
    "Problema con el reactivo",
    "Falla del equipo",
    "Error de calibración",
    "Interferencia de la muestra",
    "Problema ambiental (temperatura/humedad)",
    "Lote de control vencido o deteriorado",
    "Causa no identificada",
    "Otro",
]

RESULTADOS_AC = ["PENDIENTE", "RESUELTO", "ESCALADO A SUPERVISIÓN"]


class Area(Base):
    __tablename__ = "areas"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    equipos = relationship("Equipo", back_populates="area", cascade="all, delete-orphan")


class Equipo(Base):
    __tablename__ = "equipos"
    id = Column(Integer, primary_key=True)
    area_id = Column(Integer, ForeignKey("areas.id"), nullable=False)
    nombre = Column(String(100), nullable=False)
    modelo = Column(String(100))
    numero_serie = Column(String(100))
    activo = Column(Boolean, default=True)
    area = relationship("Area", back_populates="equipos")
    materiales = relationship("MaterialControl", back_populates="equipo", cascade="all, delete-orphan")


class Personal(Base):
    __tablename__ = "personal"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    codigo = Column(String(20), unique=True)
    cargo = Column(String(100))
    activo = Column(Boolean, default=True)
    controles_diarios = relationship("ControlDiario", back_populates="personal")
    controles_externos = relationship("ControlExterno", back_populates="personal")
    acciones_correctivas = relationship("AccionCorrectiva", back_populates="personal")


class MaterialControl(Base):
    __tablename__ = "materiales_control"
    id = Column(Integer, primary_key=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False)
    analito = Column(String(100), nullable=False)
    proveedor = Column(String(100), nullable=False)
    unidad = Column(String(30))
    nombre_material = Column(String(150))
    activo = Column(Boolean, default=True)
    equipo = relationship("Equipo", back_populates="materiales")
    lotes = relationship("Lote", back_populates="material", cascade="all, delete-orphan")
    controles_diarios = relationship("ControlDiario", back_populates="material")
    controles_externos = relationship("ControlExterno", back_populates="material")
    sesiones_ep15 = relationship("SesionEP15", back_populates="material")


class Lote(Base):
    __tablename__ = "lotes"
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey("materiales_control.id"), nullable=False)
    numero_lote = Column(String(50), nullable=False)
    fecha_vencimiento = Column(Date, nullable=False)
    activo = Column(Boolean, default=True)
    material = relationship("MaterialControl", back_populates="lotes")
    niveles = relationship("NivelLote", back_populates="lote", cascade="all, delete-orphan")
    controles_diarios = relationship("ControlDiario", back_populates="lote")
    __table_args__ = (UniqueConstraint("material_id", "numero_lote", name="uq_material_lote"),)


class NivelLote(Base):
    __tablename__ = "niveles_lote"
    id = Column(Integer, primary_key=True)
    lote_id = Column(Integer, ForeignKey("lotes.id"), nullable=False)
    nivel = Column(Integer, nullable=False)
    valor_minimo = Column(Float, nullable=False)
    valor_maximo = Column(Float, nullable=False)
    media = Column(Float, nullable=False)
    de = Column(Float, nullable=False)
    lote = relationship("Lote", back_populates="niveles")
    controles = relationship("ControlDiario", back_populates="nivel_lote")
    __table_args__ = (UniqueConstraint("lote_id", "nivel", name="uq_lote_nivel"),)


class ControlDiario(Base):
    __tablename__ = "controles_diarios"
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey("materiales_control.id"), nullable=False)
    lote_id = Column(Integer, ForeignKey("lotes.id"), nullable=False)
    nivel_lote_id = Column(Integer, ForeignKey("niveles_lote.id"), nullable=False)
    personal_id = Column(Integer, ForeignKey("personal.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    turno = Column(String(20))                   # MAÑANA / TARDE / NOCHE / GUARDIA
    valor = Column(Float, nullable=False)
    zscore = Column(Float)
    resultado = Column(String(20))               # OK / ADVERTENCIA / RECHAZO
    regla_violada = Column(String(30))
    es_retroactivo = Column(Boolean, default=False)
    comentario = Column(Text)
    registrado_en = Column(DateTime, default=datetime.now)
    material = relationship("MaterialControl", back_populates="controles_diarios")
    lote = relationship("Lote", back_populates="controles_diarios")
    nivel_lote = relationship("NivelLote", back_populates="controles")
    personal = relationship("Personal", back_populates="controles_diarios")
    accion_correctiva = relationship("AccionCorrectiva", back_populates="control", uselist=False)
    __table_args__ = (
        UniqueConstraint("material_id", "nivel_lote_id", "fecha", "hora", name="uq_control_diario"),
    )


class AccionCorrectiva(Base):
    """Acción correctiva asociada a un control rechazado."""
    __tablename__ = "acciones_correctivas"
    id = Column(Integer, primary_key=True)
    control_id = Column(Integer, ForeignKey("controles_diarios.id"), nullable=False, unique=True)
    personal_id = Column(Integer, ForeignKey("personal.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    causa_probable = Column(String(200))
    accion_tomada = Column(Text, nullable=False)
    resultado = Column(String(50), default="PENDIENTE")
    requiere_repeticion_control = Column(Boolean, default=False)
    observaciones = Column(Text)
    registrado_en = Column(DateTime, default=datetime.now)
    control = relationship("ControlDiario", back_populates="accion_correctiva")
    personal = relationship("Personal", back_populates="acciones_correctivas")


class ControlExterno(Base):
    __tablename__ = "controles_externos"
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey("materiales_control.id"), nullable=False)
    personal_id = Column(Integer, ForeignKey("personal.id"))
    proveedor_externo = Column(String(100), nullable=False)
    periodo = Column(String(50), nullable=False)
    nivel = Column(Integer, default=1)
    valor_obtenido = Column(Float, nullable=False)
    valor_diana = Column(Float)
    de_grupo = Column(Float)
    n_participantes = Column(Integer)
    zscore = Column(Float)
    percentil = Column(Float)
    resultado = Column(String(30))
    comentario = Column(Text)
    registrado_en = Column(DateTime, default=datetime.now)
    material = relationship("MaterialControl", back_populates="controles_externos")
    personal = relationship("Personal", back_populates="controles_externos")
    __table_args__ = (
        UniqueConstraint("material_id", "proveedor_externo", "periodo", "nivel", name="uq_control_externo"),
    )


class SesionEP15(Base):
    __tablename__ = "sesiones_ep15"
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey("materiales_control.id"), nullable=False)
    nombre_sesion = Column(String(200), nullable=False)
    nivel = Column(Integer, default=1)
    n_dias = Column(Integer, default=5)
    n_replicados = Column(Integer, default=3)
    cv_r_fabricante = Column(Float)
    cv_ip_fabricante = Column(Float)
    sesgo_permitido = Column(Float)
    valor_referencia = Column(Float)
    completada = Column(Boolean, default=False)
    grand_mean = Column(Float)
    de_r = Column(Float)
    cv_r = Column(Float)
    de_ip = Column(Float)
    cv_ip = Column(Float)
    sesgo_absoluto = Column(Float)
    sesgo_porcentual = Column(Float)
    verificacion_precision_r = Column(Boolean)
    verificacion_precision_ip = Column(Boolean)
    verificacion_sesgo = Column(Boolean)
    comentario = Column(Text)
    registrado_en = Column(DateTime, default=datetime.now)
    material = relationship("MaterialControl", back_populates="sesiones_ep15")
    mediciones = relationship("MedicionEP15", back_populates="sesion", cascade="all, delete-orphan")


class MedicionEP15(Base):
    __tablename__ = "mediciones_ep15"
    id = Column(Integer, primary_key=True)
    sesion_id = Column(Integer, ForeignKey("sesiones_ep15.id"), nullable=False)
    dia = Column(Integer, nullable=False)
    replicado = Column(Integer, nullable=False)
    valor = Column(Float, nullable=False)
    fecha = Column(Date)
    sesion = relationship("SesionEP15", back_populates="mediciones")
    __table_args__ = (
        UniqueConstraint("sesion_id", "dia", "replicado", name="uq_medicion_ep15"),
    )
