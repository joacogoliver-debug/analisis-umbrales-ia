"""
Módulo de preprocesamiento de texto.

Todas las transformaciones son determinísticas: mismo input → mismo output.
No usa modelos externos ni randomness.
"""

import re
import unicodedata
from typing import List


def normalizar_unicode(texto: str) -> str:
    """
    Convierte caracteres Unicode a su forma normalizada NFC
    y elimina variantes tipográficas (comillas curvas, guiones especiales, etc.).
    """
    # Normalización NFC: composición canónica
    texto = unicodedata.normalize("NFC", texto)
    # Reemplazar variantes de comillas
    texto = re.sub(r'[""«»„]', '"', texto)
    # Reemplazar variantes de guion/raya
    texto = re.sub(r'[–—―]', '-', texto)
    # Reemplazar puntos suspensivos tipográficos
    texto = texto.replace("…", "...")
    return texto


def normalizar_acentos(texto: str) -> str:
    """
    Convierte vocales acentuadas a su versión sin tilde para mejorar
    el matching de keywords (solo para comparación interna, no modifica salida).
    Mantiene la ñ ya que es distintiva en español.
    """
    mapa = str.maketrans(
        "áéíóúÁÉÍÓÚàèìòùÀÈÌÒÙäëïöüÄËÏÖÜ",
        "aeiouAEIOUaeiouAEIOUaeiouAEIOU",
    )
    # Preservar ñ/Ñ antes de transformar
    texto = texto.replace("ñ", "\x00ENIE\x00").replace("Ñ", "\x00ENIE_MAY\x00")
    texto = texto.translate(mapa)
    texto = texto.replace("\x00ENIE\x00", "ñ").replace("\x00ENIE_MAY\x00", "Ñ")
    return texto


def limpiar_texto(texto: str) -> str:
    """
    Aplica pipeline de limpieza:
    1. Normalización Unicode
    2. Minúsculas
    3. Eliminar URLs
    4. Eliminar emojis y símbolos no alfanuméricos (excepto espacios)
    5. Normalizar espacios múltiples
    """
    if not isinstance(texto, str) or not texto.strip():
        return ""

    texto = normalizar_unicode(texto)
    texto = texto.lower()

    # Eliminar URLs
    texto = re.sub(r'https?://\S+|www\.\S+', ' ', texto)

    # Eliminar emojis y símbolos (mantiene letras, números, espacios, puntuación básica)
    texto = re.sub(r'[^\w\s\-.,;:!?áéíóúüñÁÉÍÓÚÜÑ]', ' ', texto, flags=re.UNICODE)

    # Normalizar espacios
    texto = re.sub(r'\s+', ' ', texto).strip()

    return texto


def tokenizar(texto: str) -> List[str]:
    """
    Divide el texto en tokens (palabras).
    Elimina tokens de un solo carácter (excepto letras solas con sentido).
    """
    tokens = re.findall(r'\b[a-záéíóúüñ]{2,}\b', texto.lower(), flags=re.UNICODE)
    return tokens


def preprocesar_para_matching(texto: str) -> str:
    """
    Versión del texto optimizada para comparación con keywords del léxico.
    Aplica normalización de acentos adicional para aumentar recall.
    El texto original no se modifica en la salida al usuario.
    """
    texto_limpio = limpiar_texto(texto)
    # Para matching interno, también normalizamos acentos
    texto_norm = normalizar_acentos(texto_limpio)
    return texto_norm


def preprocesar_dataset(textos: List[str]) -> List[str]:
    """
    Aplica limpiar_texto a una lista de textos.
    Retorna lista de misma longitud (textos vacíos → string vacío).
    """
    return [limpiar_texto(t) for t in textos]
