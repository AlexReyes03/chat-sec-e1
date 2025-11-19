from passlib.context import CryptContext


class PasswordManager:
    """
    Gestor de contraseñas usando BCrypt con salt
    """

    def __init__(self):
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12
        )

    def hash_password(self, password: str) -> str:
        """
        Genera hash de contraseña con BCrypt y salt automático

        Args:
            password: Contraseña en texto plano

        Returns:
            Hash de contraseña
        """
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifica si la contraseña coincide con el hash

        Args:
            plain_password: Contraseña en texto plano
            hashed_password: Hash almacenado

        Returns:
            True si coincide, False si no
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def needs_update(self, hashed_password: str) -> bool:
        """
        Verifica si el hash necesita actualización

        Args:
            hashed_password: Hash almacenado

        Returns:
            True si necesita actualización
        """
        return self.pwd_context.needs_update(hashed_password)
