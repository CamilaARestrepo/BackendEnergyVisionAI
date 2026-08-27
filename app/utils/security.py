import os
from cryptography.fernet import Fernet
from app.config import settings

class SecurityService:
    def __init__(self):
        self.secret_path = settings.SECRET_KEY_PATH
        self._fernet = self._initialize_fernet()

    def _initialize_fernet(self) -> Fernet:
        """Carga la clave desde el archivo o genera una nueva si no existe."""
        if not os.path.exists(self.secret_path):
            os.makedirs(os.path.dirname(self.secret_path), exist_ok=True)
            key = Fernet.generate_key()
            with open(self.secret_path, "wb") as f:
                f.write(key)
        else:
            with open(self.secret_path, "rb") as f:
                key = f.read()
        
        return Fernet(key)

    def encrypt_api_key(self, api_key: str) -> str:
        """Cifra la clave de API y retorna un formarto seguro decodeado utf-8."""
        if not api_key:
            return api_key
        return self._fernet.encrypt(api_key.encode("utf-8")).decode("utf-8")

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Descifra el secreto almacenado."""
        if not encrypted_key:
            return encrypted_key
        return self._fernet.decrypt(encrypted_key.encode("utf-8")).decode("utf-8")

security_service = SecurityService()
