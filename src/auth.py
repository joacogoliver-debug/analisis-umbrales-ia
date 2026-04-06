"""
Módulo de autenticación · Umbrales
===================================
Gestión de usuarios y sesiones con almacenamiento en JSON.
Contraseñas hasheadas con SHA-256.
"""

import hashlib
import json
from pathlib import Path
from typing import Optional

CREDENTIALS_FILE = Path("data/credentials.json")

_DEFAULT_CREDENTIALS = {
    "users": {
        "admin": {
            "password": hashlib.sha256("umbrales2024".encode()).hexdigest(),
            "role": "admin",
            "nombre": "Administrador",
        }
    }
}


def _load() -> dict:
    if not CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _save(_DEFAULT_CREDENTIALS)
        return _DEFAULT_CREDENTIALS
    with open(CREDENTIALS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_login(username: str, password: str) -> Optional[dict]:
    """Verifica credenciales. Retorna dict con username/role/nombre o None."""
    creds = _load()
    user = creds["users"].get(username)
    if user and user["password"] == hash_pw(password):
        return {
            "username": username,
            "role": user["role"],
            "nombre": user["nombre"],
        }
    return None


def get_users() -> dict:
    return _load()["users"]


def add_user(username: str, password: str, role: str, nombre: str) -> None:
    data = _load()
    data["users"][username] = {
        "password": hash_pw(password),
        "role": role,
        "nombre": nombre,
    }
    _save(data)


def delete_user(username: str) -> None:
    data = _load()
    data["users"].pop(username, None)
    _save(data)


def change_password(username: str, new_password: str) -> None:
    data = _load()
    if username in data["users"]:
        data["users"][username]["password"] = hash_pw(new_password)
        _save(data)
