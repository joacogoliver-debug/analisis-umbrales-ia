"""
Motor de análisis y clasificación temática.

MÉTODO: Clasificador léxico ponderado con TF-IDF por categoría.

Por qué este enfoque:
- 100% determinístico: mismo texto → mismo resultado siempre
- Auditabilidad completa: cada clasificación lista las keywords que la activaron
- Sin modelos externos, sin randomness, sin dependencias de red
- Interpretable: el score es la proporción de palabras del texto
  que pertenecen a cada categoría (normalizado por longitud)

Limitación conocida y aceptada:
- No captura ironía ni negación compleja (ej. "no me gusta la familia")
  → se mitiga registrando el texto original junto al resultado
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.lexicon import CATEGORIAS, STOPWORDS_ES, VERSION_LEXICO
from src.preprocessor import limpiar_texto, normalizar_acentos, tokenizar


VERSION_ANALIZADOR = "1.0.0"
UMBRAL_CLASIFICACION = 0.03   # score mínimo para asignar categoría (3%)
MAX_CATEGORIAS_POR_TEXTO = 3  # máximo de categorías asignadas por texto


@dataclass
class ResultadoTexto:
    """Resultado de análisis para un texto individual."""
    id_texto: int
    texto_original: str
    texto_preprocesado: str
    categorias_asignadas: List[str]           # lista de claves de categoría
    scores: Dict[str, float]                  # score por categoría
    keywords_activadas: Dict[str, List[str]]  # keywords que activaron cada categoría
    tipo_predominante: str                    # 'factor_protector', 'estresor', 'neutro', 'sin_clasificar'
    longitud_tokens: int
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


def calcular_scores(texto: str) -> Tuple[Dict[str, float], Dict[str, List[str]]]:
    """
    Calcula el score de cada categoría para un texto dado.

    Algoritmo:
    1. Tokenizar el texto
    2. Para cada token, buscar en el índice léxico
    3. Si hay match, sumar 1 al contador de la categoría
    4. El score final = (conteo_matches / total_tokens) * peso_categoria
       → normalizado por longitud para comparar textos cortos y largos equitativamente

    Returns:
        scores: dict {categoria: score_normalizado}
        keywords_activadas: dict {categoria: [keywords que matchearon]}
    """
    texto_norm = normalizar_acentos(limpiar_texto(texto))
    tokens = tokenizar(texto_norm)

    if not tokens:
        return {k: 0.0 for k in CATEGORIAS}, {k: [] for k in CATEGORIAS}

    conteos: Dict[str, int] = {k: 0 for k in CATEGORIAS}
    activadas: Dict[str, List[str]] = {k: [] for k in CATEGORIAS}

    # También buscar frases de 2 tokens (bigramas) para capturar "me gusta", "no quiero", etc.
    bigramas = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
    todos_los_candidatos = tokens + bigramas

    for candidato in todos_los_candidatos:
        if candidato in _INDEX_LEXICO:
            for cat_key in _INDEX_LEXICO[candidato]:
                conteos[cat_key] += 1
                if candidato not in activadas[cat_key]:
                    activadas[cat_key].append(candidato)

    total_tokens = len(tokens)
    scores = {}
    for cat_key, conteo in conteos.items():
        peso = CATEGORIAS[cat_key]["peso"]
        scores[cat_key] = round((conteo / total_tokens) * peso, 4)

    return scores, activadas


def clasificar_texto(
    id_texto: int,
    texto: str,
    umbral: float = UMBRAL_CLASIFICACION,
    max_categorias: int = MAX_CATEGORIAS_POR_TEXTO,
) -> ResultadoTexto:
    """
    Clasifica un texto y retorna un ResultadoTexto con toda la trazabilidad.

    Args:
        id_texto: identificador único del texto
        texto: texto original sin procesar
        umbral: score mínimo para asignar categoría
        max_categorias: máximo de categorías asignadas

    Returns:
        ResultadoTexto con scores, keywords activadas y categorías asignadas
    """
    texto_limpio = limpiar_texto(texto)
    tokens = tokenizar(normalizar_acentos(texto_limpio))
    scores, keywords_activadas = calcular_scores(texto)

    # Ordenar categorías por score descendente
    cats_ordenadas = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Asignar categorías que superan el umbral (máximo max_categorias)
    categorias_asignadas = [
        cat for cat, score in cats_ordenadas
        if score >= umbral
    ][:max_categorias]

    # Limpiar keywords de categorías no asignadas
    kw_filtradas = {
        cat: kws for cat, kws in keywords_activadas.items()
        if cat in categorias_asignadas
    }

    # Determinar tipo predominante
    if not categorias_asignadas:
        tipo_predominante = "sin_clasificar"
    else:
        conteo_tipos = {"factor_protector": 0, "estresor": 0, "neutro": 0}
        for cat in categorias_asignadas:
            tipo = CATEGORIAS[cat]["tipo"]
            conteo_tipos[tipo] += scores[cat]  # ponderado por score

        tipo_predominante = max(conteo_tipos, key=lambda k: conteo_tipos[k])
        if conteo_tipos[tipo_predominante] == 0:
            tipo_predominante = "sin_clasificar"

    return ResultadoTexto(
        id_texto=id_texto,
        texto_original=texto,
        texto_preprocesado=texto_limpio,
        categorias_asignadas=categorias_asignadas,
        scores=scores,
        keywords_activadas=kw_filtradas,
        tipo_predominante=tipo_predominante,
        longitud_tokens=len(tokens),
    )


def analizar_dataset(
    df: pd.DataFrame,
    columna_texto: str,
    columna_id: Optional[str] = None,
    umbral: float = UMBRAL_CLASIFICACION,
    max_categorias: int = MAX_CATEGORIAS_POR_TEXTO,
) -> pd.DataFrame:
    """
    Analiza un DataFrame completo y retorna un DataFrame enriquecido.

    Columnas agregadas al DataFrame resultante:
    - texto_preprocesado
    - categorias (str separada por |)
    - categorias_nombres (nombres legibles separados por |)
    - tipo_predominante
    - score_[categoria] para cada categoría del léxico
    - keywords_[categoria] para las categorías asignadas
    - longitud_tokens
    - clasificado (bool)

    Args:
        df: DataFrame con al menos la columna de texto
        columna_texto: nombre de la columna con los textos
        columna_id: nombre de la columna ID (opcional)
        umbral: score mínimo para clasificar
        max_categorias: máximo de categorías por texto

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
        )
        resultados.append(resultado)

    # Construir DataFrame de resultados
    df_out = df.copy()
    # Columna normalizada para que la app siempre pueda referenciarla
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

    # Columnas de score por categoría
    for cat_key in CATEGORIAS:
        df_out[f"score_{cat_key}"] = [r.scores[cat_key] for r in resultados]

    # Columnas de keywords activadas (solo categorías asignadas)
    for cat_key in CATEGORIAS:
        df_out[f"keywords_{cat_key}"] = [
            ", ".join(r.keywords_activadas.get(cat_key, []))
            for r in resultados
        ]

    return df_out


