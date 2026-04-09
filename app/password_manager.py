<<<<<<< HEAD
# app/password_manager.py
import os
import json
import hashlib
import hmac


class PasswordManager:
    def __init__(self, default_password: str = "letmein"):
        self.default_password = default_password

        # Force storage in %APPDATA%\NovaTurn\password.json
        appdata = os.getenv("APPDATA")
        if not appdata:
            # Fallback: use user home if APPDATA is missing (very rare)
            appdata = os.path.expanduser("~")

        self.config_dir = os.path.join(appdata, "NovaTurn")
        self.path = os.path.join(self.config_dir, "password.json")

        os.makedirs(self.config_dir, exist_ok=True)

        if not os.path.exists(self.path):
            self._write_password(self.default_password)

    def _derive_hash(self, password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100_000,
            dklen=32,
        )

    def _write_password(self, password: str) -> None:
        salt = os.urandom(16)
        pwd_hash = self._derive_hash(password, salt)

        data = {
            "salt": salt.hex(),
            "hash": pwd_hash.hex(),
        }

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _load_data(self):
        if not os.path.exists(self.path):
            return None
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "salt" not in data or "hash" not in data:
                return None
            return data
        except Exception:
            return None

    def verify_password(self, password: str) -> bool:
        data = self._load_data()
        if data is None:
            self._write_password(self.default_password)
            data = self._load_data()
            if data is None:
                return False

        salt = bytes.fromhex(data["salt"])
        stored_hash = bytes.fromhex(data["hash"])
        test_hash = self._derive_hash(password, salt)
        return hmac.compare_digest(test_hash, stored_hash)

    def change_password(self, old_password: str, new_password: str) -> bool:
        if not self.verify_password(old_password):
            return False
        self._write_password(new_password)
        return True

    def reset_to_default(self) -> None:
        self._write_password(self.default_password)

=======
# app/password_manager.py
import os
import json
import hashlib
import hmac


class PasswordManager:
    def __init__(self, default_password: str = "letmein"):
        self.default_password = default_password

        # Force storage in %APPDATA%\NovaTurn\password.json
        appdata = os.getenv("APPDATA")
        if not appdata:
            # Fallback: use user home if APPDATA is missing (very rare)
            appdata = os.path.expanduser("~")

        self.config_dir = os.path.join(appdata, "NovaTurn")
        self.path = os.path.join(self.config_dir, "password.json")

        os.makedirs(self.config_dir, exist_ok=True)

        if not os.path.exists(self.path):
            self._write_password(self.default_password)

    def _derive_hash(self, password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100_000,
            dklen=32,
        )

    def _write_password(self, password: str) -> None:
        salt = os.urandom(16)
        pwd_hash = self._derive_hash(password, salt)

        data = {
            "salt": salt.hex(),
            "hash": pwd_hash.hex(),
        }

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _load_data(self):
        if not os.path.exists(self.path):
            return None
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "salt" not in data or "hash" not in data:
                return None
            return data
        except Exception:
            return None

    def verify_password(self, password: str) -> bool:
        data = self._load_data()
        if data is None:
            self._write_password(self.default_password)
            data = self._load_data()
            if data is None:
                return False

        salt = bytes.fromhex(data["salt"])
        stored_hash = bytes.fromhex(data["hash"])
        test_hash = self._derive_hash(password, salt)
        return hmac.compare_digest(test_hash, stored_hash)

    def change_password(self, old_password: str, new_password: str) -> bool:
        if not self.verify_password(old_password):
            return False
        self._write_password(new_password)
        return True

    def reset_to_default(self) -> None:
        self._write_password(self.default_password)

>>>>>>> be9547aaccb1857afa059ff99cc82f20dba6ff7b
