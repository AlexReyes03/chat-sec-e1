"""
Servidor REST API - FastAPI
============================

Servidor REST API para operaciones de firma digital y Google APIs.
Proporciona endpoints para el frontend React.

Endpoints principales:
- POST /api/auth/google - Autenticación con Google OAuth 2.0
- POST /api/sign/upload - Subir documento para firma
- POST /api/sign/document - Firmar documento
- GET /api/sign/verify/{file_id} - Verificar firma
- POST /api/drive/upload - Subir a Google Drive
- POST /api/gmail/send - Enviar correo de autorización
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, EmailStr
import uvicorn

from src.config.config import Config
from src.signature import DocumentSigner, SignatureVerifier, SignatureRequest, VerificationRequest
from src.integrations.google import GoogleAuthManager, GoogleDriveManager, GmailManager


# ============================================================================
# MODELOS DE DATOS (Pydantic)
# ============================================================================

class SignDocumentRequest(BaseModel):
    """Petición para firmar un documento"""
    file_id: str  # ID del archivo temporal
    signer_name: str
    signer_email: EmailStr


class UploadToDriveRequest(BaseModel):
    """Petición para subir archivo a Google Drive"""
    file_id: str
    authorized_emails: List[EmailStr]
    folder_id: Optional[str] = None


class SendAuthorizationRequest(BaseModel):
    """Petición para enviar correo de autorización"""
    recipients: List[EmailStr]
    document_name: str
    document_link: str
    signer_name: str
    additional_info: Optional[str] = None


class AuthStatusResponse(BaseModel):
    """Respuesta del estado de autenticación"""
    authenticated: bool
    message: str
    user_info: Optional[dict] = None


# ============================================================================
# INICIALIZACIÓN DE LA APP
# ============================================================================

app = FastAPI(
    title="API de Firma Digital",
    description="API REST para firma digital de documentos y integración con Google APIs",
    version="5.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ESTADO GLOBAL DE LA APLICACIÓN
# ============================================================================

class AppState:
    """Estado global de la aplicación"""
    def __init__(self):
        self.google_auth: Optional[GoogleAuthManager] = None
        self.drive_manager: Optional[GoogleDriveManager] = None
        self.gmail_manager: Optional[GmailManager] = None
        self.document_signer: Optional[DocumentSigner] = None
        self.signature_verifier: Optional[SignatureVerifier] = None

    def initialize(self):
        """Inicializa los servicios de la aplicación"""
        try:
            # Crear directorios necesarios
            Config.crear_directorios()

            # Inicializar firmador de documentos
            print("\nInicializando firmador de documentos...")
            self.document_signer = DocumentSigner(
                private_key_path=Config.SIGNATURE_PRIVATE_KEY_PATH,
                public_key_path=Config.SIGNATURE_PUBLIC_KEY_PATH
            )

            # Inicializar verificador de firmas
            print("Inicializando verificador de firmas...")
            self.signature_verifier = SignatureVerifier(
                public_key_path=Config.SIGNATURE_PUBLIC_KEY_PATH
            )

            # Inicializar autenticación de Google
            print("Inicializando autenticación con Google...")
            self.google_auth = GoogleAuthManager(
                credentials_file=Config.GOOGLE_CREDENTIALS_FILE,
                token_file=Config.GOOGLE_TOKEN_FILE,
                scopes=Config.GOOGLE_SCOPES
            )

            print("\nServicios inicializados correctamente")

        except Exception as e:
            print(f"\nError al inicializar servicios: {e}")
            raise

    def ensure_google_authenticated(self):
        """Asegura que hay autenticación con Google"""
        if not self.google_auth:
            raise HTTPException(status_code=500, detail="Gestor de autenticación no inicializado")

        # Autenticar si es necesario
        if not self.google_auth.is_authenticated():
            creds = self.google_auth.authenticate()
            if not creds:
                raise HTTPException(
                    status_code=401,
                    detail="No se pudo autenticar con Google. Ejecuta el flujo OAuth primero."
                )

            # Inicializar servicios de Google
            self.drive_manager = GoogleDriveManager(creds)
            self.gmail_manager = GmailManager(creds)

        return True


# Instancia global del estado
state = AppState()


# ============================================================================
# EVENTOS DE INICIO/CIERRE
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    print("\n" + "="*70)
    print("INICIANDO SERVIDOR REST API - FIRMA DIGITAL")
    print("="*70)
    Config.mostrar_configuracion()
    print("\nInicializando servicios...")
    state.initialize()
    print("\n" + "="*70)
    print(f"Servidor REST API iniciado en http://{Config.API_HOST}:{Config.API_PORT}")
    print("Documentación interactiva: http://{}:{}/docs".format(Config.API_HOST, Config.API_PORT))
    print("="*70 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    print("\nCerrando servidor REST API...")


# ============================================================================
# ENDPOINTS - AUTENTICACIÓN
# ============================================================================

@app.get("/api/auth/status", response_model=AuthStatusResponse)
async def get_auth_status():
    """Obtiene el estado de autenticación con Google"""
    try:
        if not state.google_auth:
            return AuthStatusResponse(
                authenticated=False,
                message="Gestor de autenticación no inicializado"
            )

        is_auth = state.google_auth.is_authenticated()

        if is_auth:
            user_info = state.google_auth.get_user_info()
            return AuthStatusResponse(
                authenticated=True,
                message="Autenticado con Google",
                user_info=user_info
            )
        else:
            return AuthStatusResponse(
                authenticated=False,
                message="No autenticado con Google"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/google/initiate")
async def initiate_google_auth():
    """
    Inicia el flujo de autenticación OAuth 2.0 con Google.
    NOTA: Este endpoint debe ser llamado desde un entorno donde se pueda abrir un navegador.
    """
    try:
        if not state.google_auth:
            raise HTTPException(status_code=500, detail="Gestor de autenticación no inicializado")

        # Autenticar
        creds = state.google_auth.authenticate(force_new=False)

        if creds:
            # Inicializar servicios de Google
            state.drive_manager = GoogleDriveManager(creds)
            state.gmail_manager = GmailManager(creds)

            return {
                "success": True,
                "message": "Autenticación exitosa con Google",
                "user_info": state.google_auth.get_user_info()
            }
        else:
            raise HTTPException(status_code=401, detail="Fallo en la autenticación")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - FIRMA DE DOCUMENTOS
# ============================================================================

@app.post("/api/sign/upload")
async def upload_document_for_signature(file: UploadFile = File(...)):
    """Sube un documento para firma (almacenamiento temporal)"""
    try:
        # Validar tipo de archivo
        allowed_extensions = ['.txt', '.pdf', '.zip']
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no soportado. Solo se permiten: {', '.join(allowed_extensions)}"
            )

        # Validar tamaño
        content = await file.read()
        if len(content) > Config.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"El archivo excede el tamaño máximo permitido ({Config.MAX_FILE_SIZE_MB} MB)"
            )

        # Generar ID único para el archivo
        file_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"

        # Guardar archivo temporal
        temp_path = Path(Config.TEMP_DOCUMENTS_PATH) / file_id
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        with open(temp_path, 'wb') as f:
            f.write(content)

        return {
            "success": True,
            "message": "Archivo subido exitosamente",
            "file_id": file_id,
            "filename": file.filename,
            "size": len(content),
            "temp_path": str(temp_path)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sign/document")
async def sign_document(request: SignDocumentRequest):
    """Firma un documento previamente subido"""
    try:
        if not state.document_signer:
            raise HTTPException(status_code=500, detail="Firmador no inicializado")

        # Obtener ruta del archivo temporal
        temp_path = Path(Config.TEMP_DOCUMENTS_PATH) / request.file_id

        if not temp_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Archivo no encontrado. Por favor sube el archivo primero."
            )

        # Crear petición de firma
        sign_request = SignatureRequest(
            document_path=str(temp_path),
            signer_name=request.signer_name,
            signer_email=request.signer_email
        )

        # Firmar documento
        result = state.document_signer.sign_document(sign_request)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)

        # Mover documento firmado a carpeta de firmados
        signed_filename = Path(request.file_id).stem + "_signed" + Path(request.file_id).suffix
        signed_path = Path(Config.SIGNED_DOCUMENTS_PATH) / signed_filename
        signed_path.parent.mkdir(parents=True, exist_ok=True)

        # Copiar archivo original a carpeta de firmados
        shutil.copy2(temp_path, signed_path)

        # Copiar archivo de firma
        signature_file = f"{temp_path}.sig"
        signed_signature_file = f"{signed_path}.sig"
        if os.path.exists(signature_file):
            shutil.copy2(signature_file, signed_signature_file)

        return {
            "success": True,
            "message": "Documento firmado exitosamente",
            "signed_file_id": signed_filename,
            "metadata": result.metadata.to_dict() if result.metadata else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sign/verify/{file_id}")
async def verify_signature(file_id: str):
    """Verifica la firma de un documento"""
    try:
        if not state.signature_verifier:
            raise HTTPException(status_code=500, detail="Verificador no inicializado")

        # Buscar documento en carpeta de firmados
        signed_path = Path(Config.SIGNED_DOCUMENTS_PATH) / file_id

        if not signed_path.exists():
            raise HTTPException(status_code=404, detail="Documento firmado no encontrado")

        # Crear petición de verificación
        verify_request = VerificationRequest(
            signed_document_path=str(signed_path)
        )

        # Verificar firma
        result = state.signature_verifier.verify_document(verify_request)

        return {
            "success": result.success,
            "status": result.status.value if result.status else None,
            "message": result.message,
            "metadata": result.metadata.to_dict() if result.metadata else None,
            "error": result.error
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sign/download/{file_id}")
async def download_signed_document(file_id: str):
    """Descarga un documento firmado"""
    try:
        signed_path = Path(Config.SIGNED_DOCUMENTS_PATH) / file_id

        if not signed_path.exists():
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        return FileResponse(
            path=signed_path,
            filename=file_id,
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - GOOGLE DRIVE
# ============================================================================

@app.post("/api/drive/upload")
async def upload_to_drive(request: UploadToDriveRequest):
    """Sube un documento firmado a Google Drive y lo comparte con usuarios autorizados"""
    try:
        # Asegurar autenticación
        state.ensure_google_authenticated()

        # Obtener archivo firmado
        signed_path = Path(Config.SIGNED_DOCUMENTS_PATH) / request.file_id

        if not signed_path.exists():
            raise HTTPException(status_code=404, detail="Documento firmado no encontrado")

        # Subir a Drive con permisos
        file_info = state.drive_manager.upload_with_permissions(
            file_path=str(signed_path),
            authorized_emails=request.authorized_emails,
            folder_id=request.folder_id or Config.GOOGLE_DRIVE_FOLDER_ID,
            role='writer'  # Permite firmar
        )

        if not file_info:
            raise HTTPException(status_code=500, detail="Error al subir archivo a Drive")

        return {
            "success": True,
            "message": "Archivo subido a Google Drive exitosamente",
            "file_info": file_info,
            "shared_with": request.authorized_emails
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - GMAIL
# ============================================================================

@app.post("/api/gmail/send-authorization")
async def send_authorization_email(request: SendAuthorizationRequest):
    """Envía correos de autorización para firma"""
    try:
        # Asegurar autenticación
        state.ensure_google_authenticated()

        # Enviar correos en batch
        results = state.gmail_manager.send_batch_authorization_emails(
            recipients=request.recipients,
            document_name=request.document_name,
            document_link=request.document_link,
            signer_name=request.signer_name,
            from_email=Config.EMAIL_FROM
        )

        return {
            "success": results['sent'] > 0,
            "message": f"Correos enviados: {results['sent']}/{results['total']}",
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - INFORMACIÓN
# ============================================================================

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "name": "API de Firma Digital",
        "version": "5.0.0",
        "status": "running",
        "docs": f"http://{Config.API_HOST}:{Config.API_PORT}/docs",
        "endpoints": {
            "auth": "/api/auth/",
            "sign": "/api/sign/",
            "drive": "/api/drive/",
            "gmail": "/api/gmail/"
        }
    }


@app.get("/health")
async def health_check():
    """Health check del servidor"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "signer": state.document_signer is not None,
            "verifier": state.signature_verifier is not None,
            "google_auth": state.google_auth is not None,
            "drive": state.drive_manager is not None,
            "gmail": state.gmail_manager is not None
        }
    }


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

def main():
    """Inicia el servidor API"""
    uvicorn.run(
        "api_server:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.API_ENV == "development",
        log_level="info"
    )


if __name__ == "__main__":
    main()
