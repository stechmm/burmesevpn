import os
import json
import secrets
import hashlib
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse

AUTH_FILE = os.path.join(os.path.dirname(__file__), "auth_config.json")

class AuthManager:
    def __init__(self):
        self.auth_file = AUTH_FILE
        self._ensure_initialized()

    def _ensure_initialized(self):
        if not os.path.exists(self.auth_file):
            default_config = {
                "username": "admin",
                "password_hash": self._hash_password("password"),
                "secret_key": secrets.token_hex(32),
                "sessions": []
            }
            with open(self.auth_file, "w") as f:
                json.dump(default_config, f, indent=2)

    def _load_data(self) -> dict:
        if os.path.exists(self.auth_file):
            try:
                with open(self.auth_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        self._ensure_initialized()
        with open(self.auth_file, "r") as f:
            return json.load(f)

    def _save_data(self, data: dict):
        with open(self.auth_file, "w") as f:
            json.dump(data, f, indent=2)

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def authenticate(self, username: str, password: str) -> str:
        """Verify username & password and generate session token"""
        data = self._load_data()
        stored_user = data.get("username", "admin")
        stored_hash = data.get("password_hash", self._hash_password("password"))

        if username.strip() == stored_user and self._hash_password(password) == stored_hash:
            session_token = secrets.token_urlsafe(32)
            if "sessions" not in data:
                data["sessions"] = []
            data["sessions"].append(session_token)
            # Keep max 20 active sessions
            if len(data["sessions"]) > 20:
                data["sessions"] = data["sessions"][-20:]
            self._save_data(data)
            return session_token
        return ""

    def validate_session(self, session_token: str) -> bool:
        """Check if session token is valid"""
        if not session_token:
            return False
        data = self._load_data()
        return session_token in data.get("sessions", [])

    def revoke_session(self, session_token: str):
        data = self._load_data()
        if "sessions" in data and session_token in data["sessions"]:
            data["sessions"].remove(session_token)
            self._save_data(data)

    def update_credentials(self, new_username: str, new_password: str):
        data = self._load_data()
        if new_username:
            data["username"] = new_username.strip()
        if new_password:
            data["password_hash"] = self._hash_password(new_password)
        self._save_data(data)
