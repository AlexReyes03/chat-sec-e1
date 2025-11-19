from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from src.config.config import Config


class JWTManager:
    """
    Gestor de tokens JWT para autenticación
    """

    def __init__(self):
        self.secret_key = Config.JWT_SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_hours = 24

    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crea un token JWT

        Args:
            data: Datos a incluir en el token (user_id, email, etc.)
            expires_delta: Tiempo de expiración personalizado

        Returns:
            Token JWT
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=self.access_token_expire_hours)

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verifica y decodifica un token JWT

        Args:
            token: Token JWT

        Returns:
            Payload del token si es válido, None si no
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload

        except JWTError:
            return None

    def decode_token(self, token: str) -> Optional[Dict]:
        """
        Decodifica un token sin verificar (solo para debugging)

        Args:
            token: Token JWT

        Returns:
            Payload del token
        """
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_signature": False})
        except:
            return None
