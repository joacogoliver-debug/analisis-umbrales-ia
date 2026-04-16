"""
Umbrales · Análisis de Narrativas Juveniles
===========================================
Aplicación Streamlit con autenticación por roles (admin / usuario).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

from src.analyzer import (
    UMBRAL_CLASIFICACION,
    MAX_CATEGORIAS_POR_TEXTO,
    analizar_dataset,
    calcular_resumen_agregado,
    obtener_parametros_analisis,
)
from src.auth import verify_login, get_users, add_user, delete_user, change_password
from src.lexicon import CATEGORIAS
from src.reporter import exportar_excel, exportar_json_auditoria, generar_log_auditoria
from src.submissions import (
    PROVINCIAS,
    ESTADOS,
    save_submission,
    get_submissions,
    get_submissions_by_user,
    update_submission,
    get_submission_bytes,
    get_territories,
    is_territory_open,
    set_territory,
    delete_territory,
)

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Umbrales · Análisis de Narrativas Juveniles",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,400;0,600;0,700;0,800;0,900;1,700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Nunito', sans-serif;
        color: #2D2D2D;
    }
    .stApp { background-color: #F7F5FF; }

    /* ── Sidebar: blanco con borde violeta ── */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] > div:first-child {
        background: #FFFFFF !important;
        border-right: 3px solid #E8D5F5 !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] small { color: #3D3D3D !important; }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 { color: #7B4BAD !important; }
    section[data-testid="stSidebar"] hr { border-color: #E8D5F5 !important; }

    /* ── Header ── */
    .cvlp-header {
        background: linear-gradient(120deg, #7B4BAD 0%, #9B6BC8 50%, #F0921E 100%);
        border-radius: 20px; padding: 28px 36px; margin-bottom: 28px;
        display: flex; align-items: center; gap: 24px;
        box-shadow: 0 6px 24px rgba(123,75,173,0.20);
    }
    .cvlp-header-text h1 {
        color: #FFFFFF !important; font-size: 1.8rem; font-weight: 900;
        margin: 0 0 4px 0; letter-spacing: 0.5px; text-transform: uppercase;
    }
    .cvlp-header-text p { color: rgba(255,255,255,0.88); font-size: 0.95rem; margin: 0; }
    .cvlp-badge {
        display: inline-block; background: rgba(255,255,255,0.25);
        color: white; font-size: 0.68rem; font-weight: 800; padding: 3px 12px;
        border-radius: 20px; margin-top: 8px; text-transform: uppercase;
        letter-spacing: 0.8px; border: 1px solid rgba(255,255,255,0.4);
    }

    /* ── Login card ── */
    .login-card {
        background: white; border-radius: 24px; padding: 40px;
        box-shadow: 0 8px 32px rgba(123,75,173,0.12);
        border-top: 5px solid #F0921E;
    }

    /* ── Títulos de sección ── */
    h2 {
        color: #F0921E !important; font-weight: 900 !important;
        letter-spacing: 0.3px; margin-top: 8px !important;
    }
    h3 { color: #7B4BAD !important; font-weight: 700 !important; }

    /* ── Botones ── */
    .stButton > button[kind="primary"] {
        background: #E8566A !important; color: white !important;
        border: none !important; border-radius: 50px !important;
        font-weight: 800 !important; font-size: 0.9rem !important;
        padding: 10px 28px !important; letter-spacing: 0.5px;
        box-shadow: 0 4px 14px rgba(232,86,106,0.40) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #C93B50 !important;
        box-shadow: 0 6px 20px rgba(232,86,106,0.50) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:not([kind="primary"]),
    .stDownloadButton > button {
        background: white !important; color: #7B4BAD !important;
        border: 2px solid #C9A0DC !important; border-radius: 50px !important;
        font-weight: 700 !important; transition: all 0.2s ease !important;
    }
    .stButton > button:not([kind="primary"]):hover,
    .stDownloadButton > button:hover {
        background: #F5EEFF !important; border-color: #7B4BAD !important;
    }

    /* ── Métricas ── */
    [data-testid="stMetric"] {
        background: white; border-radius: 16px; padding: 20px !important;
        box-shadow: 0 2px 12px rgba(123,75,173,0.08);
        border-top: 4px solid #F0921E;
    }
    [data-testid="stMetricValue"] { color: #7B4BAD !important; font-weight: 900 !important; font-size: 2rem !important; }
    [data-testid="stMetricLabel"] { color: #666 !important; font-weight: 600 !important; font-size: 0.85rem !important; }

    /* ── Alertas ── */
    [data-testid="stAlert"] {
        border-radius: 14px !important; border-left: 5px solid #F0921E !important;
        background: #FFF8F0 !important;
    }

    /* ── Tablas ── */
    [data-testid="stDataFrame"] {
        border-radius: 14px !important; border: 1px solid #EDE0F7 !important;
        overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    /* ── Expanders ── */
    [data-testid="stExpander"] {
        border: 1px solid #EDE0F7 !important; border-radius: 14px !important;
        background: white; box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {
        border: 2px dashed #C9A0DC !important;
        border-radius: 16px !important; background: #FDFAFF !important;
    }

    /* ── Tabs ── */
    [data-testid="stTabs"] [role="tab"] {
        font-weight: 700 !important; color: #7B4BAD !important;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #F0921E !important; border-bottom-color: #F0921E !important;
    }

    /* ── Sidebar elementos especiales ── */
    .sidebar-user-card {
        background: linear-gradient(135deg, #7B4BAD, #9B6BC8);
        border-radius: 14px; padding: 14px 16px; color: white; margin-bottom: 8px;
    }
    .sidebar-user-card strong { font-size: 1rem; display: block; }
    .sidebar-user-card span { font-size: 0.8rem; opacity: 0.85; }
    .metodologia-box {
        background: #F5EEFF; border: 1px solid #C9A0DC;
        border-radius: 12px; padding: 12px 14px; font-size: 0.85em;
        color: #5C3185; line-height: 1.6;
    }

    /* ── Footer ── */
    .cvlp-footer {
        margin-top: 56px; padding: 20px 0 8px 0;
        text-align: center; color: #999; font-size: 0.82em;
        border-top: 1px solid #EDE0F7;
    }
    .cvlp-footer strong { color: #7B4BAD; }
</style>
""", unsafe_allow_html=True)

