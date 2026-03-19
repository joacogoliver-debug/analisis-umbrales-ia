# Umbrales · Análisis de Narrativas Juveniles

Sistema de análisis sistemático de textos producidos por jóvenes en talleres educativos.
Identifica patrones temáticos vinculados a **factores protectores** y **estresores**.

> Este sistema realiza *análisis sistemático de narrativas juveniles con herramientas de lenguaje*.
> No constituye diagnóstico clínico ni epidemiológico.

---

## Requisitos del sistema

- Python 3.9 o superior
- pip

---

## Instalación y ejecución

```bash
# 1. Clonar o descomprimir el proyecto
cd analisis-umbrales-ia

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate.bat       # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
streamlit run app.py
```

La app abre automáticamente en el navegador en `http://localhost:8501`.

---

## Flujo de uso

1. **Subir archivo** — CSV o Excel con los textos
2. **Configurar columnas** — indicar cuál columna tiene los textos y (opcionalmente) columnas de agrupación
3. **Ejecutar análisis** — el sistema clasifica cada texto
4. **Revisar resultados** — gráficos, tablas y explorador texto por texto
5. **Exportar** — reporte Excel y log de auditoría JSON

---

## Formato del archivo de entrada

El archivo debe tener al menos una columna de texto. Ejemplo mínimo:

| texto |
|-------|
| Me gusta estar con mi familia |
| Tengo miedo de que me roben |

Con variables adicionales (recomendado):

| id | texto | region | taller | sexo |
|----|-------|--------|--------|------|

---

## Categorías temáticas

| Categoría | Tipo |
|-----------|------|
| Familia y Vínculos Afectivos | Factor protector |
| Amigos y Relaciones entre Pares | Factor protector |
| Educación y Aprendizaje | Factor protector |
| Salud Mental y Bienestar Emocional | Factor protector/Estresor |
| Violencia y Conflicto | Estresor |
| Futuro y Proyectos de Vida | Factor protector |
| Identidad y Autopercepción | Neutro |
| Territorio y Comunidad | Neutro |
| Recreación, Arte y Cultura | Factor protector |
| Trabajo y Situación Económica | Estresor |
| Miedos y Ansiedades | Estresor |
| Consumo de Sustancias | Estresor |

---

## Metodología técnica

### Método: Clasificación Léxica Ponderada

**Por qué este método:**

- **Reproducible**: mismo input → mismo output, sin randomness ni APIs externas
- **Auditable**: cada clasificación lista exactamente qué palabras la activaron
- **Interpretable**: el score es la proporción de tokens del texto que coinciden con el léxico de la categoría
- **Sin dependencias externas**: no requiere internet ni servicios de terceros en producción

**Pipeline:**

1. **Preprocesamiento**: normalización Unicode (NFC) → minúsculas → eliminación de URLs → normalización de acentos (solo para comparación interna)
2. **Tokenización**: extracción de palabras de ≥2 caracteres con regex
3. **Matching léxico**: búsqueda de tokens y bigramas en índice de keywords por categoría
4. **Scoring**: `score = (matches / total_tokens) × peso_categoría`
5. **Asignación**: categorías con `score ≥ umbral` (default: 0.03), máximo 3 por texto
6. **Tipo predominante**: suma ponderada de scores por tipo (protector / estresor / neutro)

**Limitación conocida:** el sistema no detecta negación compleja (ej. "no me gusta la familia"). Se recomienda revisar manualmente los textos con score cercano al umbral.

### Parámetros del análisis

| Parámetro | Valor por defecto | Descripción |
|-----------|------------------|-------------|
| Umbral de clasificación | 0.03 | Score mínimo para asignar categoría |
| Máx. categorías por texto | 3 | Categorías asignadas simultáneamente |

Los parámetros se pueden ajustar desde el panel lateral de la app.

---

## Auditoría

Cada ejecución genera:

- **Reporte Excel** con 4 hojas:
  - `Resultados`: texto por texto con scores y keywords
  - `Resumen`: estadísticas agregadas
  - `Por [grupo]`: desglose si se usó agrupación
  - `Auditoría`: versiones, parámetros, hash del dataset

- **Log JSON de auditoría** con:
  - Timestamp UTC
  - Versión del analizador y del léxico
  - Hash SHA-256 del dataset (para verificar integridad)
  - Parámetros usados
  - Resultados agregados

---

## Estructura del proyecto

```
analisis-umbrales-ia/
├── app.py                   # Aplicación Streamlit (interfaz web)
├── requirements.txt         # Dependencias Python
├── README.md
├── src/
│   ├── __init__.py
│   ├── lexicon.py           # Léxico de categorías temáticas (v1.0.0)
│   ├── preprocessor.py      # Normalización y tokenización de textos
│   ├── analyzer.py          # Motor de clasificación y scoring
│   └── reporter.py          # Generación de reportes Excel y JSON
├── data/
│   └── ejemplo_textos.csv   # Dataset de 50 textos de ejemplo
└── reportes/                # Carpeta para guardar reportes generados
```

---

## Extensibilidad

Para agregar nuevas categorías o keywords, editá `src/lexicon.py`:

```python
CATEGORIAS["nueva_categoria"] = {
    "nombre": "Nombre Legible",
    "tipo": "factor_protector",  # o "estresor" o "neutro"
    "descripcion": "Descripción operacional",
    "keywords": ["palabra1", "palabra2", "frase dos palabras"],
    "peso": 1.0,
}
```

Los cambios se aplican automáticamente en el próximo análisis. Incrementar `VERSION_LEXICO` para trazabilidad.

---

## Licencia y uso institucional

Este sistema está diseñado para uso en contextos de investigación social, programas de juventud y evaluación de talleres educativos. Los resultados deben interpretarse como indicadores exploratorios, no como diagnósticos individuales.
