"""
Módulo de generación de reportes y auditoría.

Genera:
1. Reporte Excel con resultados detallados + hoja de resumen + hoja de auditoría
2. Log de auditoría en JSON (para trazabilidad institucional)
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from io import BytesIO
from typing import Dict, Optional

import pandas as pd

from src.analyzer import VERSION_ANALIZADOR, obtener_parametros_analisis
from src.lexicon import CATEGORIAS, VERSION_LEXICO


def _hash_dataset(df: pd.DataFrame, columna_texto: str) -> str:
    """
    Calcula SHA-256 del contenido de la columna de textos.
    Permite verificar que el dataset no fue alterado entre ejecuciones.
    """
    contenido = "|".join(str(v) for v in df[columna_texto].fillna("").tolist())
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()


def generar_log_auditoria(
    df_original: pd.DataFrame,
    df_analizado: pd.DataFrame,
    columna_texto: str,
    columna_agrupacion: Optional[str],
    resumen: Dict,
    parametros: Dict,
    nombre_archivo: str = "",
) -> Dict:
    """
    Genera el log completo de auditoría de una ejecución.

    El log contiene toda la información necesaria para reproducir
    y verificar los resultados.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    log = {
        "meta": {
            "timestamp_utc": timestamp,
            "nombre_herramienta": "Umbrales · Análisis de Narrativas Juveniles",
            "version_analizador": VERSION_ANALIZADOR,
            "version_lexico": VERSION_LEXICO,
            "nota_metodologica": (
                "Este sistema realiza análisis sistemático de narrativas juveniles "
                "con herramientas de lenguaje (NLP clásico). No constituye diagnóstico "
                "clínico ni epidemiológico."
            ),
        },
        "dataset": {
            "nombre_archivo": nombre_archivo,
            "total_filas": len(df_original),
            "columna_texto": columna_texto,
            "columna_agrupacion": columna_agrupacion,
            "columnas_disponibles": list(df_original.columns),
            "hash_sha256_textos": _hash_dataset(df_original, columna_texto),
        },
        "parametros": parametros,
        "resultados_globales": {
            "total_textos": resumen["total_textos"],
            "clasificados": resumen["textos_clasificados"],
            "sin_clasificar": resumen["textos_sin_clasificar"],
            "tasa_clasificacion_pct": resumen["tasa_clasificacion"],
            "distribucion_tipos": resumen["por_tipo"],
        },
        "distribucion_categorias": {
            cat_key: {
                "nombre": info["nombre"],
                "tipo": info["tipo"],
                "conteo": resumen["por_categoria"][cat_key]["conteo"],
                "porcentaje": resumen["por_categoria"][cat_key]["porcentaje"],
            }
            for cat_key, info in CATEGORIAS.items()
        },
    }

    if "por_grupo" in resumen:
        log["distribucion_por_grupo"] = resumen["por_grupo"]

    return log


