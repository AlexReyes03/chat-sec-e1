"""
Script de Autenticación con Google OAuth 2.0
============================================

Este script maneja el flujo de autenticación OAuth 2.0 con Google.
Debe ejecutarse al menos una vez antes de usar las funcionalidades
de Google Drive y Gmail.

Uso:
    python authenticate_google.py [opciones]

Opciones:
    --force-new     Forzar nueva autenticación (ignorar token existente)
    --revoke        Revocar acceso actual
    --info          Mostrar información de autenticación actual
"""

import sys
import argparse
from pathlib import Path

from src.config.config import Config
from src.integrations.google import GoogleAuthManager


def print_banner():
    """Imprime el banner"""
    print("\n" + "="*70)
    print("AUTENTICACIÓN CON GOOGLE OAUTH 2.0")
    print("="*70)
    print("\nEste proceso te permitirá autorizar la aplicación para:")
    print("  • Subir archivos a Google Drive")
    print("  • Enviar correos electrónicos con Gmail")
    print("\n" + "="*70 + "\n")


def show_auth_info(auth_manager: GoogleAuthManager):
    """Muestra información de autenticación"""
    print("\n" + "="*70)
    print("INFORMACIÓN DE AUTENTICACIÓN")
    print("="*70)

    if auth_manager.is_authenticated():
        print("\nEstado: AUTENTICADO")

        user_info = auth_manager.get_user_info()
        if user_info.get('authenticated'):
            if 'email' in user_info:
                print(f"\nEmail: {user_info.get('email')}")
                print(f"Nombre: {user_info.get('name', 'N/A')}")
            else:
                print(f"\n{user_info.get('message')}")

        print(f"\nArchivo de token: {Config.GOOGLE_TOKEN_FILE}")
        print(f"Scopes autorizados:")
        for scope in Config.GOOGLE_SCOPES:
            print(f"   - {scope}")

    else:
        print("\nEstado: NO AUTENTICADO")
        print("\nEjecuta este script sin opciones para autenticarte.")

    print("\n" + "="*70 + "\n")


def authenticate(force_new: bool = False):
    """Ejecuta el flujo de autenticación"""
    print_banner()

    try:
        # Verificar que existe el archivo de credenciales
        if not Path(Config.GOOGLE_CREDENTIALS_FILE).exists():
            print("ERROR: Archivo de credenciales no encontrado")
            print(f"\nBusque en: {Config.GOOGLE_CREDENTIALS_FILE}")
            print("\nPara obtener las credenciales:")
            print("  1. Ve a Google Cloud Console")
            print("  2. Crea un proyecto (si no tienes uno)")
            print("  3. Habilita Google Drive API y Gmail API")
            print("  4. Crea credenciales OAuth 2.0")
            print("  5. Descarga el archivo JSON de credenciales")
            print("  6. Guardalo en la raiz de chat-backend/")
            print("\n" + "="*70 + "\n")
            return False

        # Crear gestor de autenticación
        auth_manager = GoogleAuthManager(
            credentials_file=Config.GOOGLE_CREDENTIALS_FILE,
            token_file=Config.GOOGLE_TOKEN_FILE,
            scopes=Config.GOOGLE_SCOPES
        )

        # Si ya está autenticado y no se fuerza nuevo
        if not force_new and auth_manager.is_authenticated():
            print("✓ Ya estás autenticado con Google")
            show_auth_info(auth_manager)
            return True

        # Ejecutar autenticación
        print("Iniciando flujo de autenticación...")
        print("\nSe abrirá tu navegador en unos momentos.")
        print("Por favor autoriza la aplicación para continuar.\n")

        creds = auth_manager.authenticate(force_new=force_new)

        if creds:
            print("\n" + "="*70)
            print("AUTENTICACION EXITOSA")
            print("="*70)
            print("\nLa aplicacion ahora tiene acceso a:")
            print("  - Google Drive - Subir y compartir archivos")
            print("  - Gmail - Enviar correos electronicos")
            print("\nPuedes cerrar la ventana del navegador.")
            print("\nEl token de acceso se guardo en:")
            print(f"  {Config.GOOGLE_TOKEN_FILE}")
            print("\n" + "="*70 + "\n")

            show_auth_info(auth_manager)
            return True
        else:
            print("\n" + "="*70)
            print("AUTENTICACION FALLIDA")
            print("="*70)
            print("\nNo se pudo completar la autenticacion.")
            print("Por favor intenta nuevamente.\n")
            return False

    except Exception as e:
        print(f"\nError durante la autenticacion: {e}\n")
        return False


def revoke_access():
    """Revoca el acceso actual"""
    print("\n" + "="*70)
    print("REVOCAR ACCESO")
    print("="*70)
    print("\nEsto eliminará el token de acceso actual.")
    print("Necesitarás volver a autenticarte para usar Google APIs.\n")

    confirm = input("¿Estás seguro? (s/n): ").strip().lower()

    if confirm != 's':
        print("\nOperación cancelada.\n")
        return

    try:
        auth_manager = GoogleAuthManager(
            credentials_file=Config.GOOGLE_CREDENTIALS_FILE,
            token_file=Config.GOOGLE_TOKEN_FILE,
            scopes=Config.GOOGLE_SCOPES
        )

        if auth_manager.is_authenticated():
            auth_manager.revoke_access()
            print("\nAcceso revocado exitosamente")
        else:
            print("\nNo habia autenticacion activa")

        print("="*70 + "\n")

    except Exception as e:
        print(f"\nError al revocar acceso: {e}\n")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Autenticación con Google OAuth 2.0"
    )
    parser.add_argument(
        '--force-new',
        action='store_true',
        help='Forzar nueva autenticación'
    )
    parser.add_argument(
        '--revoke',
        action='store_true',
        help='Revocar acceso actual'
    )
    parser.add_argument(
        '--info',
        action='store_true',
        help='Mostrar información de autenticación'
    )

    args = parser.parse_args()

    # Crear directorios necesarios
    Config.crear_directorios()

    if args.revoke:
        revoke_access()
    elif args.info:
        print_banner()
        auth_manager = GoogleAuthManager(
            credentials_file=Config.GOOGLE_CREDENTIALS_FILE,
            token_file=Config.GOOGLE_TOKEN_FILE,
            scopes=Config.GOOGLE_SCOPES
        )
        show_auth_info(auth_manager)
    else:
        success = authenticate(force_new=args.force_new)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
