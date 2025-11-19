import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


class Config:
    # ========================================
    # SERVIDOR WEBSOCKET (CHAT)
    # ========================================
    SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')
    SERVER_PORT = int(os.getenv('SERVER_PORT', '5555'))
    TIPO_CIFRADO = os.getenv('TIPO_CIFRADO', 'simetrico').lower()

    # ========================================
    # SERVIDOR REST API (FIRMA DIGITAL)
    # ========================================
    API_HOST = os.getenv('API_HOST', 'localhost')
    API_PORT = int(os.getenv('API_PORT', '5000'))
    API_ENV = os.getenv('API_ENV', 'development')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')

    # ========================================
    # CIFRADO SIMETRICO (Fernet)
    # ========================================
    CLAVE_SECRETA = os.getenv('CLAVE_SECRETA', os.getenv('SYMMETRIC_SECRET_KEY', 'mi_clave_super_secreta_2025_chat_grupal'))
    SALT = os.getenv('SALT', os.getenv('SYMMETRIC_SALT', 'salt_estatico_12345')).encode('utf-8')
    PBKDF2_ITERATIONS = int(os.getenv('PBKDF2_ITERATIONS', '100000'))

    # ========================================
    # CIFRADO ASIMETRICO (RSA)
    # ========================================
    CLAVE_PRIVADA_PEM = os.getenv('CLAVE_PRIVADA_PEM', '').encode('utf-8')
    CLAVE_PUBLICA_PEM = os.getenv('CLAVE_PUBLICA_PEM', '').encode('utf-8')
    RSA_KEY_SIZE = int(os.getenv('RSA_KEY_SIZE', '2048'))
    RSA_PRIVATE_KEY_PATH = os.getenv('RSA_PRIVATE_KEY_PATH', 'keys/rsa_private.pem')
    RSA_PUBLIC_KEY_PATH = os.getenv('RSA_PUBLIC_KEY_PATH', 'keys/rsa_public.pem')

    # ========================================
    # SSL/TLS
    # ========================================
    SSL_AUTO_GENERAR = os.getenv('SSL_AUTO_GENERAR', 'True').lower() == 'true'
    SSL_CERT_FILE = os.getenv('SSL_CERT_FILE', os.getenv('SSL_CERT_PATH', 'certs/server.crt'))
    SSL_KEY_FILE = os.getenv('SSL_KEY_FILE', os.getenv('SSL_KEY_PATH', 'certs/server.key'))
    SSL_CERT_VALIDITY_DAYS = int(os.getenv('SSL_CERT_VALIDITY_DAYS', os.getenv('SSL_CERT_DAYS', '365')))

    # ========================================
    # FIRMA DIGITAL
    # ========================================
    SIGNATURE_PRIVATE_KEY_PATH = os.getenv('SIGNATURE_PRIVATE_KEY_PATH', 'keys/signature_private.pem')
    SIGNATURE_PUBLIC_KEY_PATH = os.getenv('SIGNATURE_PUBLIC_KEY_PATH', 'keys/signature_public.pem')
    SIGNATURE_KEY_SIZE = int(os.getenv('SIGNATURE_KEY_SIZE', '2048'))

    SIGNED_DOCUMENTS_PATH = os.getenv('SIGNED_DOCUMENTS_PATH', 'signed_documents')
    TEMP_DOCUMENTS_PATH = os.getenv('TEMP_DOCUMENTS_PATH', 'temp_documents')
    TEMP_FILE_LIFETIME = int(os.getenv('TEMP_FILE_LIFETIME', '3600'))

    # ========================================
    # GOOGLE APIS - OAUTH 2.0
    # ========================================
    GOOGLE_CREDENTIALS_FILE = os.getenv(
        'GOOGLE_CREDENTIALS_FILE',
        'client_secret_244625168933-9kuftvafdqhheerj0r3uddjrcbk1p1dg.apps.googleusercontent.com.json'
    )
    GOOGLE_TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'tokens/google_token.json')
    GOOGLE_SCOPES = os.getenv(
        'GOOGLE_SCOPES',
        'https://www.googleapis.com/auth/drive.file,https://www.googleapis.com/auth/gmail.send'
    ).split(',')
    GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')

    # ========================================
    # EMAIL - NOTIFICACIONES
    # ========================================
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'tu-email@gmail.com')
    EMAIL_SUBJECT_TEMPLATE = os.getenv(
        'EMAIL_SUBJECT_TEMPLATE',
        'Autorización para Firma Digital - {document_name}'
    )
    EMAIL_BODY_TEMPLATE = os.getenv(
        'EMAIL_BODY_TEMPLATE',
        'Se le ha otorgado permiso para firmar el documento: {document_name}'
    )

    # ========================================
    # BASE DE DATOS - MYSQL
    # ========================================
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_NAME = os.getenv('DB_NAME', 'chatsec')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # ========================================
    # SEGURIDAD
    # ========================================
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production-2025')
    JWT_EXPIRATION_MINUTES = int(os.getenv('JWT_EXPIRATION_MINUTES', '60'))
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '10'))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

    @staticmethod
    def validar_configuracion():
        """Valida la configuración del sistema"""
        errores = []

        # Validar TIPO_CIFRADO
        if Config.TIPO_CIFRADO not in ['simetrico', 'asimetrico']:
            errores.append(f"TIPO_CIFRADO invalido: '{Config.TIPO_CIFRADO}'. Debe ser 'simetrico' o 'asimetrico'")

        # Validar cifrado simétrico
        if Config.TIPO_CIFRADO == 'simetrico':
            if not Config.CLAVE_SECRETA or len(Config.CLAVE_SECRETA) < 8:
                errores.append('CLAVE_SECRETA debe tener al menos 8 caracteres')
            if not Config.SALT or len(Config.SALT) < 8:
                errores.append('SALT debe tener al menos 8 caracteres')

        # Validar cifrado asimétrico
        if Config.TIPO_CIFRADO == 'asimetrico':
            if not Config.CLAVE_PRIVADA_PEM or b'BEGIN PRIVATE KEY' not in Config.CLAVE_PRIVADA_PEM:
                errores.append('CLAVE_PRIVADA_PEM no esta configurada correctamente')
            if not Config.CLAVE_PUBLICA_PEM or b'BEGIN PUBLIC KEY' not in Config.CLAVE_PUBLICA_PEM:
                errores.append('CLAVE_PUBLICA_PEM no esta configurada correctamente')

        # Validar puertos
        if Config.SERVER_PORT < 1024 or Config.SERVER_PORT > 65535:
            errores.append(f'SERVER_PORT invalido: {Config.SERVER_PORT}. Debe estar entre 1024 y 65535')
        if Config.API_PORT < 1024 or Config.API_PORT > 65535:
            errores.append(f'API_PORT invalido: {Config.API_PORT}. Debe estar entre 1024 y 65535')

        # Validar archivo de credenciales de Google
        if not os.path.exists(Config.GOOGLE_CREDENTIALS_FILE):
            errores.append(f'Archivo de credenciales de Google no encontrado: {Config.GOOGLE_CREDENTIALS_FILE}')

        # Validar JWT_SECRET_KEY
        if Config.JWT_SECRET_KEY == 'your-secret-key-change-this-in-production-2025' and Config.API_ENV == 'production':
            errores.append('JWT_SECRET_KEY debe cambiarse en producción')

        # Validar EMAIL_FROM
        if '@' not in Config.EMAIL_FROM:
            errores.append(f'EMAIL_FROM invalido: {Config.EMAIL_FROM}. Debe ser un email válido')

        return errores

    @staticmethod
    def mostrar_configuracion():
        """Muestra la configuración actual del sistema"""
        print("\n" + "="*70)
        print("CONFIGURACION DEL SISTEMA")
        print("="*70)

        print("\n[SERVIDOR WEBSOCKET - CHAT]")
        print(f"  Host: {Config.SERVER_HOST}")
        print(f"  Puerto: {Config.SERVER_PORT}")
        print(f"  Tipo de cifrado: {Config.TIPO_CIFRADO}")
        print(f"  SSL auto-generar: {Config.SSL_AUTO_GENERAR}")

        if Config.TIPO_CIFRADO == 'simetrico':
            print(f"  PBKDF2 iteraciones: {Config.PBKDF2_ITERATIONS}")
        else:
            print(f"  RSA key size: {Config.RSA_KEY_SIZE}")

        print("\n[SERVIDOR REST API - FIRMA DIGITAL]")
        print(f"  Host: {Config.API_HOST}")
        print(f"  Puerto: {Config.API_PORT}")
        print(f"  Entorno: {Config.API_ENV}")
        print(f"  CORS origins: {', '.join(Config.CORS_ORIGINS)}")

        print("\n[FIRMA DIGITAL]")
        print(f"  Tamaño de clave: {Config.SIGNATURE_KEY_SIZE} bits")
        print(f"  Documentos firmados: {Config.SIGNED_DOCUMENTS_PATH}")
        print(f"  Documentos temporales: {Config.TEMP_DOCUMENTS_PATH}")

        print("\n[GOOGLE APIS]")
        print(f"  Archivo de credenciales: {Config.GOOGLE_CREDENTIALS_FILE}")
        print(f"  Scopes: {', '.join(Config.GOOGLE_SCOPES)}")
        print(f"  Drive Folder ID: {Config.GOOGLE_DRIVE_FOLDER_ID or '(raíz)'}")

        print("\n[EMAIL]")
        print(f"  Remitente: {Config.EMAIL_FROM}")

        print("\n[SEGURIDAD]")
        print(f"  Tamaño máximo de archivo: {Config.MAX_FILE_SIZE_MB} MB")
        print(f"  Expiración de tokens JWT: {Config.JWT_EXPIRATION_MINUTES} minutos")
        print("="*70)

    @staticmethod
    def crear_directorios():
        """Crea los directorios necesarios si no existen"""
        directorios = [
            'certs',
            'keys',
            'tokens',
            Config.SIGNED_DOCUMENTS_PATH,
            Config.TEMP_DOCUMENTS_PATH
        ]

        for directorio in directorios:
            Path(directorio).mkdir(parents=True, exist_ok=True)

        print("Directorios creados/verificados correctamente")


if __name__ == "__main__":
    print("Validando configuracion...")
    errores = Config.validar_configuracion()

    if errores:
        print("\nErrores encontrados:")
        for error in errores:
            print(f"  - {error}")
    else:
        print("\nConfiguracion valida")
        Config.mostrar_configuracion()


