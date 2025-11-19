"""
Script de Prueba - Google APIs
===============================

ARCHIVO TEMPORAL - BORRAR DESPUÉS DE PRUEBAS

Este script prueba las funcionalidades de Google APIs:
- Autenticación OAuth 2.0
- Google Drive (subir archivos)
- Gmail (enviar correos)

NOTA: Requiere autenticación previa con:
    python authenticate_google.py

Uso:
    python test_google_apis.py
"""

import os
from pathlib import Path
from src.config.config import Config
from src.integrations.google import GoogleAuthManager, GoogleDriveManager, GmailManager


def test_autenticacion():
    """Prueba la autenticación con Google"""
    print("\n" + "="*70)
    print("PRUEBA: AUTENTICACION GOOGLE OAUTH 2.0")
    print("="*70 + "\n")

    try:
        auth_manager = GoogleAuthManager(
            credentials_file=Config.GOOGLE_CREDENTIALS_FILE,
            token_file=Config.GOOGLE_TOKEN_FILE,
            scopes=Config.GOOGLE_SCOPES
        )

        if auth_manager.is_authenticated():
            print("Estado: AUTENTICADO")
            user_info = auth_manager.get_user_info()
            if user_info.get('email'):
                print(f"Email: {user_info['email']}")
                print(f"Nombre: {user_info.get('name', 'N/A')}")
            return True, auth_manager.get_credentials()
        else:
            print("Estado: NO AUTENTICADO")
            print("\nEjecuta primero:")
            print("  python authenticate_google.py")
            return False, None

    except Exception as e:
        print(f"Error: {e}")
        return False, None


def crear_archivo_prueba():
    """Crea un archivo de prueba para subir"""
    Config.crear_directorios()

    archivo_path = Path(Config.TEMP_DOCUMENTS_PATH) / "prueba_drive.txt"

    with open(archivo_path, 'w', encoding='utf-8') as f:
        f.write("Archivo de prueba para Google Drive\n")
        f.write("Este archivo fue creado automaticamente para pruebas.\n")
        f.write("Fecha: 2025-11-19\n")

    print(f"Archivo de prueba creado: {archivo_path}")
    return str(archivo_path)


def test_google_drive(creds):
    """Prueba Google Drive API"""
    print("\n" + "="*70)
    print("PRUEBA: GOOGLE DRIVE API")
    print("="*70 + "\n")

    if not creds:
        print("Error: No hay credenciales")
        return False

    try:
        drive_manager = GoogleDriveManager(creds)

        # Crear archivo de prueba
        archivo_path = crear_archivo_prueba()

        # Subir archivo
        print("\nSubiendo archivo a Google Drive...")
        file_info = drive_manager.upload_file(
            file_path=archivo_path,
            file_name="prueba_drive.txt",
            description="Archivo de prueba creado por test_google_apis.py"
        )

        if file_info:
            print("\nRESULTADO: EXITO")
            print(f"ID del archivo: {file_info['id']}")
            print(f"Nombre: {file_info['name']}")
            print(f"Enlace: {file_info['webViewLink']}")

            # Guardar ID para limpieza posterior
            with open('temp_drive_file_id.txt', 'w') as f:
                f.write(file_info['id'])

            return True, file_info
        else:
            print("\nRESULTADO: ERROR al subir archivo")
            return False, None

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_gmail(creds):
    """Prueba Gmail API"""
    print("\n" + "="*70)
    print("PRUEBA: GMAIL API")
    print("="*70 + "\n")

    if not creds:
        print("Error: No hay credenciales")
        return False

    try:
        gmail_manager = GmailManager(creds)

        # Email de prueba (cambiar por tu email)
        email_to = input("Ingresa tu email para prueba (o Enter para saltar): ").strip()

        if not email_to:
            print("Prueba de Gmail omitida")
            return None

        # Enviar email de prueba
        print(f"\nEnviando email de prueba a {email_to}...")
        success = gmail_manager.send_email(
            to=email_to,
            subject="Prueba de Gmail API",
            body="Este es un correo de prueba enviado desde test_google_apis.py\n\nSi recibes este mensaje, Gmail API funciona correctamente.",
            is_html=False
        )

        if success:
            print("\nRESULTADO: EXITO")
            print("Revisa tu bandeja de entrada")
            return True
        else:
            print("\nRESULTADO: ERROR al enviar email")
            return False

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


def limpiar_archivos_drive():
    """Limpia archivos de prueba en Drive"""
    print("\n" + "="*70)
    print("LIMPIEZA DE ARCHIVOS EN DRIVE")
    print("="*70 + "\n")

    if not os.path.exists('temp_drive_file_id.txt'):
        print("No hay archivos para limpiar")
        return

    try:
        with open('temp_drive_file_id.txt', 'r') as f:
            file_id = f.read().strip()

        # Autenticar
        auth_manager = GoogleAuthManager(
            credentials_file=Config.GOOGLE_CREDENTIALS_FILE,
            token_file=Config.GOOGLE_TOKEN_FILE,
            scopes=Config.GOOGLE_SCOPES
        )

        if not auth_manager.is_authenticated():
            print("Error: No autenticado")
            return

        drive_manager = GoogleDriveManager(auth_manager.get_credentials())

        confirmar = input(f"Eliminar archivo {file_id} de Drive? (s/n): ").lower()

        if confirmar == 's':
            if drive_manager.delete_file(file_id):
                print("Archivo eliminado de Drive")
                os.remove('temp_drive_file_id.txt')
            else:
                print("Error al eliminar archivo")
        else:
            print("Eliminacion cancelada")
            print(f"Para eliminar manualmente, el ID es: {file_id}")

    except Exception as e:
        print(f"Error: {e}")


def main():
    """Función principal de pruebas"""
    print("\n" + "="*70)
    print("PRUEBAS DE GOOGLE APIS")
    print("="*70)

    Config.crear_directorios()

    resultados = {
        'auth': False,
        'drive': False,
        'gmail': None
    }

    try:
        # Test 1: Autenticación
        resultados['auth'], creds = test_autenticacion()

        if not resultados['auth']:
            print("\nError: No autenticado. Abortando pruebas.")
            return

        # Test 2: Google Drive
        drive_success, file_info = test_google_drive(creds)
        resultados['drive'] = drive_success

        # Test 3: Gmail
        resultados['gmail'] = test_gmail(creds)

        # Limpieza
        if drive_success:
            limpiar_archivos_drive()

    except KeyboardInterrupt:
        print("\n\nPruebas interrumpidas por usuario")
    except Exception as e:
        print(f"\nError durante pruebas: {e}")
        import traceback
        traceback.print_exc()

    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE PRUEBAS")
    print("="*70)
    print(f"Autenticacion OAuth 2.0:  {'OK' if resultados['auth'] else 'FAIL'}")
    print(f"Google Drive API:         {'OK' if resultados['drive'] else 'FAIL'}")
    if resultados['gmail'] is not None:
        print(f"Gmail API:                {'OK' if resultados['gmail'] else 'FAIL'}")
    else:
        print(f"Gmail API:                OMITIDO")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