# ── LOGIN ──────────────────────────────────────────────────────────────────────

LOGO_PATH = Path("assets/logo.png")

def _render_header(subtitulo: str = "") -> None:
    """Renderiza el header principal con logo si existe."""
    col_logo, col_txt = st.columns([1, 5])
    with col_logo:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=110)
    with col_txt:
        st.markdown(f"""
        <div class="cvlp-header-text" style="padding: 4px 0;">
            <h1>Umbrales · Análisis de Narrativas Juveniles</h1>
            <p>{subtitulo}</p>
            <span class="cvlp-badge">Fundación Crear Vale la Pena · Talleres Umbrales</span>
        </div>""", unsafe_allow_html=True)
    st.markdown("")


def _show_login() -> None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Logo centrado en login
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=180)
        else:
            st.markdown("## 🎨 Crear Vale la Pena")

        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("### Umbrales — Iniciá sesión")
        st.markdown("*Análisis de Narrativas Juveniles*")
        st.markdown("")

        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="tu usuario")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Ingresar", type="primary", use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        user = verify_login(username, password)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            with col2:
                st.error("Usuario o contraseña incorrectos.")


if "user" not in st.session_state:
    _show_login()
    st.stop()

user = st.session_state["user"]
role = user["role"]

# ── SIDEBAR ────────────────────────────────────────────────────────────────────

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=140)
    else:
        st.markdown("## 🎨 Umbrales")
    st.markdown("*Análisis de Narrativas Juveniles*")
    st.divider()
    rol_label = "Administrador" if role == "admin" else "Usuario"
    st.markdown(
        f'<div class="sidebar-user-card"><strong>{user["nombre"]}</strong>'
        f'<span>{rol_label}</span></div>',
        unsafe_allow_html=True,
    )
    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.divider()

    if role == "admin":
        st.markdown("### Parámetros de análisis")
        umbral = st.slider(
            "Umbral de clasificación", min_value=0.01, max_value=0.15,
            value=UMBRAL_CLASIFICACION, step=0.01,
            help="Score mínimo para asignar una categoría."
        )
        max_cats = st.slider(
            "Máx. categorías por texto", min_value=1, max_value=5,
            value=MAX_CATEGORIAS_POR_TEXTO
        )
        st.divider()

    st.markdown("""
    <div class="metodologia-box">
    <strong>Metodología</strong><br>
    Clasificación léxica ponderada.<br>
    Sin LLMs · Sin APIs externas.<br>
    100% reproducible y auditable.
    </div>""", unsafe_allow_html=True)
    st.divider()
    st.markdown("<small>v1.2.0 · Fundación Crear Vale la Pena</small>", unsafe_allow_html=True)

