import hashlib
from utils.config import Config

API_SALT = Config.API_SALT
PASSWORD_SALT = Config.PASSWORD_SALT

def api_hash_key(key: str) -> str:
    return hashlib.sha256((API_SALT + key).encode("utf-8")).hexdigest()

def password_hash_key(key: str) -> str:
    return hashlib.sha256((PASSWORD_SALT + key).encode("utf-8")).hexdigest()