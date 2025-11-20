"""
Gestor de Autenticación con Google OAuth 2.0
============================================

Maneja el flujo de autenticación OAuth 2.0 con Google APIs.
"""

import os
import json
from pathlib import Path
from typing import Optional, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class GoogleAuthManager:
    """
    Gestor de autenticación con Google OAuth 2.0

    Maneja el flujo de autenticación y autorización con Google APIs
    utilizando OAuth 2.0. Soporta almacenamiento y renovación de tokens.
    """

    def __init__(
        self,
        credentials_file: str,
        token_file: str,
        scopes: List[str]
    ):
        """
        Inicializa el gestor de autenticación

        Args:
            credentials_file: Ruta al archivo client_secret.json
            token_file: Ruta donde guardar/cargar el token de acceso
            scopes: Lista de scopes de Google API requeridos
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = scopes
        self.creds: Optional[Credentials] = None

    def authenticate(self, force_new: bool = False) -> Optional[Credentials]:
        """
        Autentica al usuario con Google OAuth 2.0

        Args:
            force_new: Si True, fuerza un nuevo flujo de autenticación

        Returns:
            Credenciales de acceso o None si hay error
        """
        try:
            # Si no se fuerza nuevo login, intentar cargar token existente
            if not force_new and os.path.exists(self.token_file):
                print(f"Cargando token existente desde: {self.token_file}")
                self.creds = Credentials.from_authorized_user_file(
                    self.token_file,
                    self.scopes
                )

            # Si no hay credenciales o no son válidas
            if not self.creds or not self.creds.valid:
                # Si el token está expirado pero es refrescable
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    print("Token expirado. Refrescando...")
                    self.creds.refresh(Request())
                    print("Token refrescado exitosamente")
                else:
                    # Realizar nuevo flujo de autenticación
                    print("Iniciando flujo de autenticación OAuth 2.0...")
                    self.creds = self._perform_auth_flow()

                # Guardar credenciales para uso futuro
                if self.creds:
                    self._save_credentials()

            if self.creds:
                print("Autenticación exitosa con Google APIs")
            else:
                print("Error: No se pudieron obtener credenciales")

            return self.creds

        except Exception as e:
            print(f"Error en autenticación: {e}")
            return None

    def _perform_auth_flow(self) -> Optional[Credentials]:
        """
        Ejecuta el flujo de autenticación OAuth 2.0

        Returns:
            Credenciales obtenidas o None si hay error
        """
        try:
            # Validar que existe el archivo de credenciales
            if not os.path.exists(self.credentials_file):
                raise FileNotFoundError(
                    f"Archivo de credenciales no encontrado: {self.credentials_file}\n"
                    f"Descarga tu archivo client_secret.json desde Google Cloud Console"
                )

            # Crear flujo de autenticación
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file,
                self.scopes
            )

            # Ejecutar servidor local para callback
            # El usuario será redirigido a su navegador para autorizar
            print("\n" + "="*70)
            print("AUTENTICACIÓN CON GOOGLE")
            print("="*70)
            print("Se abrirá tu navegador para que autorices la aplicación.")
            print("Asegúrate de usar la cuenta de Google correcta.")
            print("="*70 + "\n")

            # Usar puerto 8080 (asegúrate de agregarlo en Google Cloud Console)
            creds = flow.run_local_server(
                port=8080,
                success_message='Autenticación exitosa. Puedes cerrar esta ventana.',
                open_browser=True
            )

            return creds

        except Exception as e:
            print(f"Error en flujo de autenticación: {e}")
            return None

    def _save_credentials(self):
        """Guarda las credenciales en archivo"""
        try:
            # Crear directorio si no existe
            Path(self.token_file).parent.mkdir(parents=True, exist_ok=True)

            # Guardar credenciales
            with open(self.token_file, 'w') as token:
                token.write(self.creds.to_json())

            print(f"Credenciales guardadas en: {self.token_file}")

        except Exception as e:
            print(f"Error al guardar credenciales: {e}")

    def revoke_access(self) -> bool:
        """
        Revoca el acceso y elimina el token

        Returns:
            True si se revocó correctamente
        """
        try:
            if self.creds and self.creds.valid:
                # Revocar token
                self.creds.revoke(Request())
                print("Acceso revocado exitosamente")

            # Eliminar archivo de token
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
                print(f"Token eliminado: {self.token_file}")

            self.creds = None
            return True

        except Exception as e:
            print(f"Error al revocar acceso: {e}")
            return False

    def is_authenticated(self) -> bool:
        """
        Verifica si hay credenciales válidas

        Returns:
            True si está autenticado y el token es válido
        """
        return self.creds is not None and self.creds.valid

    def get_credentials(self) -> Optional[Credentials]:
        """
        Obtiene las credenciales actuales

        Returns:
            Credenciales de acceso o None si no está autenticado
        """
        return self.creds

    def get_access_token(self) -> Optional[str]:
        """
        Obtiene el token de acceso actual

        Returns:
            Token de acceso o None si no está autenticado
        """
        if self.creds and self.creds.valid:
            return self.creds.token
        return None

    @staticmethod
    def validate_scopes(required_scopes: List[str], available_scopes: List[str]) -> bool:
        """
        Valida que todos los scopes requeridos estén disponibles

        Args:
            required_scopes: Scopes que se necesitan
            available_scopes: Scopes que se tienen

        Returns:
            True si todos los scopes requeridos están disponibles
        """
        return all(scope in available_scopes for scope in required_scopes)

    def get_user_info(self) -> dict:
        """
        Obtiene información del usuario autenticado

        Returns:
            Diccionario con información del usuario
        """
        if not self.creds:
            return {
                'authenticated': False,
                'message': 'No autenticado'
            }

        try:
            # Decodificar ID token si está disponible
            if hasattr(self.creds, 'id_token') and self.creds.id_token:
                import jwt
                user_info = jwt.decode(
                    self.creds.id_token,
                    options={"verify_signature": False}
                )
                return {
                    'authenticated': True,
                    'email': user_info.get('email'),
                    'name': user_info.get('name'),
                    'picture': user_info.get('picture')
                }
            else:
                return {
                    'authenticated': True,
                    'message': 'Usuario autenticado (información limitada)'
                }

        except Exception as e:
            print(f"Error al obtener información de usuario: {e}")
            return {
                'authenticated': True,
                'message': 'Error al obtener información de usuario'
            }
