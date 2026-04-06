"""
Módulo de envíos y territorios · Umbrales
==========================================
Gestión de archivos subidos por usuarios, estados de aprobación
y apertura/cierre de territorios.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

SUBMISSIONS_DIR = Path("data/submissions")
SUBMISSIONS_INDEX = Path("data/submissions_index.json")
TERRITORIES_FILE = Path("data/territories.json")

PROVINCIAS = [
    "Buenos Aires",
    "Catamarca",
    "Chaco",
    "Chubut",
    "Ciudad Autónoma de Buenos Aires (CABA)",
    "Córdoba",
    "Corrientes",
    "Entre Ríos",
    "Formosa",
    "Jujuy",
    "La Pampa",
    "La Rioja",
    "Mendoza",
    "Misiones",
    "Neuquén",
    "Río Negro",
    "Salta",
    "San Juan",
    "San Luis",
    "Santa Cruz",
    "Santa Fe",
    "Santiago del Estero",
    "Tierra del Fuego, Antártida e Islas del Atlántico Sur",
    "Tucumán",
]

ESTADOS = {
    "pendiente": "🟡 Pendiente",
    "aprobado": "🟢 Aprobado",
    "rechazado": "🔴 Rechazado",
    "en_revision": "🔵 En revisión",
}

# ── Submissions ────────────────────────────────────────────────────────────────

def _load_index() -> list:
    if not SUBMISSIONS_INDEX.exists():
        return []
    with open(SUBMISSIONS_INDEX, encoding="utf-8") as f:
        return json.load(f)


def _save_index(data: list) -> None:
    SUBMISSIONS_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with open(SUBMISSIONS_INDEX, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_submission(
    file_bytes: bytes,
    filename: str,
    provincia: str,
    localidad: str,
    taller: str,
    uploaded_by: str,
) -> dict:
    SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stored_name = f"{ts}_{filename}"
    (SUBMISSIONS_DIR / stored_name).write_bytes(file_bytes)

    index = _load_index()
    next_id = (index[-1]["id"] + 1) if index else 1
    entry = {
        "id": next_id,
        "filename_original": filename,
        "filename_stored": stored_name,
        "provincia": provincia,
        "localidad": localidad,
        "taller": taller,
        "uploaded_by": uploaded_by,
        "uploaded_at": datetime.now().isoformat(),
        "estado": "pendiente",
        "nota_admin": "",
    }
    index.append(entry)
    _save_index(index)
    return entry


def get_submissions() -> list:
    return _load_index()


def get_submissions_by_user(username: str) -> list:
    return [s for s in _load_index() if s["uploaded_by"] == username]


def update_submission(submission_id: int, estado: str, nota: str = "") -> None:
    index = _load_index()
    for entry in index:
        if entry["id"] == submission_id:
            entry["estado"] = estado
            entry["nota_admin"] = nota
            entry["updated_at"] = datetime.now().isoformat()
    _save_index(index)


def get_submission_bytes(filename_stored: str) -> Optional[bytes]:
    p = SUBMISSIONS_DIR / filename_stored
    return p.read_bytes() if p.exists() else None


# ── Territories ────────────────────────────────────────────────────────────────

def _load_territories() -> dict:
    if not TERRITORIES_FILE.exists():
        return {}
    with open(TERRITORIES_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_territories(data: dict) -> None:
    TERRITORIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TERRITORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_territories() -> dict:
    return _load_territories()


def is_territory_open(provincia: str, localidad: str) -> bool:
    """Retorna True si el territorio acepta envíos (abierto por defecto)."""
    t = _load_territories()
    key = f"{provincia}|{localidad}"
    return t.get(key, {}).get("abierto", True)


def set_territory(
    provincia: str, localidad: str, abierto: bool, nota: str = ""
) -> None:
    t = _load_territories()
    key = f"{provincia}|{localidad}"
    t[key] = {
        "provincia": provincia,
        "localidad": localidad,
        "abierto": abierto,
        "nota": nota,
        "updated_at": datetime.now().isoformat(),
    }
    _save_territories(t)


def delete_territory(provincia: str, localidad: str) -> None:
    t = _load_territories()
    key = f"{provincia}|{localidad}"
    t.pop(key, None)
    _save_territories(t)