# ── HEADER ─────────────────────────────────────────────────────────────────────

_render_header(
    subtitulo="Herramienta para el análisis sistemático de textos producidos por jóvenes en talleres educativos. "
              "Identifica patrones temáticos vinculados a factores protectores y estresores."
)

# ── HELPER: selectores de provincia/territorio ─────────────────────────────────

def _selector_territorio(key_prefix: str):
    """Retorna (provincia, localidad) seleccionados."""
    c1, c2 = st.columns(2)
    with c1:
        provincia = st.selectbox(
            "Provincia", options=PROVINCIAS, key=f"{key_prefix}_provincia",
            help="Seleccioná la provincia correspondiente al archivo."
        )
    with c2:
        localidad = st.text_input(
            "Localidad / Territorio", key=f"{key_prefix}_localidad",
            help="Escribí el nombre de la localidad o territorio."
        )
    return provincia, localidad


def _plantilla_csv(provincia: str, localidad: str) -> str:
    return (
        "ID,Texto,Provincia,Localidad seleccionada\n"
        f"1,Escribí el texto aquí,{provincia},{localidad}\n"
    )


# ══════════════════════════════════════════════════════════════════════════════
# ROL: USUARIO
# ══════════════════════════════════════════════════════════════════════════════

def _pagina_usuario() -> None:
    st.info(
        "Como usuario podés subir archivos con las frases de tu taller. "
        "El equipo de administración revisará y procesará tu envío.",
        icon="ℹ️",
    )

    st.header("Seleccionar territorio")
    provincia, localidad = _selector_territorio("usr")

    taller = st.text_input(
        "Nombre del taller (opcional)",
        help="Ej: Taller de escritura, Escuela Nº 42, etc."
    )

    # Verificar si el territorio está cerrado
    territorio_abierto = True
    if localidad:
        territorio_abierto = is_territory_open(provincia, localidad)
        if not territorio_abierto:
            st.warning(
                f"El territorio **{localidad}, {provincia}** está cerrado para nuevos envíos. "
                "Contactá al equipo de administración para más información.",
                icon="🔒",
            )

    st.header("Descargar plantilla")
    st.caption("Usá esta plantilla para preparar tu archivo antes de subirlo.")
    st.download_button(
        label="Descargar plantilla CSV",
        data=_plantilla_csv(provincia, localidad or "Tu localidad"),
        file_name="plantilla_umbrales.csv",
        mime="text/csv",
    )

    st.header("Subir archivo")
    archivo = st.file_uploader(
        "Seleccioná tu archivo CSV o Excel",
        type=["csv", "xlsx", "xls"],
        disabled=not territorio_abierto,
        help="El archivo debe tener una columna 'Texto' con las frases de los participantes.",
    )

    if archivo and territorio_abierto:
        if not localidad:
            st.warning("Completá el campo Localidad / Territorio antes de enviar.")
        else:
            if st.button("Enviar archivo", type="primary"):
                file_bytes = archivo.read()
                save_submission(
                    file_bytes=file_bytes,
                    filename=archivo.name,
                    provincia=provincia,
                    localidad=localidad,
                    taller=taller,
                    uploaded_by=user["username"],
                )
                st.success(
                    f"Archivo **{archivo.name}** enviado correctamente. "
                    "El equipo de administración lo revisará pronto."
                )
                st.balloons()

    # ── Mis envíos ────────────────────────────────────────────────────────────
    st.header("Mis envíos")
    mis_envios = get_submissions_by_user(user["username"])

    if not mis_envios:
        st.caption("Todavía no enviaste ningún archivo.")
    else:
        for envio in reversed(mis_envios):
            estado_label = ESTADOS.get(envio["estado"], envio["estado"])
            with st.expander(
                f"{estado_label}  ·  {envio['filename_original']}  ·  "
                f"{envio['provincia']} / {envio['localidad']}",
                expanded=False,
            ):
                st.markdown(f"**Fecha de envío:** {envio['uploaded_at'][:10]}")
                st.markdown(f"**Taller:** {envio.get('taller') or '—'}")
                st.markdown(f"**Estado:** {estado_label}")
                if envio.get("nota_admin"):
                    st.info(f"Nota del administrador: {envio['nota_admin']}")


