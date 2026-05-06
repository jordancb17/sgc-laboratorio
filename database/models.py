from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey,
    Boolean, Date, Time, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

TURNOS = ["MAÑANA", "TARDE", "NOCHE", "GUARDIA"]

PANELES_PREDEFINIDOS = {

    # ── HEMATOLOGÍA ──────────────────────────────────────────────────────────
    "🩸 Hemograma — 5-Diff Básico": [
        ("Leucocitos (WBC)",          "×10³/µL"),
        ("Eritrocitos (RBC)",          "×10⁶/µL"),
        ("Hemoglobina",               "g/dL"),
        ("Hematocrito",               "%"),
        ("VCM (MCV)",                 "fL"),
        ("HCM (MCH)",                 "pg"),
        ("CHCM (MCHC)",               "g/dL"),
        ("Plaquetas (PLT)",           "×10³/µL"),
        ("Neutrófilos %",             "%"),
        ("Linfocitos %",              "%"),
        ("Monocitos %",               "%"),
        ("Eosinófilos %",             "%"),
        ("Basófilos %",               "%"),
    ],
    "🩸 Hemograma — 5-Diff Extendido (con reticulocitos e IPF)": [
        # Serie roja
        ("Leucocitos (WBC)",          "×10³/µL"),
        ("Eritrocitos (RBC)",          "×10⁶/µL"),
        ("Hemoglobina",               "g/dL"),
        ("Hematocrito",               "%"),
        ("VCM (MCV)",                 "fL"),
        ("HCM (MCH)",                 "pg"),
        ("CHCM (MCHC)",               "g/dL"),
        ("RDW-CV",                    "%"),
        ("RDW-SD",                    "fL"),
        # Serie blanca — porcentajes
        ("Neutrófilos %",             "%"),
        ("Linfocitos %",              "%"),
        ("Monocitos %",               "%"),
        ("Eosinófilos %",             "%"),
        ("Basófilos %",               "%"),
        ("Granulocitos Inmaduros %",  "%"),
        # Serie blanca — valores absolutos
        ("Neutrófilos #",             "×10³/µL"),
        ("Linfocitos #",              "×10³/µL"),
        ("Monocitos #",               "×10³/µL"),
        ("Eosinófilos #",             "×10³/µL"),
        ("Basófilos #",               "×10³/µL"),
        ("Granulocitos Inmaduros #",  "×10³/µL"),
        # Plaquetas
        ("Plaquetas (PLT)",           "×10³/µL"),
        ("VPM (MPV)",                 "fL"),
        ("PDW",                       "%"),
        ("IPF (Plaquetas Inmaduras)", "%"),
        # Reticulocitos
        ("Reticulocitos %",           "%"),
        ("Reticulocitos #",           "×10³/µL"),
        ("IRF (Fracción Inmadura)",   "%"),
        ("LFR",                       "%"),
        ("MFR",                       "%"),
        ("HFR",                       "%"),
        # NRBC
        ("NRBC %",                    "%"),
        ("NRBC #",                    "×10³/µL"),
    ],

    # ── GASES ARTERIALES ─────────────────────────────────────────────────────
    "🫁 Gases Arteriales / BGA": [
        ("pH",                        ""),
        ("pCO₂",                      "mmHg"),
        ("pO₂",                       "mmHg"),
        ("HCO₃⁻",                     "mmol/L"),
        ("Exceso de Bases (BE)",      "mmol/L"),
        ("SaO₂",                      "%"),
        ("FiO₂",                      "%"),
        ("Lactato",                   "mmol/L"),
        ("Na⁺ (BGA)",                 "mmol/L"),
        ("K⁺ (BGA)",                  "mmol/L"),
        ("Ca²⁺ iónico (BGA)",         "mmol/L"),
        ("Cl⁻ (BGA)",                 "mmol/L"),
        ("Glucosa (BGA)",             "mg/dL"),
        ("Hematocrito (BGA)",         "%"),
        ("Hemoglobina (BGA)",         "g/dL"),
    ],

    # ── ELECTROLITOS ─────────────────────────────────────────────────────────
    "⚡ Electrolitos": [
        ("Sodio (Na⁺)",               "mEq/L"),
        ("Potasio (K⁺)",              "mEq/L"),
        ("Cloro (Cl⁻)",               "mEq/L"),
        ("Calcio total",              "mg/dL"),
        ("Calcio iónico (Ca²⁺)",      "mmol/L"),
        ("Magnesio (Mg²⁺)",           "mEq/L"),
        ("Fósforo inorgánico",        "mg/dL"),
        ("Bicarbonato (HCO₃⁻)",       "mEq/L"),
    ],

    # ── BIOQUÍMICA ───────────────────────────────────────────────────────────
    "🔬 Bioquímica — Panel Hepático": [
        ("AST (TGO)",                 "U/L"),
        ("ALT (TGP)",                 "U/L"),
        ("Fosfatasa Alcalina (FA)",   "U/L"),
        ("GGT (Gamma-GT)",            "U/L"),
        ("LDH",                       "U/L"),
        ("Bilirrubina Total",         "mg/dL"),
        ("Bilirrubina Directa",       "mg/dL"),
        ("Bilirrubina Indirecta",     "mg/dL"),
        ("Proteínas Totales",         "g/dL"),
        ("Albúmina",                  "g/dL"),
        ("Globulinas",                "g/dL"),
        ("5'-Nucleotidasa",           "U/L"),
    ],
    "🔬 Bioquímica — Panel Renal": [
        ("Creatinina",                "mg/dL"),
        ("BUN (Nitrógeno Ureico)",    "mg/dL"),
        ("Urea",                      "mg/dL"),
        ("Ácido Úrico",               "mg/dL"),
        ("Cistatina C",               "mg/L"),
    ],
    "🔬 Bioquímica — Panel Lipídico": [
        ("Colesterol Total",          "mg/dL"),
        ("HDL Colesterol",            "mg/dL"),
        ("LDL Colesterol",            "mg/dL"),
        ("VLDL Colesterol",           "mg/dL"),
        ("Triglicéridos",             "mg/dL"),
        ("No-HDL Colesterol",         "mg/dL"),
        ("Lipoproteína (a) [Lp(a)]",  "mg/dL"),
        ("Apolipoproteína A-I",       "mg/dL"),
        ("Apolipoproteína B",         "mg/dL"),
    ],
    "🔬 Bioquímica — Panel Metabólico Completo": [
        ("Glucosa",                   "mg/dL"),
        ("Hemoglobina Glicosilada A1c","% Hgb"),
        ("Insulina",                  "µUI/mL"),
        ("Creatinina",                "mg/dL"),
        ("BUN",                       "mg/dL"),
        ("Ácido Úrico",               "mg/dL"),
        ("Sodio (Na⁺)",               "mEq/L"),
        ("Potasio (K⁺)",              "mEq/L"),
        ("Cloro (Cl⁻)",               "mEq/L"),
        ("Calcio total",              "mg/dL"),
        ("Magnesio (Mg²⁺)",           "mEq/L"),
        ("Fósforo",                   "mg/dL"),
        ("AST (TGO)",                 "U/L"),
        ("ALT (TGP)",                 "U/L"),
        ("Fosfatasa Alcalina",        "U/L"),
        ("GGT",                       "U/L"),
        ("Bilirrubina Total",         "mg/dL"),
        ("Proteínas Totales",         "g/dL"),
        ("Albúmina",                  "g/dL"),
        ("Colesterol Total",          "mg/dL"),
        ("Triglicéridos",             "mg/dL"),
        ("HDL Colesterol",            "mg/dL"),
        ("LDL Colesterol",            "mg/dL"),
        ("Proteína C Reactiva (PCR)", "mg/L"),
        ("Amilasa",                   "U/L"),
        ("Lipasa",                    "U/L"),
    ],
    "❤️ Bioquímica — Marcadores Cardíacos": [
        ("Troponina I",               "ng/mL"),
        ("Troponina T",               "ng/mL"),
        ("Troponina I Alta Sensibilidad (hs-TnI)", "ng/L"),
        ("Troponina T Alta Sensibilidad (hs-TnT)", "ng/L"),
        ("CK Total (Creatinquinasa)", "U/L"),
        ("CK-MB (actividad)",         "U/L"),
        ("CK-MB (masa)",              "ng/mL"),
        ("Mioglobina",                "ng/mL"),
        ("NT-proBNP",                 "pg/mL"),
        ("BNP",                       "pg/mL"),
        ("LDH",                       "U/L"),
        ("PCR ultrasensible",         "mg/L"),
        ("Homocisteína",              "µmol/L"),
    ],
    "🧬 Bioquímica — Panel Tiroideo": [
        ("TSH",                       "µUI/mL"),
        ("T4 libre (FT4)",            "ng/dL"),
        ("T3 libre (FT3)",            "pg/mL"),
        ("T4 total",                  "µg/dL"),
        ("T3 total",                  "ng/dL"),
        ("Anti-TPO (Anti-peroxidasa)","UI/mL"),
        ("Anti-Tg (Anti-tiroglobulina)","UI/mL"),
        ("Anti-TSH receptor",         "UI/L"),
        ("Tiroglobulina",             "ng/mL"),
        ("Calcitonina",               "pg/mL"),
    ],
    "🔬 Bioquímica — Panel Enzimático": [
        ("Amilasa",                   "U/L"),
        ("Lipasa",                    "U/L"),
        ("Colinesterasa",             "U/L"),
        ("Aldolasa",                  "U/L"),
        ("LDH",                       "U/L"),
        ("CK Total",                  "U/L"),
        ("Fosfatasa Alcalina",        "U/L"),
        ("GGT",                       "U/L"),
        ("AST",                       "U/L"),
        ("ALT",                       "U/L"),
    ],
    "🦠 Bioquímica — Marcadores Inflamatorios / Infecciosos": [
        ("PCR (Proteína C Reactiva)",  "mg/L"),
        ("PCR ultrasensible",          "mg/L"),
        ("Procalcitonina (PCT)",       "ng/mL"),
        ("IL-6 (Interleucina 6)",      "pg/mL"),
        ("Ferritina",                  "ng/mL"),
        ("Fibrinógeno",                "mg/dL"),
        ("VSG (Velocidad Sedimentación)","mm/h"),
        ("LDH",                        "U/L"),
    ],

    # ── COAGULACIÓN ──────────────────────────────────────────────────────────
    "🩸 Coagulación — Panel Básico": [
        ("TP (Tiempo de Protrombina)",             "segundos"),
        ("INR",                                    ""),
        ("Actividad de Protrombina (%)",           "%"),
        ("TTPA (Tiempo Tromboplastina Parcial Act.)", "segundos"),
        ("Relación TTPA (R)",                      ""),
        ("Fibrinógeno (método Clauss)",            "mg/dL"),
        ("Tiempo de Trombina (TT)",                "segundos"),
        ("Dímero-D",                               "ng/mL FEU"),
    ],
    "🩸 Coagulación — Panel Extendido (Trombofilia / Factores)": [
        ("TP",                            "segundos"),
        ("INR",                           ""),
        ("Actividad de Protrombina",      "%"),
        ("TTPA",                          "segundos"),
        ("Fibrinógeno",                   "mg/dL"),
        ("Dímero-D",                      "ng/mL FEU"),
        ("Antitrombina III (AT-III)",     "%"),
        ("Proteína C (actividad)",        "%"),
        ("Proteína S total",              "%"),
        ("Proteína S libre",              "%"),
        ("Factor II (Protrombina)",       "%"),
        ("Factor V",                      "%"),
        ("Factor VII",                    "%"),
        ("Factor VIII",                   "%"),
        ("Factor IX",                     "%"),
        ("Factor X",                      "%"),
        ("Factor XI",                     "%"),
        ("Factor XII",                    "%"),
        ("VWF:Ag (Factor Von Willebrand)","% o UI/dL"),
        ("VWF:RCo (Actividad Ristocetina)","% o UI/dL"),
    ],

    # ── ORINA ─────────────────────────────────────────────────────────────────
    "🧪 Orina — Análisis Fisicoquímico + Sedimento": [
        ("pH",                         ""),
        ("Densidad",                   "g/mL"),
        ("Proteínas",                  "mg/dL"),
        ("Glucosa",                    "mg/dL"),
        ("Bilirrubina",                "µmol/L"),
        ("Urobilinógeno",              "µmol/L"),
        ("Cetonas",                    "mg/dL"),
        ("Sangre / Hemoglobina",       "Ery/µL"),
        ("Leucocitos esterasa",        "Leu/µL"),
        ("Nitritos",                   ""),
        ("Sedimento: Leucocitos",      "/campo"),
        ("Sedimento: Eritrocitos",     "/campo"),
        ("Sedimento: Células epiteliales","/campo"),
        ("Sedimento: Cilindros hialinos","/campo"),
        ("Sedimento: Bacterias",       "/campo"),
    ],
}

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
    marca = Column(String(100))
    modelo = Column(String(100))
    numero_serie = Column(String(100))
    activo = Column(Boolean, default=True)
    area = relationship("Area", back_populates="equipos")
    materiales = relationship("MaterialControl", back_populates="equipo", cascade="all, delete-orphan")
    grupos = relationship("GrupoAnalitos", back_populates="equipo", cascade="all, delete-orphan")


