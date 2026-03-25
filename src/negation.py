"""
Módulo de detección de negación por ventana de tokens.

MÉTODO: Negation scope window
Basado en: Polanyi & Zaenen (2006), adaptado de la implementación de VADER
           (Hutto & Gilbert, 2014) para español rioplatense/latinoamericano.

El alcance de la negación funciona así:
  "no  me  gusta  la  familia"
   [N] [1] [2]   [3]  [4=keyword]
   ↑__ dentro de la ventana → keyword NEGADA

Interrupciones del alcance:
  "no me gusta, pero quiero a mi familia"
   [N]          [,=límite]              [keyword]
                ↑__ límite de cláusula → keyword NO negada

Limitaciones conocidas y documentadas:
  - No detecta doble negación: "no es que no me guste" (raro en textos cortos)
  - No detecta ironía: "claro que me encanta que me peguen"
  - Negación de largo alcance con subordinadas complejas puede fallar
  Estos casos son infrecuentes en frases cortas de talleres adolescentes.
"""

import re
from typing import List

VERSION_NEGACION = "1.0.0"
VENTANA_NEGACION = 4  # máximo de palabras a revisar antes de la keyword

# ── Palabras de negación en español ──────────────────────────────────────────
# Incluye formas del español rioplatense y latinoamericano
PALABRAS_NEGACION = {
    "no", "ni", "sin", "nunca", "jamas", "jamás",
    "tampoco", "nada", "nadie", "ninguno", "ninguna",
    "ningun", "ningún", "imposible", "incapaz",
}

# ── Límites de cláusula (interrumpen el alcance de la negación) ──────────────
# Puntuación dura
LIMITES_PUNTUACION = {",", ";", ".", "?", "!", ":"}

# Conjunciones adversativas y contrastivas (palabras que "resetean" la negación)
LIMITES_PALABRAS = {"pero", "aunque", "sino", "mas", "sin embargo",
                    "a pesar", "no obstante", "igual", "igualmente"}


def tokenizar_con_limites(texto: str) -> List[str]:
    """
    Tokeniza preservando marcadores de puntuación como señales de límite.

    A diferencia de `tokenizar()` en preprocessor.py, este tokenizador
    conserva los signos de puntuación porque son necesarios para detectar
    interrupciones del alcance de la negación.

    Ejemplo:
      "no me gusta, pero quiero a mi familia"
      → ["no", "me", "gusta", ",", "pero", "quiero", "a", "mi", "familia"]
    """
    tokens = re.findall(r'[a-záéíóúüñ]{2,}|[.,;?!:]', texto.lower(), flags=re.UNICODE)
    return tokens


def esta_negado(secuencia: List[str], indice: int, ventana: int = VENTANA_NEGACION) -> bool:
    """
    Determina si el token en `indice` está dentro del alcance de una negación.

    Recorre la secuencia hacia atrás desde `indice - 1`.
    Cuenta solo palabras (no puntuación) para la ventana.
    Se detiene si encuentra un límite de cláusula antes de una negación.

    Args:
        secuencia: lista con palabras Y signos de puntuación (de tokenizar_con_limites)
        indice: posición del token a evaluar en `secuencia`
        ventana: máximo de palabras a revisar (por defecto 4)

    Returns:
        True si el token está negado, False en caso contrario.

    Ejemplos:
        ["no", "me", "gusta", "la", "familia"] → esta_negado(seq, 4) → True
        ["quiero", "a", "mi", "familia"]        → esta_negado(seq, 3) → False
        ["no", "me", "gusta", ",", "familia"]   → esta_negado(seq, 4) → False (límite ,)
        ["no", "gusta", "pero", "familia"]      → esta_negado(seq, 3) → False (límite pero)
    """
    palabras_revisadas = 0

    for j in range(indice - 1, -1, -1):
        tok = secuencia[j]

        # Límite duro: puntuación → terminar búsqueda sin negación
        if tok in LIMITES_PUNTUACION:
            return False

        # Límite blando: conjunción adversativa → terminar búsqueda sin negación
        if tok in LIMITES_PALABRAS:
            return False

        # Palabra de negación encontrada dentro de la ventana
        if tok in PALABRAS_NEGACION:
            return True

        # Contamos palabras reales (no puntuación) para la ventana
        if len(tok) >= 2:
            palabras_revisadas += 1
            if palabras_revisadas >= ventana:
                return False

    return False


def obtener_parametros_negacion(ventana: int = VENTANA_NEGACION) -> dict:
    """Retorna los parámetros del módulo de negación para el log de auditoría."""
    return {
        "version_negacion": VERSION_NEGACION,
        "ventana_negacion": ventana,
        "total_palabras_negacion": len(PALABRAS_NEGACION),
        "palabras_negacion": sorted(PALABRAS_NEGACION),
        "limites_puntuacion": sorted(LIMITES_PUNTUACION),
        "limites_palabras": sorted(LIMITES_PALABRAS),
        "metodo_negacion": "ventana_tokens_con_limites_clausula",
        "referencia": "Polanyi & Zaenen (2006), adaptado de VADER (Hutto & Gilbert, 2014)",
    }
