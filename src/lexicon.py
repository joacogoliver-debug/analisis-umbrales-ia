"""
Léxico de categorías temáticas para análisis de narrativas juveniles.

Cada categoría incluye:
- nombre: etiqueta legible
- tipo: 'factor_protector', 'estresor' o 'neutro'
- descripcion: definición operacional
- keywords: lista de términos en español (con variantes morfológicas comunes)
- peso: relevancia relativa de la categoría (1.0 = normal)

Fuentes conceptuales:
- Modelo de factores protectores y de riesgo (OPS/OMS)
- Marco de resiliencia juvenil (UNICEF LAC)
- Indicadores de desarrollo adolescente (INDEC)
"""

VERSION_LEXICO = "1.1.0"

CATEGORIAS = {
    "familia_vinculos": {
        "nombre": "Familia y Vínculos Afectivos",
        "tipo": "factor_protector",
        "descripcion": (
            "Referencias a relaciones familiares, convivencia doméstica "
            "y vínculos emocionales cercanos con figuras de cuidado."
        ),
        "keywords": [
            "familia", "mamá", "mama", "papá", "papa", "madre", "padre",
            "hermano", "hermana", "hermanos", "hermanas", "abuelo", "abuela",
            "abuelos", "tío", "tia", "tios", "primo", "prima", "primos",
            "hogar", "casa", "amor", "cariño", "carino", "querer", "quiero",
            "abrazo", "abrazos", "unión", "union", "juntos", "apoyo",
            "confianza", "contención", "contencion", "padres",
            "hijos", "hijo", "hija", "sobrino", "sobrina", "afecto",
            "compañía", "compania", "convivir", "convivencia",
            "navidad", "navidades", "reunión", "reunion", "reuniones",
            "celebrar", "celebración", "celebracion", "festejo", "festejar",
            "extrañar", "extraño", "extrano", "extrañas", "extrañarte",
            "volver", "volver a casa", "volver con", "reencontrarnos",
            "unidos", "unida", "unido", "familia unida", "vínculo", "vinculo",
            "cuidar", "cuidado", "cuidarme", "cuidarte", "proteger",
        ],
        "peso": 1.0,
    },
    "amigos_pares": {
        "nombre": "Amigos y Relaciones entre Pares",
        "tipo": "factor_protector",
        "descripcion": (
            "Menciones a amistades, grupos de pertenencia etaria "
            "y relaciones sociales con pares."
        ),
        "keywords": [
            "amigo", "amiga", "amigos", "amigas", "amistad", "amistades",
            "compañero", "compañera", "compañeros", "companero", "companera",
            "companeros", "pares", "grupo", "grupos", "banda", "pandilla",
            "juntarse", "juntarme", "salir", "compartir", "juntos",
            "divertirse", "pasarla bien", "risas", "reírse", "reirse",
            "confianza", "escuchar", "acompañar", "acompanar",
            "novio", "novia", "pareja", "chico", "chica", "pibe", "piba",
            "personas", "gente", "alguien", "conocer", "conocés",
            "alejarte", "alejarse", "alejar", "alejé", "aleje",
            "perder amigos", "perdí amigos", "quedarte solo", "quedarte sola",
            "acompañarte", "acompanarte", "estar con", "lazos",
        ],
        "peso": 1.0,
    },
    "educacion_aprendizaje": {
        "nombre": "Educación y Aprendizaje",
        "tipo": "factor_protector",
        "descripcion": (
            "Referencias a la escuela, el estudio, el conocimiento "
            "y procesos formativos formales e informales."
        ),
        "keywords": [
            "escuela", "colegio", "secundaria", "secundario", "universidad",
            "facultad", "estudiar", "estudios", "aprender", "aprendizaje",
            "libro", "libros", "clase", "clases", "maestro", "maestra",
            "profesor", "profesora", "profesores", "materias", "materia",
            "conocimiento", "educación", "educacion", "leer", "lectura",
            "escribir", "escritura", "matemática", "matematica", "historia",
            "ciencias", "geografía", "geografia", "taller", "talleres",
            "capacitación", "capacitacion", "formación", "formacion",
            "título", "titulo", "diploma", "becas", "beca",
        ],
        "peso": 1.0,
    },
    "salud_bienestar": {
        "nombre": "Salud Mental y Bienestar Emocional",
        "tipo": "factor_protector",
        "descripcion": (
            "Alusiones al estado emocional, la salud psicológica, "
            "el bienestar subjetivo y recursos de autocuidado."
        ),
        "keywords": [
            "feliz", "felicidad", "alegría", "alegria", "contento", "contenta",
            "bien", "bienestar", "salud", "tranquilo", "tranquila", "paz",
            "calma", "equilibrio", "emoción", "emocion", "sentir", "sentirse",
            "llorar", "tristeza", "triste", "angustia", "ansiedad", "nervios",
            "estrés", "estres", "depresión", "depresion", "soledad", "solo",
            "sola", "vacío", "vacio", "cansado", "cansada", "agotado",
            "psicólogo", "psicologa", "terapeuta", "terapia",
            "medicación", "medicacion", "pastillas", "dormir", "descansar",
            "respirar", "meditar", "relajarme", "autoestima",
            "disfrutar", "disfrutando", "disfrute", "disfrutá", "disfruta",
            "presente", "momento", "vivir el momento", "el aquí y ahora",
            "segura", "seguro", "seguridad", "sentirme segura", "sentirte seguro",
            "sentirme", "sentirte", "sintiendo", "sentí", "senti",
            "perdonar", "perdón", "perdon", "perdono", "perdonarme",
            "perdonarte", "perdonarse", "perdoná", "perdona",
            "aceptar", "aceptarme", "aceptarte", "aceptación", "aceptacion",
            "sanar", "sanarte", "sanarse", "sanarme", "curarme",
            "quererme", "quererte", "amarme", "amarte", "amarse",
            "valorarme", "valorarte", "valorarse", "valoración",
            "ritmo", "bajar el ritmo", "pausar", "pausa",
            "presente", "vivir", "vida", "vivir la vida",
            "emocionalmente", "interior", "interior", "proceso",
        ],
        "peso": 1.1,
    },
    "violencia_conflicto": {
        "nombre": "Violencia y Conflicto",
        "tipo": "estresor",
        "descripcion": (
            "Narrativas sobre situaciones de violencia física, verbal, "
            "simbólica, doméstica o en el entorno comunitario."
        ),
        "keywords": [
            "violencia", "pegar", "golpe", "golpes", "golpear", "pelear",
            "pelea", "peleas", "bullying", "acoso", "hostigamiento",
            "amenaza", "amenazas", "miedo", "miedos", "gritos", "gritar",
            "insultos", "insultar", "maltrato", "maltratar", "abuso",
            "abusar", "agresión", "agresion", "agresivo", "agresiva",
            "lastimar", "daño", "dano", "herido", "herida", "sangre",
            "arma", "armas", "cuchillo", "disparos", "tiroteo", "robo",
            "robaron", "asalto", "inseguridad", "peligro", "peligroso",
            "matar", "matarte", "matarme", "matarse", "mataba", "mató", "mato",
            "morir", "morirte", "morirme", "muerte", "muerto", "muerta",
            "suicidio", "suicidarse", "hacerse daño", "hacerme daño",
            "quitarse la vida", "quitarme la vida",
            "malas personas", "personas malas", "personas que hacen daño",
            "hacerte daño", "te hicieron", "hicieron daño",
            "herirte", "herirme", "lastimarte", "lastimarse",
        ],
        "peso": 1.2,
    },
    "futuro_proyectos": {
        "nombre": "Futuro y Proyectos de Vida",
        "tipo": "factor_protector",
        "descripcion": (
            "Expresiones sobre aspiraciones, metas, sueños y orientación "
            "hacia el proyecto vital personal."
        ),
        "keywords": [
            "futuro", "sueño", "sueños", "soñar", "sonar", "meta", "metas",
            "objetivo", "objetivos", "lograr", "logro", "quiero ser",
            "quiero tener", "quiero vivir", "proyecto", "proyectos",
            "carrera", "profesión", "profesion", "trabajo", "trabajar",
            "crecer", "crecimiento", "superación", "superacion", "mejorar",
            "cambiar", "cambio", "viajar", "viajes", "mundo", "oportunidad",
            "oportunidades", "posibilidad", "esperanza", "ilusión", "ilusion",
            "deseo", "deseos", "aspiración", "aspiracion", "independencia",
            "arriesgar", "arriesgarte", "arriesgarse", "arriesga", "arriesgues",
            "no te rindas", "seguir adelante", "sigue adelante", "adelante",
            "construir", "construirte", "lograrlo", "lo vas a lograr",
            "vas a poder", "podés", "podés lograrlo", "confiá",
            "vengo del futuro", "carta al futuro", "yo del futuro",
            "decirte que", "decirme que", "recordarte", "recordarme",
            "no olvides", "no te olvides", "acordate", "tené en cuenta",
        ],
        "peso": 1.0,
    },
    "identidad_autopercepcion": {
        "nombre": "Identidad y Autopercepción",
        "tipo": "neutro",
        "descripcion": (
            "Narrativas sobre la construcción de la identidad personal, "
            "la autopercepción, el género y la orientación sexual."
        ),
        "keywords": [
            "soy", "me siento", "me llamo", "identidad", "quien soy",
            "quién soy", "persona", "ser", "cuerpo", "imagen", "espejo",
            "género", "genero", "mujer", "hombre", "trans", "gay", "lesbiana",
            "bisexual", "sexualidad", "orientación", "orientacion",
            "diferente", "único", "unico", "especial", "yo mismo", "yo misma",
            "autoconocimiento", "valores", "creencias", "cultura", "origen",
            "raíces", "raices", "tradición", "tradicion", "religión", "religion",
            "fe", "dios", "creer", "espiritualidad",
        ],
        "peso": 1.0,
    },
    "territorio_comunidad": {
        "nombre": "Territorio y Comunidad",
        "tipo": "neutro",
        "descripcion": (
            "Referencias al barrio, la comunidad, el espacio público "
            "y el sentido de pertenencia territorial."
        ),
        "keywords": [
            "barrio", "barrios", "vecino", "vecina", "vecinos", "comunidad",
            "plaza", "calle", "calles", "espacio", "territorio", "lugar",
            "acá", "aca", "aquí", "aqui", "municipio", "provincia",
            "ciudad", "pueblo", "localidad", "zona", "sector", "villa",
            "asentamiento", "cancha", "parque", "club", "centro",
            "organización", "organizacion", "movimiento", "participar",
            "participación", "participacion", "vecindad", "pertenecer",
            "pertenencia", "arraigo", "raíces", "raices",
        ],
        "peso": 1.0,
    },
    "recreacion_cultura": {
        "nombre": "Recreación, Arte y Cultura",
        "tipo": "factor_protector",
        "descripcion": (
            "Alusiones a actividades recreativas, artísticas, deportivas "
            "y expresiones culturales como recursos de bienestar."
        ),
        "keywords": [
            "música", "musica", "bailar", "baile", "cantar", "canto",
            "deporte", "deportes", "fútbol", "futbol", "básquet", "basquet",
            "natación", "natacion", "atletismo", "correr", "jugar", "juego",
            "juegos", "dibujar", "dibujo", "arte", "pintura", "escultura",
            "teatro", "actuación", "actuacion", "cine", "película", "pelicula",
            "series", "libros", "leer", "poesía", "poesia", "escribir",
            "fotografía", "fotografia", "video", "youtube", "redes",
            "instagram", "tiktok", "videojuegos", "hobby", "hobbies",
            "vacaciones", "salida", "paseo", "viaje", "descanso", "tiempo libre",
        ],
        "peso": 1.0,
    },
    "trabajo_economia": {
        "nombre": "Trabajo y Situación Económica",
        "tipo": "estresor",
        "descripcion": (
            "Menciones a la situación laboral y económica familiar, "
            "la precariedad y las necesidades materiales no cubiertas."
        ),
        "keywords": [
            "trabajo", "trabajar", "empleo", "desempleo", "plata", "dinero",
            "plata", "guita", "plata", "sueldo", "salario", "cobrar",
            "ganar", "pobreza", "pobre", "pobres", "hambre", "comer",
            "comida", "necesidad", "necesidades", "falta", "faltar",
            "no alcanza", "no tengo", "sin trabajo", "desocupado",
            "rebuscarla", "changas", "changa", "informal", "precarizado",
            "deuda", "deudas", "plata", "economia", "economía",
        ],
        "peso": 1.1,
    },
    "miedos_ansiedades": {
        "nombre": "Miedos y Ansiedades",
        "tipo": "estresor",
        "descripcion": (
            "Expresiones explícitas de temores, miedos concretos o difusos, "
            "y estados de ansiedad o preocupación crónica."
        ),
        "keywords": [
            "miedo", "miedos", "tener miedo", "miedo a", "asustado",
            "asustada", "susto", "terror", "pánico", "panico", "fobia",
            "preocupación", "preocupacion", "preocupado", "preocupada",
            "angustia", "angustiado", "ansiedad", "ansioso", "ansiosa",
            "nervioso", "nerviosa", "nervios", "tensión", "tension",
            "incertidumbre", "no sé", "no se", "no saber", "qué va a pasar",
            "que va a pasar", "no puedo", "no logro", "bloqueado", "bloqueada",
            "paralizado", "paralizarse", "catástrofe", "catastrofe",
            "presiones", "presión", "presion", "presionado", "presionada",
            "presionarte", "presionarse", "exigencia", "exigencias",
            "preocupes", "preocuparte", "preocuparse", "preocupa",
            "agobio", "agobiado", "agobiante", "abrumado", "abrumada",
            "estresado", "estresada", "estrés", "estres",
            "sobrepasado", "sobrepasada", "no aguanto", "no aguanta",
        ],
        "peso": 1.1,
    },
    "drogas_sustancias": {
        "nombre": "Consumo de Sustancias",
        "tipo": "estresor",
        "descripcion": (
            "Referencias al consumo de alcohol, tabaco u otras sustancias, "
            "ya sea propio, familiar o del entorno cercano."
        ),
        "keywords": [
            "droga", "drogas", "drogarse", "consumir", "consumo",
            "alcohol", "tomar", "borracho", "borracha", "pedo", "fumando",
            "fumar", "faso", "porro", "marihuana", "cocaína", "cocaina",
            "merca", "pasta", "pastillas", "paco", "pegamento", "inhalar",
            "adicción", "adiccion", "adicto", "adicta", "vicios",
            "vicio", "dependencia", "rehabilitación", "rehabilitacion",
        ],
        "peso": 1.2,
    },
}