# ══════════════════════════════════════════════════════════════════════════════
# ROL: ADMIN — TAB ANÁLISIS
# ══════════════════════════════════════════════════════════════════════════════

def _tab_analisis() -> None:
    st.info(
        "Este sistema realiza *análisis sistemático de narrativas juveniles con herramientas de lenguaje*. "
        "No constituye diagnóstico clínico ni epidemiológico.",
        icon="ℹ️",
    )

    # ── Paso 1: Cargar datos ──────────────────────────────────────────────────
    st.header("1. Cargar datos")

    col_upload, col_demo = st.columns([3, 1])

    with col_upload:
        st.markdown("**Territorio de este archivo**")
        provincia_t, localidad_t = _selector_territorio("adm")

        archivo = st.file_uploader(
            "Subí tu archivo CSV o Excel (.csv, .xlsx, .xls)",
            type=["csv", "xlsx", "xls"],
            help="El archivo debe tener al menos una columna con los textos a analizar.",
        )

        st.download_button(
            label="Descargar plantilla CSV",
            data=_plantilla_csv(provincia_t, localidad_t or "Tu localidad"),
            file_name="plantilla_umbrales.csv",
            mime="text/csv",
            help="Plantilla con las columnas esperadas.",
        )

    with col_demo:
        st.markdown("**¿No tenés datos?**")
        if st.button("Cargar dataset de ejemplo", use_container_width=True):
            try:
                df_demo = pd.read_csv("data/ejemplo_textos.csv")
                st.session_state["df_cargado"] = df_demo
                st.session_state["nombre_archivo"] = "ejemplo_textos.csv"
                st.success("Dataset de ejemplo cargado.")
            except FileNotFoundError:
                st.error("No se encontró el archivo de ejemplo.")

    if archivo is not None:
        try:
            if archivo.name.endswith(".csv"):
                df_cargado = pd.read_csv(archivo)
            else:
                df_cargado = pd.read_excel(archivo)
            st.session_state["df_cargado"] = df_cargado
            st.session_state["nombre_archivo"] = archivo.name
            st.success(f"Archivo cargado: **{archivo.name}** — {len(df_cargado)} filas.")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

    # ── Detección automática de columnas ─────────────────────────────────────
    if "df_cargado" not in st.session_state:
        st.markdown("---")
        st.markdown("**Para comenzar:** subí un archivo o cargá el dataset de ejemplo.")
        return

    df = st.session_state["df_cargado"]

    # Auto-detectar columnas de la plantilla
    cols = list(df.columns)
    columna_texto = next((c for c in cols if c.strip().lower() == "texto"), None)
    columna_id = next((c for c in cols if c.strip().lower() == "id"), None)
    columna_agrupacion = next(
        (c for c in cols if "localidad" in c.strip().lower() or "provincia" in c.strip().lower()),
        None
    )

    # Si no encuentra la columna Texto, pedir al usuario que la indique
    if columna_texto is None:
        st.warning("No se encontró una columna llamada **Texto**. Seleccionala manualmente:")
        columna_texto = st.selectbox("Columna con los textos", options=cols)

    # Vista previa compacta
    with st.expander(f"Vista previa — {df.shape[0]} filas · {df.shape[1]} columnas"):
        st.dataframe(df.head(8), use_container_width=True)

    # ── Ejecutar análisis ─────────────────────────────────────────────────────
    st.header("2. Ejecutar análisis")

    if st.button("Analizar textos", type="primary", use_container_width=True):
        with st.spinner("Analizando textos..."):
            try:
                df_analizado = analizar_dataset(
                    df=df, columna_texto=columna_texto,
                    columna_id=columna_id, umbral=umbral, max_categorias=max_cats,
                )
                resumen = calcular_resumen_agregado(df_analizado, columna_agrupacion)
                parametros = obtener_parametros_analisis(umbral, max_cats)
                log = generar_log_auditoria(
                    df_original=df, df_analizado=df_analizado,
                    columna_texto=columna_texto, columna_agrupacion=columna_agrupacion,
                    resumen=resumen, parametros=parametros,
                    nombre_archivo=st.session_state.get("nombre_archivo", ""),
                )
                st.session_state["df_analizado"] = df_analizado
                st.session_state["resumen"] = resumen
                st.session_state["log"] = log
                st.session_state["columna_agrupacion"] = columna_agrupacion
                st.success("Análisis completado.")
            except Exception as e:
                st.error(f"Error durante el análisis: {e}")
                raise

    # ── Paso 4: Resultados ────────────────────────────────────────────────────
    if "df_analizado" not in st.session_state:
        return

    df_analizado = st.session_state["df_analizado"]
    resumen = st.session_state["resumen"]
    log = st.session_state["log"]
    col_agrup = st.session_state.get("columna_agrupacion")

    tipos_labels = {
        "factor_protector": "Factor protector", "estresor": "Estresor",
        "neutro": "Neutro", "sin_clasificar": "Sin clasificar",
    }

    st.header("4. Resultados")
    st.subheader("Resumen global")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total textos", resumen["total_textos"])
    m2.metric("Clasificados", resumen["textos_clasificados"])
    m3.metric("Sin clasificar", resumen["textos_sin_clasificar"])
    m4.metric("Tasa clasificación", f"{resumen['tasa_clasificacion']}%")

    st.subheader("Distribución por tipo predominante")
    por_tipo = resumen.get("por_tipo", {})
    if por_tipo:
        df_tipos = pd.DataFrame([
            {"Tipo": tipos_labels.get(k, k), "Cantidad": v}
            for k, v in por_tipo.items()
        ]).sort_values("Cantidad", ascending=False)
        st.bar_chart(df_tipos.set_index("Tipo"), height=200)

    st.subheader("Distribución por categoría temática")
    cats_data = [
        {"Categoría": info["nombre"], "Tipo": info["tipo"],
         "Conteo": info["conteo"], "% del total": info["porcentaje"]}
        for cat_key, info in resumen["por_categoria"].items() if info["conteo"] > 0
    ]
    if cats_data:
        df_cats = pd.DataFrame(cats_data).sort_values("Conteo", ascending=False)
        st.bar_chart(df_cats.set_index("Categoría")["Conteo"], height=280)
        tipo_iconos = {
            "factor_protector": "🟢 Factor protector",
            "estresor": "🔴 Estresor", "neutro": "⚫ Neutro",
        }
        df_cats["Tipo"] = df_cats["Tipo"].map(lambda x: tipo_iconos.get(x, x))
        st.dataframe(df_cats, use_container_width=True, hide_index=True)
    else:
        st.warning("Ningún texto superó el umbral. Bajá el umbral en el panel lateral.")

    if col_agrup and "por_grupo" in resumen:
        st.subheader(f"Desglose por: {col_agrup}")
        grupo_sel = st.selectbox("Seleccionar grupo", list(resumen["por_grupo"].keys()))
        if grupo_sel:
            datos_g = resumen["por_grupo"][grupo_sel]
            st.caption(f"Total textos: {datos_g['total']}")
            cats_g = [
                {"Categoría": v["nombre"], "Conteo": v["conteo"], "% dentro del grupo": v["porcentaje"]}
                for v in datos_g["por_categoria"].values() if v["conteo"] > 0
            ]
            if cats_g:
                df_g = pd.DataFrame(cats_g).sort_values("Conteo", ascending=False)
                st.bar_chart(df_g.set_index("Categoría")["Conteo"], height=220)
                st.dataframe(df_g, use_container_width=True, hide_index=True)

    st.subheader("Explorador de textos individuales")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_tipo = st.multiselect(
            "Filtrar por tipo", options=list(tipos_labels.keys()),
            format_func=lambda x: tipos_labels.get(x, x),
        )
    with col_f2:
        filtro_clasificado = st.checkbox("Solo textos clasificados")

    df_vista = df_analizado.copy()
    if filtro_tipo:
        df_vista = df_vista[df_vista["tipo_predominante"].isin(filtro_tipo)]
    if filtro_clasificado:
        df_vista = df_vista[df_vista["clasificado"]]

    cols_mostrar = ["texto_original", "categorias_nombres", "tipo_predominante", "longitud_tokens"]
    cols_mostrar = [c for c in cols_mostrar if c in df_vista.columns]
    if col_agrup and col_agrup in df_vista.columns:
        cols_mostrar = [col_agrup] + cols_mostrar

    st.dataframe(
        df_vista[cols_mostrar].rename(columns={
            "texto_original": "Texto", "categorias_nombres": "Categorías",
            "tipo_predominante": "Tipo", "longitud_tokens": "Tokens",
        }),
        use_container_width=True, height=300,
    )
    st.caption(f"Mostrando {len(df_vista)} textos")

    st.subheader("Explicar una clasificación")
    idx_max = len(df_analizado) - 1
    if idx_max >= 0:
        idx_sel = st.number_input("Número de fila (0 = primera)", min_value=0, max_value=idx_max, value=0, step=1)
        fila = df_analizado.iloc[int(idx_sel)]
        st.markdown(f"**Texto:** {fila['texto_original']}")
        st.markdown(f"**Tipo predominante:** {tipos_labels.get(fila['tipo_predominante'], fila['tipo_predominante'])}")
        cats_asignadas = [c for c in fila["categorias"].split("|") if c]
        if cats_asignadas:
            st.markdown("**Categorías asignadas:**")
            for cat in cats_asignadas:
                if cat in CATEGORIAS:
                    score = fila.get(f"score_{cat}", 0)
                    kws = fila.get(f"keywords_{cat}", "")
                    tipo_cat = CATEGORIAS[cat]["tipo"]
                    icono = {"factor_protector": "🟢", "estresor": "🔴", "neutro": "⚫"}.get(tipo_cat, "")
                    st.markdown(f"- {icono} **{CATEGORIAS[cat]['nombre']}** (score: `{score:.4f}`) → `{kws or 'n/a'}`")
        else:
            st.markdown("*No clasificado en ninguna categoría.*")

    # ── Paso 5: Exportar ──────────────────────────────────────────────────────
    st.header("5. Exportar resultados")
    col_exp1, col_exp2 = st.columns(2)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    with col_exp1:
        st.markdown("**Reporte Excel completo**")
        excel_bytes = exportar_excel(
            df_analizado=df_analizado, resumen=resumen,
            log_auditoria=log, columna_agrupacion=col_agrup,
        )
        st.download_button(
            "Descargar Excel", data=excel_bytes,
            file_name=f"umbrales_resultados_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_exp2:
        st.markdown("**Log de auditoría (JSON)**")
        json_str = exportar_json_auditoria(log)
        st.download_button(
            "Descargar JSON de auditoría", data=json_str.encode("utf-8"),
            file_name=f"umbrales_auditoria_{ts}.json",
            mime="application/json", use_container_width=True,
        )

    with st.expander("Ver log de auditoría completo"):
        st.json(log)


# ══════════════════════════════════════════════════════════════════════════════
# ROL: ADMIN — TAB ENVÍOS
# ══════════════════════════════════════════════════════════════════════════════

def _tab_envios() -> None:
    todos = get_submissions()

    if not todos:
        st.info("No hay envíos todavía.")
        return

    # Métricas
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total envíos", len(todos))
    m2.metric("Pendientes", sum(1 for s in todos if s["estado"] == "pendiente"))
    m3.metric("Aprobados",  sum(1 for s in todos if s["estado"] == "aprobado"))
    m4.metric("Rechazados", sum(1 for s in todos if s["estado"] == "rechazado"))

    # Filtros
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_estado = st.multiselect(
            "Filtrar por estado", options=list(ESTADOS.keys()),
            format_func=lambda x: ESTADOS[x],
        )
    with col_f2:
        provincias_presentes = sorted({s["provincia"] for s in todos})
        filtro_prov = st.selectbox("Filtrar por provincia", ["Todas"] + provincias_presentes)

    envios = todos
    if filtro_estado:
        envios = [s for s in envios if s["estado"] in filtro_estado]
    if filtro_prov != "Todas":
        envios = [s for s in envios if s["provincia"] == filtro_prov]

    st.markdown(f"**{len(envios)} envíos** encontrados")

    for envio in reversed(envios):
        estado_label = ESTADOS.get(envio["estado"], envio["estado"])
        titulo = (
            f"{estado_label}  ·  {envio['filename_original']}  ·  "
            f"{envio['provincia']} / {envio['localidad']}  ·  "
            f"por {envio['uploaded_by']}  ·  {envio['uploaded_at'][:10]}"
        )
        with st.expander(titulo):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Taller:** {envio.get('taller') or '—'}")
                st.markdown(f"**Provincia:** {envio['provincia']}")
                st.markdown(f"**Localidad:** {envio['localidad']}")
                st.markdown(f"**Subido por:** {envio['uploaded_by']}")
                st.markdown(f"**Fecha:** {envio['uploaded_at'][:16].replace('T', ' ')}")

                file_bytes = get_submission_bytes(envio["filename_stored"])
                if file_bytes:
                    st.download_button(
                        "Descargar archivo",
                        data=file_bytes,
                        file_name=envio["filename_original"],
                        key=f"dl_{envio['id']}",
                    )
                    if st.button("Cargar para análisis", key=f"load_{envio['id']}"):
                        import io
                        name = envio["filename_original"]
                        if name.endswith(".csv"):
                            df_loaded = pd.read_csv(io.BytesIO(file_bytes))
                        else:
                            df_loaded = pd.read_excel(io.BytesIO(file_bytes))
                        st.session_state["df_cargado"] = df_loaded
                        st.session_state["nombre_archivo"] = name
                        st.success("Archivo cargado. Andá a la pestaña 📊 Análisis.")

            with col_b:
                nuevo_estado = st.selectbox(
                    "Estado", options=list(ESTADOS.keys()),
                    format_func=lambda x: ESTADOS[x],
                    index=list(ESTADOS.keys()).index(envio["estado"]),
                    key=f"est_{envio['id']}",
                )
                nota = st.text_area(
                    "Nota para el usuario", value=envio.get("nota_admin", ""),
                    key=f"nota_{envio['id']}", height=80,
                )
                if st.button("Guardar cambios", key=f"save_{envio['id']}", type="primary"):
                    update_submission(envio["id"], nuevo_estado, nota)
                    st.success("Estado actualizado.")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ROL: ADMIN — TAB TERRITORIOS
# ══════════════════════════════════════════════════════════════════════════════

def _tab_territorios() -> None:
    st.subheader("Agregar / actualizar territorio")
    with st.form("form_territorio"):
        col1, col2 = st.columns(2)
        with col1:
            prov_new = st.selectbox("Provincia", PROVINCIAS, key="t_prov")
        with col2:
            loc_new = st.text_input("Localidad / Territorio", key="t_loc")
        abierto_new = st.toggle("Territorio abierto para envíos", value=True)
        nota_new = st.text_input("Nota (opcional)")
        submitted = st.form_submit_button("Guardar territorio", type="primary")

    if submitted:
        if not loc_new:
            st.warning("Completá la localidad.")
        else:
            set_territory(prov_new, loc_new, abierto_new, nota_new)
            st.success(f"Territorio **{loc_new}, {prov_new}** guardado.")
            st.rerun()

    st.subheader("Territorios registrados")
    territorios = get_territories()

    if not territorios:
        st.caption("No hay territorios registrados todavía.")
        return

    for key, t in territorios.items():
        estado_t = "🟢 Abierto" if t["abierto"] else "🔴 Cerrado"
        with st.expander(f"{estado_t}  ·  {t['localidad']}, {t['provincia']}"):
            st.markdown(f"**Nota:** {t.get('nota') or '—'}")
            st.markdown(f"**Última actualización:** {t.get('updated_at', '—')[:16].replace('T', ' ')}")
            col_x, col_y = st.columns(2)
            with col_x:
                nuevo_estado_t = st.toggle(
                    "Abierto", value=t["abierto"], key=f"tog_{key}"
                )
                if st.button("Actualizar estado", key=f"upd_{key}"):
                    set_territory(t["provincia"], t["localidad"], nuevo_estado_t, t.get("nota", ""))
                    st.rerun()
            with col_y:
                if st.button("Eliminar territorio", key=f"del_{key}"):
                    delete_territory(t["provincia"], t["localidad"])
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ROL: ADMIN — TAB USUARIOS
# ══════════════════════════════════════════════════════════════════════════════

def _tab_usuarios() -> None:
    st.subheader("Crear usuario")
    with st.form("form_usuario"):
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("Nombre de usuario")
            new_nombre = st.text_input("Nombre completo")
        with col2:
            new_password = st.text_input("Contraseña inicial", type="password")
            new_role = st.selectbox("Rol", options=["usuario", "admin"],
                                    format_func=lambda x: "Administrador" if x == "admin" else "Usuario")
        submitted_u = st.form_submit_button("Crear usuario", type="primary")

    if submitted_u:
        if not new_username or not new_password or not new_nombre:
            st.warning("Completá todos los campos.")
        else:
            usuarios_actuales = get_users()
            if new_username in usuarios_actuales:
                st.error("Ya existe un usuario con ese nombre.")
            else:
                add_user(new_username, new_password, new_role, new_nombre)
                st.success(f"Usuario **{new_username}** creado.")
                st.rerun()

    st.subheader("Usuarios registrados")
    usuarios = get_users()

    for uname, udata in usuarios.items():
        rol_label = "👑 Administrador" if udata["role"] == "admin" else "👤 Usuario"
        with st.expander(f"{rol_label}  ·  {uname}  ·  {udata['nombre']}"):
            col_a, col_b = st.columns(2)
            with col_a:
                if uname != user["username"]:
                    if st.button("Eliminar usuario", key=f"del_u_{uname}"):
                        delete_user(uname)
                        st.success(f"Usuario {uname} eliminado.")
                        st.rerun()
                else:
                    st.caption("*(tu cuenta)*")
            with col_b:
                with st.form(f"pw_{uname}"):
                    nueva_pw = st.text_input("Nueva contraseña", type="password", key=f"pw_input_{uname}")
                    if st.form_submit_button("Cambiar contraseña"):
                        if nueva_pw:
                            change_password(uname, nueva_pw)
                            st.success("Contraseña actualizada.")
                        else:
                            st.warning("Escribí una contraseña.")


# ══════════════════════════════════════════════════════════════════════════════
# ROUTING PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

if role == "admin":
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Análisis", "📁 Envíos", "🗺️ Territorios", "👥 Usuarios"])
    with tab1:
        _tab_analisis()
    with tab2:
        _tab_envios()
    with tab3:
        _tab_territorios()
    with tab4:
        _tab_usuarios()
else:
    _pagina_usuario()

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="cvlp-footer">
    © <span>Fundación Crear Vale la Pena</span> · Talleres Umbrales ·
    Herramienta de análisis de narrativas juveniles
</div>
""", unsafe_allow_html=True)