class GrupoAnalitos(Base):
    """Panel o batería de pruebas: conjunto de analitos analizados juntos (hemograma, gases, etc.)."""
    __tablename__ = "grupos_analitos"
    id = Column(Integer, primary_key=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text)
    activo = Column(Boolean, default=True)
    equipo = relationship("Equipo", back_populates="grupos")
    materiales = relationship("MaterialControl", back_populates="grupo")


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
    grupo_id = Column(Integer, ForeignKey("grupos_analitos.id"), nullable=True)
    analito = Column(String(100), nullable=False)
    proveedor = Column(String(100), nullable=False)
    unidad = Column(String(30))
    nombre_material = Column(String(150))
    activo = Column(Boolean, default=True)
    equipo = relationship("Equipo", back_populates="materiales")
    grupo = relationship("GrupoAnalitos", back_populates="materiales")
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
    __table_args__ = (
        UniqueConstraint("material_id", "numero_lote", name="uq_material_lote"),
        Index("ix_lotes_material_vencimiento", "material_id", "fecha_vencimiento"),
    )


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
    __table_args__ = (
        UniqueConstraint("lote_id", "nivel", name="uq_lote_nivel"),
        Index("ix_niveles_lote_lote_nivel", "lote_id", "nivel"),
    )


class ControlDiario(Base):
    __tablename__ = "controles_diarios"
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey("materiales_control.id"), nullable=False)
    lote_id = Column(Integer, ForeignKey("lotes.id"), nullable=False)
    nivel_lote_id = Column(Integer, ForeignKey("niveles_lote.id"), nullable=False)
    personal_id = Column(Integer, ForeignKey("personal.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    turno = Column(String(20))
    valor = Column(Float, nullable=False)
    zscore = Column(Float)
    resultado = Column(String(20))
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
        Index("ix_controles_fecha_resultado", "fecha", "resultado"),
        Index("ix_controles_material_fecha", "material_id", "fecha"),
        Index("ix_controles_nivel_lote_fecha", "nivel_lote_id", "fecha"),
        Index("ix_controles_personal", "personal_id"),
        Index("ix_controles_turno_fecha", "turno", "fecha"),
    )


class AccionCorrectiva(Base):
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
        Index("ix_mediciones_sesion", "sesion_id"),
    )