def calcular_resumen_agregado(
    df_analizado: pd.DataFrame,
    columna_agrupacion: Optional[str] = None,
) -> Dict:
    """
    Calcula estadísticas agregadas del dataset analizado.

    Args:
        df_analizado: DataFrame resultado de analizar_dataset()
        columna_agrupacion: columna opcional para agrupar (ej: 'region', 'sexo')

    Returns:
        dict con resúmenes por categoría, tipo y (opcionalmente) por grupo
    """
    total = len(df_analizado)
    clasificados = df_analizado["clasificado"].sum()

    # Conteo por categoría (un texto puede estar en múltiples)
    conteo_categorias = {}
    for cat_key in CATEGORIAS:
        mask = df_analizado["categorias"].str.contains(cat_key, na=False)
        conteo = int(mask.sum())
        conteo_categorias[cat_key] = {
            "nombre": CATEGORIAS[cat_key]["nombre"],
            "tipo": CATEGORIAS[cat_key]["tipo"],
            "conteo": conteo,
            "porcentaje": round(conteo / total * 100, 1) if total > 0 else 0,
        }

    # Conteo por tipo predominante
    tipos = df_analizado["tipo_predominante"].value_counts().to_dict()

    resumen = {
        "total_textos": total,
        "textos_clasificados": int(clasificados),
        "textos_sin_clasificar": int(total - clasificados),
        "tasa_clasificacion": round(clasificados / total * 100, 1) if total > 0 else 0,
        "por_categoria": conteo_categorias,
        "por_tipo": {k: int(v) for k, v in tipos.items()},
    }

    # Resumen por grupo si se especifica columna
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
) -> Dict:
    """
    Retorna el diccionario de parámetros usados en el análisis.
    Se incluye en el reporte de auditoría.
    """
    return {
        "version_analizador": VERSION_ANALIZADOR,
        "version_lexico": VERSION_LEXICO,
        "umbral_clasificacion": umbral,
        "max_categorias_por_texto": max_categorias,
        "total_categorias": len(CATEGORIAS),
        "total_keywords": sum(len(c["keywords"]) for c in CATEGORIAS.values()),
        "metodo": "clasificacion_lexica_ponderada",
        "normalizacion": "unicode_NFC + minusculas + normalizacion_acentos",
        "tokenizacion": "regex_palabras_>=2_chars",
        "scoring": "conteo_matches / total_tokens * peso_categoria",
    }
