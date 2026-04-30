"""
Página de Administración del Sistema:
  - Gestión de respaldos (crear, listar, restaurar, Google Drive)
  - Configuración y prueba de alertas por email
  - Gestión de usuarios/contraseñas
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import date

from database.database import init_db
from modules.page_utils import setup_page, page_header
from modules import backup as bk
from modules.email_alerts import probar_conexion

st.set_page_config(page_title="Administración", page_icon="🛡️", layout="wide")
init_db()
setup_page()


def main():
    page_header(
        icon="🛡️",
        title="Administración del Sistema",
        subtitle="Respaldos, alertas por email, usuarios y configuración general del sistema",
        badge="Acceso Restringido",
    )

    tab_backup, tab_email, tab_usuarios = st.tabs([
        "💾 Respaldos y Almacenamiento", "📧 Alertas por Email", "🔑 Usuarios y Contraseñas"
    ])

    with tab_backup:
        _tab_backup()
    with tab_email:
        _tab_email()
    with tab_usuarios:
        _tab_usuarios()


# ─── RESPALDOS ────────────────────────────────────────────────────────────────

def _tab_backup():
    st.subheader("💾 Gestión de Respaldos")

    # Info de ruta actual
    dir_actual = bk._get_backup_dir()
    col1, col2 = st.columns([2, 1])
    col1.info(f"**Carpeta de respaldos actual:** `{dir_actual}`")

    st.markdown("""
    ### 🌐 Conectar con Google Drive (respaldo en la nube)

    **Pasos para respaldo ilimitado en Google Drive:**

    1. Descarga e instala **[Google Drive para escritorio](https://www.google.com/drive/download/)**
    2. Inicia sesión — se creará una carpeta en tu PC (ej: `G:\\Mi unidad\\`)
    3. Crea una carpeta para los respaldos, por ejemplo:
       `G:\\Mi unidad\\SGC_Backups\\`
    4. En el archivo `.streamlit/secrets.toml` agrega:

    ```toml
    [backup]
    directorio = "G:/Mi unidad/SGC_Backups"
    auto_backup = true
    ```

    5. Reinicia la aplicación — todos los respaldos se guardarán en Google Drive automáticamente.

    > ✅ **Sin límite de días** — los archivos se acumulan indefinidamente en tu Google Drive.
    > Google Drive gratuito incluye 15 GB (suficiente para años de respaldos).
    """)

    st.markdown("---")

    # Crear respaldo manual
    col1, col2, col3 = st.columns([1, 1, 2])
    if col1.button("📦 Crear Respaldo Ahora", type="primary", use_container_width=True):
        try:
            ruta = bk.crear_backup()
            st.success(f"✅ Respaldo creado: `{ruta.name}`")
            st.rerun()
        except Exception as e:
            st.error(f"Error al crear respaldo: {e}")

    # Limpiar respaldos antiguos
    dias_retener = col2.number_input("Retener últimos N días", min_value=7, value=365, step=30)
    if col2.button("🗑️ Limpiar antiguos", use_container_width=True):
        eliminados = bk.limpiar_backups_antiguos(int(dias_retener))
        st.success(f"Se eliminaron {eliminados} respaldo(s) antiguos.")
        st.rerun()

    st.markdown("---")

    # Lista de respaldos
    backups = bk.listar_backups()
    total_mb = bk.tamaño_total_mb()

    st.subheader(f"Respaldos disponibles ({len(backups)} archivos · {total_mb:.1f} MB total)")

    if not backups:
        st.info("No hay respaldos. Cree uno con el botón de arriba.")
        return

    filas = [bk.info_backup(b) for b in backups]
    df = pd.DataFrame(filas)[["fecha", "edad", "tamaño_mb", "archivo"]]
    df.columns = ["Fecha", "Antigüedad", "Tamaño (MB)", "Archivo"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("⚠️ Restaurar Respaldo")
    st.warning("Restaurar reemplazará la base de datos actual. Se creará un respaldo de seguridad automático antes de restaurar.")

    backup_opts = {b.name: b for b in backups}
    sel_backup = st.selectbox("Seleccione el respaldo a restaurar", list(backup_opts.keys()))
    if st.button("🔄 Restaurar Respaldo Seleccionado", type="secondary"):
        ok = bk.restaurar_backup(backup_opts[sel_backup])
        if ok:
            st.success("✅ Respaldo restaurado. Reinicie la aplicación para ver los cambios.")
        else:
            st.error("Error al restaurar. El archivo no existe.")


# ─── EMAIL ────────────────────────────────────────────────────────────────────

def _tab_email():
    st.subheader("📧 Configuración de Alertas por Email")

    st.markdown("""
    Las alertas se envían automáticamente cuando:
    - 🛑 Un control es **RECHAZADO** (cualquier regla de Westgard)
    - 📦 Un lote está por **vencer** (configurable)

    Edite el archivo `.streamlit/secrets.toml` con la siguiente sección:

    ```toml
    [email]
    habilitado    = true
    smtp_host     = "smtp.gmail.com"
    smtp_port     = 465
    remitente     = "sgc.lab@gmail.com"
    password      = "xxxx xxxx xxxx xxxx"
    destinatarios = "jefe@lab.com, calidad@lab.com"
    ```

    ### Cómo obtener la contraseña de aplicación de Gmail:
    1. Abre **myaccount.google.com**
    2. Seguridad → Verificación en 2 pasos (debe estar activa)
    3. Contraseñas de aplicación → Selecciona "Correo" y "Windows"
    4. Copia la contraseña de 16 caracteres generada
    """)

    st.markdown("---")

    # Estado actual
    try:
        cfg = dict(st.secrets["email"])
        habilitado = cfg.get("habilitado", False)
        remitente  = cfg.get("remitente", "—")
        dest       = cfg.get("destinatarios", "—")
        st.markdown(f"""
        **Estado actual:**
        - Habilitado: {'✅ Sí' if habilitado else '❌ No'}
        - Remitente: `{remitente}`
        - Destinatarios: `{dest}`
        """)
        if habilitado and st.button("📤 Enviar email de prueba", type="primary"):
            ok, msg = probar_conexion()
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")
    except Exception:
        st.info("No hay configuración de email en secrets.toml.")


# ─── USUARIOS ─────────────────────────────────────────────────────────────────

def _tab_usuarios():
    st.subheader("🔑 Gestión de Usuarios y Contraseñas")

    st.markdown("""
    Los usuarios se definen en el archivo `.streamlit/secrets.toml`:

    ```toml
    [credentials]
    admin        = "MiContraseña"
    tecnico1     = "OtraClave"
    supervisor   = "Clave2024!"
    ```

    **Para cambiar una contraseña:** edite el archivo y reinicie la app.
    **Para agregar un usuario:** agregue una línea con `nombre = "contraseña"`.
    **Para desactivar un usuario:** elimine su línea.
    """)

    secrets_path = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
    st.markdown(f"**Ruta del archivo:** `{secrets_path}`")

    if st.button("📂 Abrir secrets.toml en el Explorador"):
        import subprocess
        subprocess.Popen(f'explorer /select,"{secrets_path}"')

    st.markdown("---")

    # Mostrar usuarios actuales (sin contraseñas)
    try:
        usuarios = list(st.secrets["credentials"].keys())
        st.markdown("**Usuarios registrados actualmente:**")
        for u in usuarios:
            st.markdown(f"- 👤 `{u}`")
    except Exception:
        st.info("No se pudo leer la lista de usuarios.")

    st.markdown("---")
    st.markdown("""
    ### 🔐 Buenas prácticas de seguridad
    - Use contraseñas de al menos **8 caracteres** con letras, números y símbolos
    - **No comparta** el archivo `secrets.toml` ni lo suba a internet
    - Cambie las contraseñas cada **6 meses**
    - El archivo `secrets.toml` **no** es accesible desde la web — solo desde el servidor
    """)


if __name__ == "__main__":
    main()
