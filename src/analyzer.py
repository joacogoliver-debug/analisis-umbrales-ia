"""
Motor de análisis y clasificación temática.

MÉTODO: Clasificador léxico ponderado con TF-IDF por categoría
        + detección de negación por ventana de tokens.

Por qué este enfoque:
- 100% determinístico: mismo texto → mismo resultado siempre
- Auditabilidad completa: cada clasificación lista las keywords que la activaron
  y las keywords que fueron negadas (con su contexto)
- Sin modelos externos, sin randomness, sin dependencias de red
- Interpretable: el score es la proporción de palabras del texto
  que pertenecen a cada categoría (normalizado por longitud)

Manejo de negación (v1.1.0):
- Las keywords negadas NO contribuyen al score positivo de su categoría
- Se registran en `keywords_negadas` para auditoría y revisión
- Se señalizan como advertencias en la salida al usuario
- Método: ventana de tokens con límites de cláusula (ver src/negation.py)
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.lexicon import CATEGORIAS, STOPWORDS_ES, VERSION_LEXICO
from src.negation import (
    VENTANA_NEGACION,
    esta_negado,
    obtener_parametros_negacion,
    tokenizar_con_limites,
)
from src.preprocessor import limpiar_texto, normalizar_acentos, tokenizar


VERSION_ANALIZADOR = "1.1.0"
UMBRAL_CLASIFICACION = 0.03   # score mínimo para asignar categoría (3%)
MAX_CATEGORIAS_POR_TEXTO = 3  # máximo de categorías asignadas por texto


@dataclass
class ResultadoTexto:
    """Resultado de análisis para un texto individual."""
    id_texto: int
    texto_original: str
    texto_preprocesado: str
    categorias_asignadas: List[str]             # claves de categorías asignadas (positivas)
    scores: Dict[str, float]                    # score positivo por categoría
    keywords_activadas: Dict[str, List[str]]    # keywords positivas que activaron cada cat
    keywords_negadas: Dict[str, List[str]]      # keywords negadas detectadas por categoría
    scores_negados: Dict[str, float]            # score de menciones negadas por categoría
    tipo_predominante: str                      # 'factor_protector', 'estresor', 'neutro', 'sin_clasificar'
    longitud_tokens: int
    tiene_negaciones: bool                      # True si alguna keyword fue negada
    metadata: Dict = field(default_factory=dict)


def _normalizar_keyword(kw: str) -> str:
    """Preprocesa una keyword para comparación: minúsculas + normalización acentos."""
    return normalizar_acentos(kw.lower().strip())


def _construir_index_lexico() -> Dict[str, List[str]]:
    """
    Construye un índice invertido: keyword_normalizada → [categoria1, categoria2, ...]
    Se computa una sola vez al cargar el módulo.
    """
    index: Dict[str, List[str]] = {}
    for cat_key, cat_def in CATEGORIAS.items():
        for kw in cat_def["keywords"]:
            kw_norm = _normalizar_keyword(kw)
            if kw_norm not in index:
                index[kw_norm] = []
            if cat_key not in index[kw_norm]:
                index[kw_norm].append(cat_key)
    return index


# Índice pre-computado (determinístico, cargado una vez)
_INDEX_LEXICO = _construir_index_lexico()


def _es_palabra(token: str) -> bool:
    """True si el token es una palabra (no puntuación)."""
    return len(token) >= 2 and token.isalpha()


def calcular_scores(
    texto: str,
    ventana_negacion: int = VENTANA_NEGACION,
) -> Tuple[
    Dict[str, float],       # scores positivos
    Dict[str, List[str]],   # keywords positivas activadas
    Dict[str, float],       # scores de menciones negadas
    Dict[str, List[str]],   # keywords negadas
]:
    """
    Calcula el score de cada categoría para un texto dado,
    distinguiendo entre menciones positivas y negadas.

    Algoritmo:
    1. Tokenizar el texto preservando puntuación (para límites de cláusula)
    2. Para cada token en posición i:
       a. Si es una keyword conocida, verificar si está negada
          usando `esta_negado(secuencia, i)`
       b. Si NO está negada: sumar al score positivo
       c. Si está negada: registrar en keywords_negadas (sin afectar score positivo)
    3. Repetir para bigramas (usando posición del primer token)
    4. Score final = (conteo_positivos / total_tokens) × peso_categoría

    La negación se detecta por ventana de tokens con límites de cláusula.
    Ver src/negation.py para la especificación completa del método.

    Returns:
        (scores, keywords_activadas, scores_negados, keywords_negadas)
    """
    texto_norm = normalizar_acentos(limpiar_texto(texto))

    if not texto_norm.strip():
        empty = {k: [] for k in CATEGORIAS}
        empty_scores = {k: 0.0 for k in CATEGORIAS}
        return empty_scores, empty, empty_scores, empty

    # Secuencia con puntuación para detección de negación
    secuencia = tokenizar_con_limites(texto_norm)

    # Solo palabras para contar tokens totales
    tokens_solo_palabras = [t for t in secuencia if _es_palabra(t)]
    total_tokens = len(tokens_solo_palabras)

    if total_tokens == 0:
        empty = {k: [] for k in CATEGORIAS}
        empty_scores = {k: 0.0 for k in CATEGORIAS}
        return empty_scores, empty, empty_scores, empty

    conteos_pos: Dict[str, int] = {k: 0 for k in CATEGORIAS}
    conteos_neg: Dict[str, int] = {k: 0 for k in CATEGORIAS}
    activadas_pos: Dict[str, List[str]] = {k: [] for k in CATEGORIAS}
    activadas_neg: Dict[str, List[str]] = {k: [] for k in CATEGORIAS}

    for i, token in enumerate(secuencia):
        if not _es_palabra(token):
            continue

        # ── Unigrama ──────────────────────────────────────────────────────
        if token in _INDEX_LEXICO:
            negado = esta_negado(secuencia, i, ventana_negacion)
            for cat_key in _INDEX_LEXICO[token]:
                if negado:
                    conteos_neg[cat_key] += 1
                    if token not in activadas_neg[cat_key]:
                        activadas_neg[cat_key].append(token)
                else:
                    conteos_pos[cat_key] += 1
                    if token not in activadas_pos[cat_key]:
                        activadas_pos[cat_key].append(token)

        # ── Bigrama: buscar la siguiente palabra en la secuencia ──────────
        for j in range(i + 1, min(i + 4, len(secuencia))):
            if _es_palabra(secuencia[j]):
                bigrama = f"{token} {secuencia[j]}"
                if bigrama in _INDEX_LEXICO:
                    # La negación se evalúa en la posición del primer token (i)
                    negado = esta_negado(secuencia, i, ventana_negacion)
                    for cat_key in _INDEX_LEXICO[bigrama]:
                        if negado:
                            conteos_neg[cat_key] += 1
                            etiqueta = f"[NEG] {bigrama}"
                            if etiqueta not in activadas_neg[cat_key]:
                                activadas_neg[cat_key].append(etiqueta)
                        else:
                            conteos_pos[cat_key] += 1
                            if bigrama not in activadas_pos[cat_key]:
                                activadas_pos[cat_key].append(bigrama)
                break  # solo el bigrama con la siguiente palabra

    scores_pos = {
        k: round((conteos_pos[k] / total_tokens) * CATEGORIAS[k]["peso"], 4)
        for k in CATEGORIAS
    }
    scores_neg = {
        k: round((conteos_neg[k] / total_tokens) * CATEGORIAS[k]["peso"], 4)
        for k in CATEGORIAS
    }

    return scores_pos, activadas_pos, scores_neg, activadas_neg


def clasificar_texto(
    id_texto: int,
    texto: str,
    umbral: float = UMBRAL_CLASIFICACION,
    max_categorias: int = MAX_CATEGORIAS_POR_TEXTO,
    ventana_negacion: int = VENTANA_NEGACION,
) -> ResultadoTexto:
    """
    Clasifica un texto y retorna un ResultadoTexto con toda la trazabilidad.

    Solo las menciones NO negadas contribuyen a la clasificación.
    Las menciones negadas se registran para auditoría y se señalan como advertencias.

    Args:
        id_texto: identificador único del texto
        texto: texto original sin procesar
        umbral: score mínimo para asignar categoría
        max_categorias: máximo de categorías asignadas
        ventana_negacion: tamaño de la ventana de negación en tokens

    Returns:
        ResultadoTexto con scores positivos, negados, keywords y categorías asignadas
    """
    texto_limpio = limpiar_texto(texto)
    tokens = tokenizar(normalizar_acentos(texto_limpio))

    scores, kw_pos, scores_neg, kw_neg = calcular_scores(texto, ventana_negacion)

    # Ordenar por score positivo descendente
    cats_ordenadas = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Asignar solo categorías con score positivo ≥ umbral
    categorias_asignadas = [
        cat for cat, score in cats_ordenadas
        if score >= umbral
    ][:max_categorias]

    # Filtrar keywords solo de categorías asignadas
    kw_pos_filtradas = {
        cat: kws for cat, kws in kw_pos.items()
        if cat in categorias_asignadas
    }
    # Keywords negadas: incluir TODAS las categorías con negaciones (no solo asignadas)
    # porque una negación en una cat no asignada también es información valiosa
    kw_neg_filtradas = {
        cat: kws for cat, kws in kw_neg.items()
        if kws
    }

    # Determinar tipo predominante (solo con scores positivos)
    if not categorias_asignadas:
        tipo_predominante = "sin_clasificar"
    else:
        conteo_tipos = {"factor_protector": 0.0, "estresor": 0.0, "neutro": 0.0}
        for cat in categorias_asignadas:
            conteo_tipos[CATEGORIAS[cat]["tipo"]] += scores[cat]

        tipo_predominante = max(conteo_tipos, key=lambda k: conteo_tipos[k])
        if conteo_tipos[tipo_predominante] == 0:
            tipo_predominante = "sin_clasificar"

    tiene_negaciones = bool(kw_neg_filtradas)

    return ResultadoTexto(
        id_texto=id_texto,
        texto_original=texto,
        texto_preprocesado=texto_limpio,
        categorias_asignadas=categorias_asignadas,
        scores=scores,
        keywords_activadas=kw_pos_filtradas,
        keywords_negadas=kw_neg_filtradas,
        scores_negados=scores_neg,
        tipo_predominante=tipo_predominante,
        longitud_tokens=len(tokens),
        tiene_negaciones=tiene_negaciones,
    )


def analizar_dataset(
    df: pd.DataFrame,
    columna_texto: str,
    columna_id: Optional[str] = None,
    umbral: float = UMBRAL_CLASIFICACION,
    max_categorias: int = MAX_CATEGORIAS_POR_TEXTO,
    ventana_negacion: int = VENTANA_NEGACION,
) -> pd.DataFrame:
    """
    Analiza un DataFrame completo y retorna un DataFrame enriquecido.

    Columnas agregadas:
    - texto_original, texto_preprocesado
    - categorias, categorias_nombres, tipo_predominante
    - score_[cat] — score positivo por categoría
    - keywords_[cat] — keywords positivas por categoría
    - neg_keywords_[cat] — keywords negadas por categoría
    - neg_score_[cat] — score de menciones negadas por categoría
    - tiene_negaciones — True si alguna keyword fue negada
    - longitud_tokens, clasificado

    Args:
        df: DataFrame con al menos la columna de texto
        columna_texto: nombre de la columna con los textos
        columna_id: columna identificadora (opcional)
        umbral: score mínimo para clasificar
        max_categorias: máximo de categorías por texto
        ventana_negacion: tamaño ventana de negación

    Returns:
        DataFrame original + columnas de análisis
    """
    resultados = []

    for idx, row in df.iterrows():
        texto = str(row.get(columna_texto, "")) if pd.notna(row.get(columna_texto, "")) else ""
        id_texto = int(row[columna_id]) if columna_id and columna_id in row else idx

        resultado = clasificar_texto(
            id_texto=id_texto,
            texto=texto,
            umbral=umbral,
            max_categorias=max_categorias,
            ventana_negacion=ventana_negacion,
        )
        resultados.append(resultado)

    df_out = df.copy()
    df_out["texto_original"] = [r.texto_original for r in resultados]
    df_out["texto_preprocesado"] = [r.texto_preprocesado for r in resultados]
    df_out["categorias"] = ["|".join(r.categorias_asignadas) for r in resultados]
    df_out["categorias_nombres"] = [
        "|".join(CATEGORIAS[c]["nombre"] for c in r.categorias_asignadas)
        for r in resultados
    ]
    df_out["tipo_predominante"] = [r.tipo_predominante for r in resultados]
    df_out["longitud_tokens"] = [r.longitud_tokens for r in resultados]
    df_out["clasificado"] = [len(r.categorias_asignadas) > 0 for r in resultados]
    df_out["tiene_negaciones"] = [r.tiene_negaciones for r in resultados]

    # Scores y keywords positivas
    for cat_key in CATEGORIAS:
        df_out[f"score_{cat_key}"] = [r.scores[cat_key] for r in resultados]
        df_out[f"keywords_{cat_key}"] = [
            ", ".join(r.keywords_activadas.get(cat_key, []))
            for r in resultados
        ]

    # Scores y keywords negadas
    for cat_key in CATEGORIAS:
        df_out[f"neg_score_{cat_key}"] = [r.scores_negados[cat_key] for r in resultados]
        df_out[f"neg_keywords_{cat_key}"] = [
            ", ".join(r.keywords_negadas.get(cat_key, []))
            for r in resultados
        ]

    return df_out


def calcular_resumen_agregado(
    df_analizado: pd.DataFrame,
    columna_agrupacion: Optional[str] = None,
) -> Dict:
    """
    Calcula estadísticas agregadas del dataset analizado.
    Incluye conteo de textos con negaciones detectadas.
    """
    total = len(df_analizado)
    clasificados = df_analizado["clasificado"].sum()
    con_negaciones = df_analizado["tiene_negaciones"].sum() if "tiene_negaciones" in df_analizado.columns else 0

    conteo_categorias = {}
    for cat_key in CATEGORIAS:
        mask_pos = df_analizado["categorias"].str.contains(cat_key, na=False)
        mask_neg = (df_analizado.get(f"neg_score_{cat_key}", 0) > 0)
        conteo_pos = int(mask_pos.sum())
        conteo_neg = int(mask_neg.sum()) if f"neg_score_{cat_key}" in df_analizado.columns else 0
        conteo_categorias[cat_key] = {
            "nombre": CATEGORIAS[cat_key]["nombre"],
            "tipo": CATEGORIAS[cat_key]["tipo"],
            "conteo": conteo_pos,
            "porcentaje": round(conteo_pos / total * 100, 1) if total > 0 else 0,
            "menciones_negadas": conteo_neg,
        }

    tipos = df_analizado["tipo_predominante"].value_counts().to_dict()

    resumen = {
        "total_textos": total,
        "textos_clasificados": int(clasificados),
        "textos_sin_clasificar": int(total - clasificados),
        "tasa_clasificacion": round(clasificados / total * 100, 1) if total > 0 else 0,
        "textos_con_negaciones": int(con_negaciones),
        "por_categoria": conteo_categorias,
        "por_tipo": {k: int(v) for k, v in tipos.items()},
    }

    if columna_agrupacion and columna_agrupacion in df_analizado.columns:
        resumen_por_grupo = {}
        for grupo, df_grupo in df_analizado.groupby(columna_agrupacion):
            total_g = len(df_grupo)
            cats_g = {}
            for cat_key in CATEGORIAS:
                mask = df_grupo["categorias"].str.contains(cat_key, na=False)
                conteo_g = int(mask.sum())
                cats_g[cat_key] = {
                    "nombre": CATEGORIAS[cat_key]["nombre"],
                    "conteo": conteo_g,
                    "porcentaje": round(conteo_g / total_g * 100, 1) if total_g > 0 else 0,
                }
            resumen_por_grupo[str(grupo)] = {
                "total": total_g,
                "por_categoria": cats_g,
                "por_tipo": df_grupo["tipo_predominante"].value_counts().to_dict(),
            }
        resumen["por_grupo"] = resumen_por_grupo

    return resumen


def obtener_parametros_analisis(
    umbral: float = UMBRAL_CLASIFICACION,
    max_categorias: int = MAX_CATEGORIAS_POR_TEXTO,
    ventana_negacion: int = VENTANA_NEGACION,
) -> Dict:
    """Retorna los parámetros del análisis para el log de auditoría."""
    params = {
        "version_analizador": VERSION_ANALIZADOR,
        "version_lexico": VERSION_LEXICO,
        "umbral_clasificacion": umbral,
        "max_categorias_por_texto": max_categorias,
        "total_categorias": len(CATEGORIAS),
        "total_keywords": sum(len(c["keywords"]) for c in CATEGORIAS.values()),
        "metodo": "clasificacion_lexica_ponderada_con_deteccion_negacion",
        "normalizacion": "unicode_NFC + minusculas + normalizacion_acentos",
        "tokenizacion": "regex_palabras_>=2_chars + marcadores_puntuacion",
        "scoring": "conteo_matches_positivos / total_tokens * peso_categoria",
    }
    params.update(obtener_parametros_negacion(ventana_negacion))
    return params
