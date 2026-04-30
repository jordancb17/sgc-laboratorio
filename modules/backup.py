"""
Sistema de respaldos automáticos de la base de datos.

Los respaldos se guardan con timestamp en una carpeta configurable.
Apuntando esa carpeta a Google Drive o cualquier nube, los respaldos
quedan sincronizados indefinidamente (sin límite de 30 días).
"""

import shutil
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent.parent / "data" / "lab_qms.db"
_DEFAULT_BACKUP_DIR = Path(__file__).parent.parent / "backups"


def _get_backup_dir() -> Path:
    """Devuelve la carpeta de respaldos configurada (o la predeterminada)."""
    try:
        ruta = st.secrets["backup"].get("directorio", "")
        if ruta:
            p = Path(ruta)
            p.mkdir(parents=True, exist_ok=True)
            return p
    except Exception:
        pass
    _DEFAULT_BACKUP_DIR.mkdir(exist_ok=True)
    return _DEFAULT_BACKUP_DIR


def crear_backup(directorio: Path | None = None) -> Path:
    """Crea un respaldo con timestamp y retorna la ruta del archivo."""
    dest = directorio or _get_backup_dir()
    dest.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = dest / f"lab_qms_{ts}.db"
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def listar_backups(directorio: Path | None = None) -> list[Path]:
    """Lista todos los respaldos disponibles, más reciente primero."""
    d = directorio or _get_backup_dir()
    if not d.exists():
        return []
    return sorted(d.glob("lab_qms_*.db"), reverse=True)


def restaurar_backup(backup_path: Path) -> bool:
    """Restaura la BD desde un respaldo. Crea un respaldo previo de seguridad."""
    if not backup_path.exists():
        return False
    # Salvar la BD actual antes de restaurar
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    shutil.copy2(DB_PATH, _get_backup_dir() / f"pre_restore_{ts}.db")
    shutil.copy2(backup_path, DB_PATH)
    return True


def eliminar_backup(backup_path: Path) -> bool:
    try:
        backup_path.unlink()
        return True
    except Exception:
        return False


def limpiar_backups_antiguos(dias: int = 365, directorio: Path | None = None) -> int:
    """Elimina respaldos más antiguos que `dias` días. Retorna cantidad eliminada."""
    limite = datetime.now() - timedelta(days=dias)
    eliminados = 0
    for b in listar_backups(directorio):
        try:
            ts_str = b.stem.replace("lab_qms_", "").replace("pre_restore_", "")
            ts = datetime.strptime(ts_str, "%Y-%m-%d_%H-%M-%S")
            if ts < limite:
                b.unlink()
                eliminados += 1
        except Exception:
            pass
    return eliminados


def auto_backup() -> bool:
    """
    Crea un respaldo automático si han pasado más de 24 h desde el último.
    Retorna True si se creó un nuevo respaldo.
    """
    try:
        cfg = st.secrets.get("backup", {})
        if not cfg.get("auto_backup", True):
            return False
    except Exception:
        pass

    backups = listar_backups()
    if not backups:
        crear_backup()
        return True

    ultimo = backups[0]
    try:
        ts_str = ultimo.stem.replace("lab_qms_", "")
        ts = datetime.strptime(ts_str, "%Y-%m-%d_%H-%M-%S")
        if (datetime.now() - ts).total_seconds() >= 86400:
            crear_backup()
            return True
    except Exception:
        crear_backup()
        return True
    return False


def tamaño_total_mb(directorio: Path | None = None) -> float:
    return sum(b.stat().st_size for b in listar_backups(directorio)) / (1024 * 1024)


def info_backup(b: Path) -> dict:
    """Retorna metadatos de un archivo de respaldo."""
    try:
        ts = datetime.strptime(b.stem.replace("lab_qms_", ""), "%Y-%m-%d_%H-%M-%S")
        hace = datetime.now() - ts
        if hace.days > 0:
            edad = f"hace {hace.days} día(s)"
        elif hace.seconds // 3600 > 0:
            edad = f"hace {hace.seconds // 3600} hora(s)"
        else:
            edad = f"hace {hace.seconds // 60} minuto(s)"
    except Exception:
        ts = datetime.fromtimestamp(b.stat().st_mtime)
        edad = "—"
    return {
        "archivo": b.name,
        "fecha": ts.strftime("%Y-%m-%d %H:%M:%S"),
        "edad": edad,
        "tamaño_mb": round(b.stat().st_size / (1024 * 1024), 2),
        "ruta": str(b),
    }
