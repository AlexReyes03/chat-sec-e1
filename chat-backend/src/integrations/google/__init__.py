"""
Módulo de Integración con Google APIs
======================================

Implementa la integración con servicios de Google:
- OAuth 2.0: Autenticación y autorización
- Google Drive API: Subida y gestión de archivos
- Gmail API: Envío de correos electrónicos

Componentes principales:
- GoogleAuthManager: Gestión de autenticación OAuth 2.0
- GoogleDriveManager: Operaciones con Google Drive
- GmailManager: Envío de correos electrónicos
"""

from .auth_manager import GoogleAuthManager
from .drive_manager import GoogleDriveManager
from .gmail_manager import GmailManager

__all__ = [
    'GoogleAuthManager',
    'GoogleDriveManager',
    'GmailManager'
]
