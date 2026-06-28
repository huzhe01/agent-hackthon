"""Lightweight Agent Mode demo authentication.

This is intentionally an app-level login for the hackathon workbench. It keeps
the Supabase service key on the server side and only gives the frontend a user
identity plus tenant key for loading persisted budget-project history.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"
DEFAULT_STORE_PATH = Path(__file__).resolve().parent / "data" / "agent_users.json"
_USERNAME_PATTERN = re.compile(r"[^a-zA-Z0-9_-]+")


def sanitize_tenant_key(value: Optional[str]) -> str:
    cleaned = _USERNAME_PATTERN.sub("-", str(value or DEFAULT_USERNAME).strip().lower()).strip("-")
    return cleaned or DEFAULT_USERNAME


def _password_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _store_path(path: Optional[str] = None) -> Path:
    return Path(path or os.environ.get("AGENT_AUTH_STORE_PATH") or DEFAULT_STORE_PATH)


def _default_user() -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": "user-admin",
        "username": DEFAULT_USERNAME,
        "display_name": DEFAULT_USERNAME,
        "role": "admin",
        "tenant_key": DEFAULT_USERNAME,
        "password_hash": _password_hash(DEFAULT_PASSWORD),
        "created_at": now,
        "updated_at": now,
    }


def _read_store(path: Optional[str] = None) -> Dict[str, Any]:
    store_path = _store_path(path)
    if not store_path.exists():
        return {"users": [_default_user()]}
    try:
        payload = json.loads(store_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = {"users": []}
    users = payload.get("users")
    if not isinstance(users, list):
        users = []
    if not any(user.get("username") == DEFAULT_USERNAME for user in users):
        users.insert(0, _default_user())
    payload["users"] = users
    return payload


def _write_store(payload: Dict[str, Any], path: Optional[str] = None) -> None:
    store_path = _store_path(path)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_user_store(path: Optional[str] = None) -> Dict[str, Any]:
    payload = _read_store(path)
    _write_store(payload, path)
    return payload


def _public_user(user: Dict[str, Any]) -> Dict[str, Any]:
    public = deepcopy(user)
    public.pop("password_hash", None)
    public.pop("password", None)
    public["tenant_key"] = sanitize_tenant_key(public.get("tenant_key") or public.get("username"))
    return public


def authenticate_user(username: str, password: str, path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    payload = ensure_user_store(path)
    normalized = str(username or "").strip().lower()
    supplied_hash = _password_hash(str(password or ""))
    for user in payload.get("users", []):
        if str(user.get("username", "")).strip().lower() == normalized and user.get("password_hash") == supplied_hash:
            return _public_user(user)
    return None