# ── Tabla de Índice de Sigma por analito ──────────────────────────────────────
class IndiceCalidad(Base):
    """Almacena el Error Total Permitido (TEa) y Sesgo% por analito para el cálculo de Sigma."""
    __tablename__ = "indices_calidad"
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey("materiales_control.id"), nullable=False, unique=True)
    tea = Column(Float, nullable=False)
    sesgo_porcentual = Column(Float, default=0.0)
    fuente_tea = Column(String(100))
    actualizado_en = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    material = relationship("MaterialControl")


# ── Calibraciones ─────────────────────────────────────────────────────────────
TIPOS_CALIBRACION = [
    "Calibración completa",
    "Calibración 2 puntos",
    "Verificación de calibración",
    "Calibración de urgencia",
    "Recalibración post-mantenimiento",
]
RESULTADOS_CALIBRACION = ["APROBADA", "RECHAZADA", "PENDIENTE VERIFICACIÓN"]


class Calibracion(Base):
    __tablename__ = "calibraciones"
    id = Column(Integer, primary_key=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False)
    personal_id = Column(Integer, ForeignKey("personal.id"))
    fecha = Column(Date, nullable=False)
    tipo = Column(String(100), nullable=False)
    lote_calibrador = Column(String(100))
    resultado = Column(String(50), default="APROBADA")
    observaciones = Column(Text)
    proxima_calibracion = Column(Date)
    registrado_en = Column(DateTime, default=datetime.now)
    equipo = relationship("Equipo")
    personal = relationship("Personal")
    __table_args__ = (
        Index("ix_calibraciones_equipo_fecha", "equipo_id", "fecha"),
    )


# ── Mantenimiento ─────────────────────────────────────────────────────────────
TIPOS_MANTENIMIENTO = [
    "Preventivo programado",
    "Correctivo",
    "Limpieza profunda",
    "Cambio de consumibles",
    "Verificación post-reparación",
    "Servicio técnico externo",
]
RESULTADOS_MANTENIMIENTO = ["COMPLETADO", "EN PROCESO", "PENDIENTE SERVICIO TÉCNICO"]


class Mantenimiento(Base):
    __tablename__ = "mantenimiento"
    id = Column(Integer, primary_key=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False)
    personal_id = Column(Integer, ForeignKey("personal.id"))
    fecha = Column(Date, nullable=False)
    tipo = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=False)
    resultado = Column(String(50), default="COMPLETADO")
    proxima_fecha = Column(Date)
    registrado_en = Column(DateTime, default=datetime.now)
    equipo = relationship("Equipo")
    personal = relationship("Personal")
    __table_args__ = (
        Index("ix_mantenimiento_equipo_fecha", "equipo_id", "fecha"),
    )
