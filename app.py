"""
Umbrales · Análisis de Narrativas Juveniles
===========================================

Aplicación Streamlit para análisis sistemático de textos producidos
por jóvenes en talleres educativos.

Metodología: clasificación léxica ponderada (NLP clásico, sin LLMs).
Reproducible · Trazable · Auditable

Para ejecutar:
    streamlit run app.py
"""

import io
import json
from datetime import datetime

import pandas as pd
import streamlit as st

from src.analyzer import (
    UMBRAL_CLASIFICACION,
    MAX_CATEGORIAS_POR_TEXTO,
    analizar_dataset,
    calcular_resumen_agregado,
    obtener_parametros_analisis,
)
from src.lexicon import CATEGORIAS
from src.reporter import (
    exportar_excel,
    exportar_json_auditoria,
    generar_log_auditoria,
)


# ──────────────────────────────────────────────────────────────────────────────
# Configuración de la página
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Umbrales · Análisis de Narrativas Juveniles",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Estilos — identidad visual Crear Vale la Pena
# Paleta: naranja #F0921E · violeta #7B4BAD · coral #E8566A
#         durazno #FBCBA8 · lila #C9A0DC · oscuro #3D3D3D
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Nunito', sans-serif;
        color: #3D3D3D;
    }

    /* Fondo general */
    .stApp { background-color: #FFF8F2; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #7B4BAD 0%, #5C3185 100%);
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stSlider > div > div > div {
        background: #C9A0DC;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.25);
    }

    /* ── Header principal ── */
    .cvlp-header {
        background: linear-gradient(135deg, #7B4BAD 0%, #5C3185 60%, #3D3D3D 100%);
        border-radius: 16px;
        padding: 32px 36px;
        margin-bottom: 24px;
        color: white;
    }
    .cvlp-header h1 {
        color: #F0921E !important;
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 8px 0;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .cvlp-header p {
        color: #F5E6FF;
        font-size: 1rem;
        margin: 0;
    }
    .cvlp-badge {
        display: inline-block;
        background: #F0921E;
        color: white;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        margin-top: 10px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    /* ── Títulos de sección ── */
    h2 {
        color: #F0921E !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 3px solid #FBCBA8;
        padding-bottom: 6px;
    }
    h3 {
        color: #7B4BAD !important;
        font-weight: 700 !important;
    }

    /* ── Botones primarios ── */
    .stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #E8566A, #C93B50) !important;
        color: white !important;
        border: none !important;
        border-radius: 30px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 10px 24px !important;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        box-shadow: 0 4px 12px rgba(232,86,106,0.35) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(232,86,106,0.45) !important;
    }

    /* ── Botones secundarios y descarga ── */
    .stButton > button:not([kind="primary"]),
    .stDownloadButton > button {
        background: white !important;
        color: #7B4BAD !important;
        border: 2px solid #7B4BAD !important;
        border-radius: 30px !important;
        font-weight: 700 !important;
        padding: 8px 20px !important;
        transition: background 0.15s ease !important;
    }
    .stButton > button:not([kind="primary"]):hover,
    .stDownloadButton > button:hover {
        background: #F5EEFF !important;
    }

    /* ── Info / alertas ── */
    [data-testid="stAlert"] {
        border-radius: 12px !important;
        border-left: 5px solid #F0921E !important;
        background: #FFF3E0 !important;
        color: #3D3D3D !important;
    }

    /* ── Métricas ── */
    [data-testid="stMetric"] {
        background: white;
        border-radius: 14px;
        padding: 16px !important;
        box-shadow: 0 2px 10px rgba(123,75,173,0.10);
        border-top: 4px solid #F0921E;
    }
    [data-testid="stMetricValue"] {
        color: #7B4BAD !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #3D3D3D !important;
        font-weight: 600 !important;
    }

    /* ── Tablas / DataFrames ── */
    [data-testid="stDataFrame"] {
        border-radius: 12px !important;
        overflow: hidden;
        border: 1px solid #E8D5F5 !important;
    }

    /* ── Expanders ── */
    [data-testid="stExpander"] {
        border: 1px solid #E8D5F5 !important;
        border-radius: 12px !important;
        background: white;
    }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {
        border: 2px dashed #C9A0DC !important;
        border-radius: 12px !important;
        background: #FDFAFF !important;
    }

    /* ── Selectbox / sliders ── */
    [data-testid="stSelectbox"] > div,
    [data-testid="stNumberInput"] > div {
        border-radius: 10px !important;
    }

    /* ── Cajas de metodología (sidebar) ── */
    .metodologia-box {
        background: rgba(255,255,255,0.15);
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 0.88em;
        color: #F5E6FF;
        line-height: 1.6;
    }

    /* ── Categorías en resultados ── */
    .categoria-protector { border-left: 4px solid #F0921E; }
    .categoria-estresor  { border-left: 4px solid #E8566A; }
    .categoria-neutro    { border-left: 4px solid #C9A0DC; }

    /* ── Footer ── */
    .cvlp-footer {
        margin-top: 48px;
        background: #3D3D3D;
        border-radius: 16px;
        padding: 20px 28px;
        text-align: center;
        color: #C9A0DC;
        font-size: 0.85em;
    }
    .cvlp-footer span {
        color: #F0921E;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎨 Umbrales")
    st.markdown("*Análisis de Narrativas Juveniles*")
    st.divider()

    st.markdown("### Parámetros")
    umbral = st.slider(
        "Umbral de clasificación",
        min_value=0.01,
        max_value=0.15,
        value=UMBRAL_CLASIFICACION,
        step=0.01,
        help=(
            "Score mínimo para asignar una categoría a un texto. "
            "Valores más bajos = más textos clasificados (mayor recall). "
            "Valores más altos = clasificaciones más estrictas (mayor precisión)."
        ),
    )
    max_cats = st.slider(
        "Máx. categorías por texto",
        min_value=1,
        max_value=5,
        value=MAX_CATEGORIAS_POR_TEXTO,
        help="Cuántas categorías temáticas puede tener asignadas un mismo texto.",
    )

    st.divider()
    st.markdown("""
    <div class="metodologia-box">
    <strong>Metodología</strong><br>
    Clasificación léxica ponderada.<br>
    Sin LLMs · Sin APIs externas.<br>
    100% reproducible y auditable.
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("<small>v1.1.0 · Fundación Crear Vale la Pena</small>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Encabezado principal
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="cvlp-header">
    <h1>Análisis de Narrativas Juveniles</h1>
    <p>
        Herramienta para el análisis sistemático de textos producidos por jóvenes
        en talleres educativos. Identifica patrones temáticos vinculados a
        <strong style="color:#FBCBA8">factores protectores</strong> y
        <strong style="color:#F4A0A8">estresores</strong> en la vida de los jóvenes.
    </p>
    <span class="cvlp-badge">Fundación Crear Vale la Pena · Talleres Umbrales</span>
</div>
""", unsafe_allow_html=True)

st.info(
    "Este sistema realiza *análisis sistemático de narrativas juveniles con "
    "herramientas de lenguaje*. No constituye diagnóstico clínico ni epidemiológico.",
    icon="ℹ️",
)

# ──────────────────────────────────────────────────────────────────────────────
# Paso 1: Carga del archivo
# ──────────────────────────────────────────────────────────────────────────────

st.header("1. Cargar datos")

col_upload, col_demo = st.columns([3, 1])

with col_upload:
    archivo = st.file_uploader(
        "Subí tu archivo CSV o Excel (.csv, .xlsx, .xls)",
        type=["csv", "xlsx", "xls"],
        help="El archivo debe tener al menos una columna con los textos a analizar.",
    )

    _plantilla_csv = "ID,Texto,Provincia,Localidad seleccionada\n"
    st.download_button(
        label="Descargar plantilla CSV",
        data=_plantilla_csv,
        file_name="plantilla_umbrales.csv",
        mime="text/csv",
        help="Plantilla con las columnas esperadas para cargar tus datos.",
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

# Procesar archivo subido
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

# ──────────────────────────────────────────────────────────────────────────────
# Paso 2: Configurar columnas
# ──────────────────────────────────────────────────────────────────────────────

if "df_cargado" in st.session_state:
    df = st.session_state["df_cargado"]

    st.header("2. Configurar columnas")

    with st.expander("Vista previa del dataset", expanded=True):
        st.dataframe(df.head(10), use_container_width=True)
        st.caption(f"Dimensiones: {df.shape[0]} filas × {df.shape[1]} columnas")

    col_conf1, col_conf2, col_conf3 = st.columns(3)

    with col_conf1:
        columna_texto = st.selectbox(
            "Columna con los textos *",
            options=list(df.columns),
            help="Columna que contiene los textos escritos por los jóvenes.",
        )

    with col_conf2:
        cols_opcionales = ["(ninguna)"] + list(df.columns)
        columna_id = st.selectbox(
            "Columna ID (opcional)",
            options=cols_opcionales,
            help="Columna identificadora de cada registro.",
        )
        columna_id = None if columna_id == "(ninguna)" else columna_id

    with col_conf3:
        columna_agrupacion = st.selectbox(
            "Agrupar resultados por (opcional)",
            options=cols_opcionales,
            help=(
                "Columna para desagregar resultados por región, taller, "
                "género u otra variable."
            ),
        )
        columna_agrupacion = None if columna_agrupacion == "(ninguna)" else columna_agrupacion

    # ──────────────────────────────────────────────────────────────────────────
    # Paso 3: Ejecutar análisis
    # ──────────────────────────────────────────────────────────────────────────

    st.header("3. Ejecutar análisis")

    if st.button("Analizar textos", type="primary", use_container_width=True):
        with st.spinner("Analizando textos..."):
            try:
                df_analizado = analizar_dataset(
                    df=df,
                    columna_texto=columna_texto,
                    columna_id=columna_id,
                    umbral=umbral,
                    max_categorias=max_cats,
                )
                resumen = calcular_resumen_agregado(df_analizado, columna_agrupacion)
                parametros = obtener_parametros_analisis(umbral, max_cats)
                log = generar_log_auditoria(
                    df_original=df,
                    df_analizado=df_analizado,
                    columna_texto=columna_texto,
                    columna_agrupacion=columna_agrupacion,
                    resumen=resumen,
                    parametros=parametros,
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

# ──────────────────────────────────────────────────────────────────────────────
# Paso 4: Resultados
# ──────────────────────────────────────────────────────────────────────────────

if "df_analizado" in st.session_state:
    df_analizado = st.session_state["df_analizado"]
    resumen = st.session_state["resumen"]
    log = st.session_state["log"]
    col_agrup = st.session_state.get("columna_agrupacion")

    st.header("4. Resultados")

    # ── Métricas globales ──────────────────────────────────────────────────
    st.subheader("Resumen global")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total textos", resumen["total_textos"])
    m2.metric("Clasificados", resumen["textos_clasificados"])
    m3.metric("Sin clasificar", resumen["textos_sin_clasificar"])
    m4.metric("Tasa clasificación", f"{resumen['tasa_clasificacion']}%")

    # ── Distribución por tipo ──────────────────────────────────────────────
    st.subheader("Distribución por tipo predominante")
    tipos_labels = {
        "factor_protector": "Factor protector",
        "estresor": "Estresor",
        "neutro": "Neutro",
        "sin_clasificar": "Sin clasificar",
    }
    tipos_colores = {
        "factor_protector": "#28a745",
        "estresor": "#dc3545",
        "neutro": "#6c757d",
        "sin_clasificar": "#adb5bd",
    }
    por_tipo = resumen.get("por_tipo", {})
    if por_tipo:
        df_tipos = pd.DataFrame([
            {"Tipo": tipos_labels.get(k, k), "Cantidad": v}
            for k, v in por_tipo.items()
        ]).sort_values("Cantidad", ascending=False)
        st.bar_chart(df_tipos.set_index("Tipo"), height=200)

    # ── Distribución por categoría ─────────────────────────────────────────
    st.subheader("Distribución por categoría temática")

    cats_data = []
    for cat_key, info in resumen["por_categoria"].items():
        if info["conteo"] > 0:
            cats_data.append({
                "Categoría": info["nombre"],
                "Tipo": info["tipo"],
                "Conteo": info["conteo"],
                "% del total": info["porcentaje"],
            })

    if cats_data:
        df_cats = (
            pd.DataFrame(cats_data)
            .sort_values("Conteo", ascending=False)
        )

        # Mostrar gráfico
        st.bar_chart(df_cats.set_index("Categoría")["Conteo"], height=280)

        # Tabla detallada
        tipo_iconos = {
            "factor_protector": "🟢 Factor protector",
            "estresor": "🔴 Estresor",
            "neutro": "⚫ Neutro",
        }
        df_cats["Tipo"] = df_cats["Tipo"].map(lambda x: tipo_iconos.get(x, x))
        st.dataframe(df_cats, use_container_width=True, hide_index=True)
    else:
        st.warning(
            "Ningún texto superó el umbral de clasificación. "
            "Considerá bajar el umbral en el panel lateral."
        )

    # ── Resultados por grupo ───────────────────────────────────────────────
    if col_agrup and "por_grupo" in resumen:
        st.subheader(f"Desglose por: {col_agrup}")
        grupos = list(resumen["por_grupo"].keys())
        grupo_sel = st.selectbox("Seleccionar grupo", grupos)

        if grupo_sel:
            datos_g = resumen["por_grupo"][grupo_sel]
            st.caption(f"Total textos en este grupo: {datos_g['total']}")

            cats_g = [
                {
                    "Categoría": v["nombre"],
                    "Conteo": v["conteo"],
                    "% dentro del grupo": v["porcentaje"],
                }
                for v in datos_g["por_categoria"].values()
                if v["conteo"] > 0
            ]
            if cats_g:
                df_g = pd.DataFrame(cats_g).sort_values("Conteo", ascending=False)
                st.bar_chart(df_g.set_index("Categoría")["Conteo"], height=220)
                st.dataframe(df_g, use_container_width=True, hide_index=True)

    # ── Explorador de textos individuales ─────────────────────────────────
    st.subheader("Explorador de textos individuales")
    st.caption(
        "Revisá texto por texto cómo fue clasificado y qué palabras activaron cada categoría."
    )

    # Filtros
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_tipo = st.multiselect(
            "Filtrar por tipo",
            options=["factor_protector", "estresor", "neutro", "sin_clasificar"],
            default=[],
            format_func=lambda x: tipos_labels.get(x, x),
        )
    with col_f2:
        filtro_clasificado = st.checkbox("Solo textos clasificados", value=False)

    df_vista = df_analizado.copy()
    if filtro_tipo:
        df_vista = df_vista[df_vista["tipo_predominante"].isin(filtro_tipo)]
    if filtro_clasificado:
        df_vista = df_vista[df_vista["clasificado"]]

    columnas_mostrar = ["texto_original", "categorias_nombres", "tipo_predominante", "longitud_tokens"]
    columnas_mostrar = [c for c in columnas_mostrar if c in df_vista.columns]

    if col_agrup and col_agrup in df_vista.columns:
        columnas_mostrar = [col_agrup] + columnas_mostrar

    st.dataframe(
        df_vista[columnas_mostrar].rename(columns={
            "texto_original": "Texto",
            "categorias_nombres": "Categorías asignadas",
            "tipo_predominante": "Tipo",
            "longitud_tokens": "Tokens",
        }),
        use_container_width=True,
        height=300,
    )
    st.caption(f"Mostrando {len(df_vista)} textos")

    # ── Explicación de una clasificación ──────────────────────────────────
    st.subheader("Explicar una clasificación")

    idx_max = len(df_analizado) - 1
    if idx_max >= 0:
        idx_sel = st.number_input(
            "Número de fila (0 = primera)",
            min_value=0, max_value=idx_max, value=0, step=1,
        )
        fila = df_analizado.iloc[int(idx_sel)]

        st.markdown(f"**Texto:** {fila['texto_original']}")
        st.markdown(f"**Preprocesado:** `{fila['texto_preprocesado']}`")
        st.markdown(f"**Tipo predominante:** {tipos_labels.get(fila['tipo_predominante'], fila['tipo_predominante'])}")

        cats_asignadas = [c for c in fila["categorias"].split("|") if c]
        if cats_asignadas:
            st.markdown("**Categorías asignadas y keywords que las activaron:**")
            for cat in cats_asignadas:
                if cat in CATEGORIAS:
                    score = fila.get(f"score_{cat}", 0)
                    kw_col = f"keywords_{cat}"
                    kws = fila.get(kw_col, "")
                    tipo_cat = CATEGORIAS[cat]["tipo"]
                    color = {"factor_protector": "🟢", "estresor": "🔴", "neutro": "⚫"}.get(tipo_cat, "")
                    st.markdown(
                        f"- {color} **{CATEGORIAS[cat]['nombre']}** "
                        f"(score: `{score:.4f}`) → keywords: `{kws if kws else 'n/a'}`"
                    )
        else:
            st.markdown("*Este texto no fue clasificado en ninguna categoría.*")

    # ──────────────────────────────────────────────────────────────────────────
    # Paso 5: Exportar
    # ──────────────────────────────────────────────────────────────────────────

    st.header("5. Exportar resultados")

    col_exp1, col_exp2 = st.columns(2)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    with col_exp1:
        st.markdown("**Reporte Excel completo**")
        st.caption(
            "Incluye: resultados detallados, resumen, "
            "desglose por grupo (si aplica) y hoja de auditoría."
        )
        excel_bytes = exportar_excel(
            df_analizado=df_analizado,
            resumen=resumen,
            log_auditoria=log,
            columna_agrupacion=col_agrup,
        )
        st.download_button(
            label="Descargar Excel",
            data=excel_bytes,
            file_name=f"umbrales_resultados_{timestamp_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_exp2:
        st.markdown("**Log de auditoría (JSON)**")
        st.caption(
            "Contiene hash del dataset, versiones, parámetros y "
            "resultados agregados. Apto para archivo institucional."
        )
        json_str = exportar_json_auditoria(log)
        st.download_button(
            label="Descargar JSON de auditoría",
            data=json_str.encode("utf-8"),
            file_name=f"umbrales_auditoria_{timestamp_str}.json",
            mime="application/json",
            use_container_width=True,
        )

    # ── Ver log de auditoría inline ────────────────────────────────────────
    with st.expander("Ver log de auditoría completo"):
        st.json(log)

# ──────────────────────────────────────────────────────────────────────────────
# Estado vacío
# ──────────────────────────────────────────────────────────────────────────────

else:
    st.markdown("---")
    st.markdown(
        "**Para comenzar:** subí un archivo CSV o Excel con los textos a analizar, "
        "o cargá el dataset de ejemplo desde el botón de arriba."
    )
    st.markdown("**Formato esperado:** el archivo debe tener una columna con los textos.")
    st.markdown("**Columnas opcionales:** región, taller, género, u otras variables de agrupación.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="cvlp-footer">
    © <span>Fundación Crear Vale la Pena</span> · Talleres Umbrales ·
    Herramienta de análisis de narrativas juveniles
</div>
""", unsafe_allow_html=True)