def exportar_excel(
    df_analizado: pd.DataFrame,
    resumen: Dict,
    log_auditoria: Dict,
    columna_agrupacion: Optional[str] = None,
) -> bytes:
    """
    Genera un archivo Excel con múltiples hojas:
    - 'Resultados': datos completos texto por texto
    - 'Resumen': estadísticas agregadas
    - 'Por Región' (si hay agrupación): desglose por grupo
    - 'Auditoría': parámetros y metadatos de la ejecución

    Returns:
        bytes del archivo Excel listo para descarga
    """
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        # ── Hoja 1: Resultados ─────────────────────────────────────────────
        columnas_resultado = [
            col for col in df_analizado.columns
            if not col.startswith("score_") and not col.startswith("keywords_")
        ]
        columnas_scores = [col for col in df_analizado.columns if col.startswith("score_")]
        columnas_kw = [col for col in df_analizado.columns if col.startswith("keywords_")]

        df_resultado = df_analizado[columnas_resultado + columnas_scores + columnas_kw].copy()

        # Renombrar columnas de score para legibilidad
        rename_scores = {
            f"score_{k}": f"Score: {CATEGORIAS[k]['nombre']}"
            for k in CATEGORIAS if f"score_{k}" in df_resultado.columns
        }
        rename_kw = {
            f"keywords_{k}": f"Keywords: {CATEGORIAS[k]['nombre']}"
            for k in CATEGORIAS if f"keywords_{k}" in df_resultado.columns
        }
        df_resultado = df_resultado.rename(columns={**rename_scores, **rename_kw})
        df_resultado.to_excel(writer, sheet_name="Resultados", index=False)

        # ── Hoja 2: Resumen ────────────────────────────────────────────────
        filas_resumen = []
        filas_resumen.append(["RESUMEN GENERAL", ""])
        filas_resumen.append(["Total de textos", resumen["total_textos"]])
        filas_resumen.append(["Textos clasificados", resumen["textos_clasificados"]])
        filas_resumen.append(["Textos sin clasificar", resumen["textos_sin_clasificar"]])
        filas_resumen.append(["Tasa de clasificación (%)", resumen["tasa_clasificacion"]])
        filas_resumen.append(["", ""])
        filas_resumen.append(["DISTRIBUCIÓN POR TIPO PREDOMINANTE", ""])
        for tipo, conteo in resumen.get("por_tipo", {}).items():
            filas_resumen.append([tipo, conteo])
        filas_resumen.append(["", ""])
        filas_resumen.append(["DISTRIBUCIÓN POR CATEGORÍA TEMÁTICA", ""])
        filas_resumen.append(["Categoría", "Tipo", "Conteo", "% del total"])
        for cat_key, info in resumen["por_categoria"].items():
            filas_resumen.append([
                info["nombre"],
                info["tipo"],
                info["conteo"],
                info["porcentaje"],
            ])

        df_resumen = pd.DataFrame(filas_resumen)
        df_resumen.to_excel(writer, sheet_name="Resumen", index=False, header=False)

        # ── Hoja 3: Por grupo (si aplica) ──────────────────────────────────
        if columna_agrupacion and "por_grupo" in resumen:
            filas_grupo = []
            filas_grupo.append([f"Agrupación por: {columna_agrupacion}", "", "", ""])
            filas_grupo.append(["Grupo", "Categoría", "Tipo", "Conteo", "% dentro del grupo"])
            for grupo, datos_grupo in resumen["por_grupo"].items():
                for cat_key, cat_data in datos_grupo["por_categoria"].items():
                    filas_grupo.append([
                        grupo,
                        cat_data["nombre"],
                        CATEGORIAS[cat_key]["tipo"],
                        cat_data["conteo"],
                        cat_data["porcentaje"],
                    ])
            df_grupo = pd.DataFrame(filas_grupo)
            df_grupo.to_excel(
                writer, sheet_name=f"Por {columna_agrupacion}", index=False, header=False
            )

        # ── Hoja 4: Auditoría ──────────────────────────────────────────────
        filas_audit = []
        filas_audit.append(["REGISTRO DE AUDITORÍA", ""])
        filas_audit.append(["Herramienta", log_auditoria["meta"]["nombre_herramienta"]])
        filas_audit.append(["Timestamp UTC", log_auditoria["meta"]["timestamp_utc"]])
        filas_audit.append(["Versión analizador", log_auditoria["meta"]["version_analizador"]])
        filas_audit.append(["Versión léxico", log_auditoria["meta"]["version_lexico"]])
        filas_audit.append(["", ""])
        filas_audit.append(["DATASET", ""])
        filas_audit.append(["Archivo", log_auditoria["dataset"]["nombre_archivo"]])
        filas_audit.append(["Total filas", log_auditoria["dataset"]["total_filas"]])
        filas_audit.append(["Columna texto", log_auditoria["dataset"]["columna_texto"]])
        filas_audit.append(["Hash SHA-256 textos", log_auditoria["dataset"]["hash_sha256_textos"]])
        filas_audit.append(["", ""])
        filas_audit.append(["PARÁMETROS", ""])
        for param, valor in log_auditoria["parametros"].items():
            filas_audit.append([param, str(valor)])
        filas_audit.append(["", ""])
        filas_audit.append([
            "NOTA METODOLÓGICA",
            log_auditoria["meta"]["nota_metodologica"],
        ])

        df_audit = pd.DataFrame(filas_audit)
        df_audit.to_excel(writer, sheet_name="Auditoría", index=False, header=False)

    return output.getvalue()


def exportar_json_auditoria(log: Dict) -> str:
    """Serializa el log de auditoría a JSON con indentación legible."""
    return json.dumps(log, ensure_ascii=False, indent=2)