# Stopwords en español para preprocesamiento
STOPWORDS_ES = {
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con",
    "contra", "cual", "cuando", "de", "del", "desde", "donde", "durante",
    "e", "el", "ella", "ellas", "ellos", "en", "entre", "era", "eras",
    "eramos", "eran", "eres", "es", "esa", "esas", "ese", "eso", "esos",
    "esta", "estaba", "estabas", "estas", "este", "esto", "estos", "estoy",
    "fin", "fue", "fueron", "fui", "fuimos", "ha", "han", "has", "hasta",
    "hay", "he", "hemos", "her", "i", "la", "las", "le", "les", "lo", "los",
    "mas", "más", "me", "mi", "mia", "mías", "mis", "mismo", "mo", "mucho",
    "muchos", "muy", "ni", "no", "nos", "nosotras", "nosotros", "o", "os",
    "otra", "otras", "otro", "otros", "para", "pero", "poco", "por", "porque",
    "que", "qué", "quien", "quienes", "quién", "se", "si", "sí", "sin",
    "sobre", "su", "sus", "también", "tambien", "tan", "tanto", "te", "ti",
    "tiene", "tienen", "tienes", "toda", "todas", "todo", "todos", "tu", "tú",
    "tus", "un", "una", "unas", "uno", "unos", "vos", "y", "ya", "yo",
}
