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
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Estilos
# ──────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .metric-card {
        background: white;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        text-align: center;
    }
    .categoria-protector { border-left: 4px solid #28a745; }
    .categoria-estresor  { border-left: 4px solid #dc3545; }
    .categoria-neutro    { border-left: 4px solid #6c757d; }
    .metodologia-box {
        background: #e8f4f8;
        border: 1px solid #bee5eb;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 0.9em;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Umbrales")
    st.caption("Análisis de Narrativas Juveniles")
    st.divider()

    st.subheader("Parámetros del análisis")
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
    st.caption("v1.0.0 · Talleres Umbrales")

# ──────────────────────────────────────────────────────────────────────────────
# Encabezado principal
# ──────────────────────────────────────────────────────────────────────────────

st.title("Análisis de Narrativas Juveniles")
st.markdown(
    "Herramienta para el análisis sistemático de textos producidos por jóvenes "
    "en talleres educativos. Identifica patrones temáticos vinculados a "
    "**factores protectores** y **estresores** en la vida de los jóvenes."
)
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
