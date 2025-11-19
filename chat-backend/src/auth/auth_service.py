from typing import Optional, Tuple
from sqlalchemy.orm import Session
from src.database.models import Usuario
from src.auth.password_manager import PasswordManager
from src.auth.jwt_manager import JWTManager


class AuthService:
    """
    Servicio de autenticación
    """

    def __init__(self):
        self.password_manager = PasswordManager()
        self.jwt_manager = JWTManager()

    def register_user(self, db: Session, email: str, password: str) -> Tuple[bool, str, Optional[Usuario]]:
        """
        Registra un nuevo usuario con credenciales

        Args:
            db: Sesión de base de datos
            email: Email del usuario
            password: Contraseña en texto plano

        Returns:
            (success, message, usuario)
        """
        existing_user = db.query(Usuario).filter(Usuario.email == email).first()

        if existing_user:
            return False, "El email ya está registrado", None

        password_hash = self.password_manager.hash_password(password)

        new_user = Usuario(
            email=email,
            password_hash=password_hash
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return True, "Usuario registrado exitosamente", new_user

    def login_with_credentials(self, db: Session, email: str, password: str) -> Tuple[bool, str, Optional[str], Optional[Usuario]]:
        """
        Login con email y contraseña

        Args:
            db: Sesión de base de datos
            email: Email del usuario
            password: Contraseña en texto plano

        Returns:
            (success, message, token, usuario)
        """
        user = db.query(Usuario).filter(Usuario.email == email).first()

        if not user:
            return False, "Email no registrado", None, None

        if not user.password_hash:
            return False, "Esta cuenta solo permite login con Google", None, None

        if not self.password_manager.verify_password(password, user.password_hash):
            return False, "Contraseña incorrecta", None, None

        token = self.jwt_manager.create_access_token(
            data={"user_id": user.id, "email": user.email}
        )

        return True, "Login exitoso", token, user

    def login_with_google(self, db: Session, email: str, google_id: str, nombre_google: str, foto_perfil_url: Optional[str] = None) -> Tuple[bool, str, Optional[str], Optional[Usuario]]:
        """
        Login o registro con Google OAuth

        Args:
            db: Sesión de base de datos
            email: Email de Google
            google_id: ID de Google
            nombre_google: Nombre completo de Google
            foto_perfil_url: URL de foto de perfil

        Returns:
            (success, message, token, usuario)
        """
        user = db.query(Usuario).filter(Usuario.email == email).first()

        if user:
            if user.google_id is None:
                user.google_id = google_id
                user.nombre_google = nombre_google
                if foto_perfil_url:
                    user.foto_perfil_url = foto_perfil_url
                db.commit()
                db.refresh(user)

        else:
            user = Usuario(
                email=email,
                google_id=google_id,
                nombre_google=nombre_google,
                foto_perfil_url=foto_perfil_url
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        token = self.jwt_manager.create_access_token(
            data={"user_id": user.id, "email": user.email}
        )

        return True, "Login exitoso", token, user

    def verify_token(self, token: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Verifica un token JWT

        Args:
            token: Token JWT

        Returns:
            (valid, user_id, email)
        """
        payload = self.jwt_manager.verify_token(token)

        if not payload:
            return False, None, None

        user_id = payload.get("user_id")
        email = payload.get("email")

        return True, user_id, email

    def update_apodo(self, db: Session, user_id: int, apodo: str) -> Tuple[bool, str]:
        """
        Actualiza el apodo del usuario

        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            apodo: Apodo nuevo

        Returns:
            (success, message)
        """
        user = db.query(Usuario).filter(Usuario.id == user_id).first()

        if not user:
            return False, "Usuario no encontrado"

        if len(apodo) < 2 or len(apodo) > 50:
            return False, "El apodo debe tener entre 2 y 50 caracteres"

        user.apodo = apodo
        db.commit()

        return True, "Apodo actualizado exitosamente"

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[Usuario]:
        """
        Obtiene un usuario por ID

        Args:
            db: Sesión de base de datos
            user_id: ID del usuario

        Returns:
            Usuario o None
        """
        return db.query(Usuario).filter(Usuario.id == user_id).first()

    def get_user_by_email(self, db: Session, email: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por email

        Args:
            db: Sesión de base de datos
            email: Email del usuario

        Returns:
            Usuario o None
        """
        return db.query(Usuario).filter(Usuario.email == email).first()
