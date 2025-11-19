"""
Gestor de Google Drive
======================

Maneja operaciones con Google Drive API para subir,
descargar y gestionar archivos.
"""

import os
import mimetypes
from typing import Optional, List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials


class GoogleDriveManager:
    """
    Gestor de operaciones con Google Drive

    Permite subir archivos, crear carpetas y gestionar permisos
    en Google Drive.
    """

    def __init__(self, credentials: Credentials):
        """
        Inicializa el gestor de Google Drive

        Args:
            credentials: Credenciales de Google OAuth 2.0
        """
        self.credentials = credentials
        self.service = None
        self._build_service()

    def _build_service(self):
        """Construye el servicio de Google Drive API"""
        try:
            self.service = build('drive', 'v3', credentials=self.credentials)
            print("Servicio de Google Drive inicializado")
        except Exception as e:
            print(f"Error al inicializar servicio de Drive: {e}")
            raise

    def upload_file(
        self,
        file_path: str,
        folder_id: Optional[str] = None,
        file_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sube un archivo a Google Drive

        Args:
            file_path: Ruta al archivo local
            folder_id: ID de la carpeta de destino (None = raíz)
            file_name: Nombre del archivo en Drive (None = usar nombre original)
            description: Descripción del archivo

        Returns:
            Diccionario con información del archivo subido o None si hay error
        """
        try:
            # Validar que el archivo existe
            if not os.path.exists(file_path):
                print(f"Error: Archivo no encontrado: {file_path}")
                return None

            # Determinar nombre del archivo
            if not file_name:
                file_name = os.path.basename(file_path)

            # Detectar tipo MIME
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'

            # Metadatos del archivo
            file_metadata = {
                'name': file_name,
            }

            if description:
                file_metadata['description'] = description

            if folder_id:
                file_metadata['parents'] = [folder_id]

            # Crear media upload
            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True
            )

            # Subir archivo
            print(f"Subiendo archivo: {file_name} ({mime_type})")

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink, size, mimeType, createdTime'
            ).execute()

            print(f"Archivo subido exitosamente:")
            print(f"  ID: {file.get('id')}")
            print(f"  Nombre: {file.get('name')}")
            print(f"  Enlace: {file.get('webViewLink')}")

            return file

        except HttpError as error:
            print(f"Error HTTP al subir archivo: {error}")
            return None
        except Exception as e:
            print(f"Error al subir archivo: {e}")
            return None

    def create_folder(
        self,
        folder_name: str,
        parent_folder_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Crea una carpeta en Google Drive

        Args:
            folder_name: Nombre de la carpeta
            parent_folder_id: ID de la carpeta padre (None = raíz)

        Returns:
            ID de la carpeta creada o None si hay error
        """
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]

            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink'
            ).execute()

            print(f"Carpeta creada:")
            print(f"  ID: {folder.get('id')}")
            print(f"  Nombre: {folder.get('name')}")
            print(f"  Enlace: {folder.get('webViewLink')}")

            return folder.get('id')

        except HttpError as error:
            print(f"Error HTTP al crear carpeta: {error}")
            return None
        except Exception as e:
            print(f"Error al crear carpeta: {e}")
            return None

    def share_file(
        self,
        file_id: str,
        email: str,
        role: str = 'reader',
        notify: bool = True
    ) -> bool:
        """
        Comparte un archivo con un usuario específico

        Args:
            file_id: ID del archivo en Drive
            email: Email del usuario con quien compartir
            role: Rol del usuario ('reader', 'writer', 'commenter')
            notify: Si se debe enviar notificación por email

        Returns:
            True si se compartió exitosamente
        """
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }

            self.service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=notify,
                fields='id'
            ).execute()

            print(f"Archivo compartido con {email} (rol: {role})")
            return True

        except HttpError as error:
            print(f"Error HTTP al compartir archivo: {error}")
            return False
        except Exception as e:
            print(f"Error al compartir archivo: {e}")
            return False

    def make_file_public(self, file_id: str) -> Optional[str]:
        """
        Hace un archivo público (cualquiera con el enlace puede verlo)

        Args:
            file_id: ID del archivo en Drive

        Returns:
            URL pública del archivo o None si hay error
        """
        try:
            # Crear permiso público
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }

            self.service.permissions().create(
                fileId=file_id,
                body=permission,
                fields='id'
            ).execute()

            # Obtener enlace público
            file = self.service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()

            public_url = file.get('webViewLink')
            print(f"Archivo ahora es público: {public_url}")

            return public_url

        except HttpError as error:
            print(f"Error HTTP al hacer archivo público: {error}")
            return None
        except Exception as e:
            print(f"Error al hacer archivo público: {e}")
            return None

    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un archivo

        Args:
            file_id: ID del archivo en Drive

        Returns:
            Diccionario con información del archivo o None si hay error
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime, modifiedTime, webViewLink, owners'
            ).execute()

            return file

        except HttpError as error:
            print(f"Error HTTP al obtener información: {error}")
            return None
        except Exception as e:
            print(f"Error al obtener información: {e}")
            return None

    def list_files(
        self,
        folder_id: Optional[str] = None,
        page_size: int = 10,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista archivos en Drive

        Args:
            folder_id: ID de carpeta (None = todos los archivos)
            page_size: Número de resultados por página
            query: Query personalizado de búsqueda

        Returns:
            Lista de archivos
        """
        try:
            # Construir query
            if query:
                search_query = query
            elif folder_id:
                search_query = f"'{folder_id}' in parents"
            else:
                search_query = None

            # Ejecutar búsqueda
            results = self.service.files().list(
                pageSize=page_size,
                q=search_query,
                fields="files(id, name, mimeType, size, createdTime, webViewLink)"
            ).execute()

            files = results.get('files', [])

            if not files:
                print('No se encontraron archivos.')
            else:
                print(f'Se encontraron {len(files)} archivos:')
                for file in files:
                    print(f"  - {file.get('name')} ({file.get('id')})")

            return files

        except HttpError as error:
            print(f"Error HTTP al listar archivos: {error}")
            return []
        except Exception as e:
            print(f"Error al listar archivos: {e}")
            return []

    def delete_file(self, file_id: str) -> bool:
        """
        Elimina un archivo de Drive

        Args:
            file_id: ID del archivo a eliminar

        Returns:
            True si se eliminó exitosamente
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            print(f"Archivo {file_id} eliminado")
            return True

        except HttpError as error:
            print(f"Error HTTP al eliminar archivo: {error}")
            return False
        except Exception as e:
            print(f"Error al eliminar archivo: {e}")
            return False

    def upload_with_permissions(
        self,
        file_path: str,
        authorized_emails: List[str],
        folder_id: Optional[str] = None,
        role: str = 'writer'
    ) -> Optional[Dict[str, Any]]:
        """
        Sube un archivo y lo comparte con usuarios específicos

        Args:
            file_path: Ruta al archivo local
            authorized_emails: Lista de emails autorizados
            folder_id: ID de carpeta de destino
            role: Rol para los usuarios autorizados

        Returns:
            Información del archivo subido
        """
        # Subir archivo
        file_info = self.upload_file(file_path, folder_id=folder_id)

        if not file_info:
            return None

        file_id = file_info.get('id')

        # Compartir con cada usuario autorizado
        print(f"\nCompartiendo archivo con {len(authorized_emails)} usuarios...")
        for email in authorized_emails:
            self.share_file(file_id, email, role=role, notify=True)

        return file_info
