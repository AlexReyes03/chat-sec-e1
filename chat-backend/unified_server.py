"""
Servidor Unificado - FastAPI + WebSocket
=========================================

Servidor unificado que combina:
- REST API para autenticación, firma digital y Google APIs
- WebSocket para chat en tiempo real
- Autenticación JWT en ambos protocolos
- Soporte para CLI y navegador web

Endpoints principales:
- POST /api/auth/register - Registrar nuevo usuario
- POST /api/auth/login - Login con credenciales
- POST /api/auth/google - Login con Google OAuth
- POST /api/auth/set-nickname - Establecer apodo
- WS /ws/chat - WebSocket para chat
- POST /api/pdf/generate - Generar PDF de prueba
- POST /api/pdf/sign - Firmar PDF con imagen de canvas
"""

import os
import io
import json
import base64
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Set
from PIL import Image

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, HTTPException, Form, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import uvicorn

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfReader, PdfWriter

from src.config.config import Config
from src.database import get_db, Usuario
from src.auth import AuthService
from src.signature import DocumentSigner, SignatureVerifier, SignatureRequest, VerificationRequest
from src.integrations.google import GoogleAuthManager, GoogleDriveManager, GmailManager
from src.crypto.cifrado_simetrico import Cifrador as CifradorSimetrico
from src.crypto.cifrado_asimetrico import Cifrador as CifradorAsimetrico
from src.security.validacion_integridad import ValidadorIntegridad


# ============================================================================
# MODELOS DE DATOS (Pydantic)
# ============================================================================

class RegisterRequest(BaseModel):
    """Petición de registro"""
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """Petición de login con credenciales"""
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    """Petición de login con Google"""
    email: EmailStr
    google_id: str
    nombre_google: str
    foto_perfil_url: Optional[str] = None


class SetNicknameRequest(BaseModel):
    """Petición para establecer apodo"""
    apodo: str


class GeneratePDFRequest(BaseModel):
    """Petición para generar PDF de prueba"""
    titulo: str = "DOCUMENTO DE PRUEBA"
    contenido: Optional[str] = None


class SignPDFRequest(BaseModel):
    """Petición para firmar PDF"""
    pdf_base64: str
    signature_image_base64: str
    signer_name: str
    signer_email: EmailStr


class ChatMessage(BaseModel):
    """Mensaje de chat"""
    type: str
    message: Optional[str] = None
    data: Optional[dict] = None


class SignDocumentRequest(BaseModel):
    """Petición para firmar documento"""
    file_id: str
    signer_name: str
    signer_email: EmailStr


class UploadToDriveRequest(BaseModel):
    """Petición para subir a Drive"""
    file_id: str
    authorized_emails: List[EmailStr]
    folder_id: Optional[str] = None


# ============================================================================
# INICIALIZACIÓN DE LA APP
# ============================================================================

app = FastAPI(
    title="CHATSEC - API Unificada",
    description="API REST y WebSocket para chat seguro con firma digital",
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
        self.auth_service = AuthService()
        self.google_auth: Optional[GoogleAuthManager] = None
        self.drive_manager: Optional[GoogleDriveManager] = None
        self.gmail_manager: Optional[GmailManager] = None
        self.document_signer: Optional[DocumentSigner] = None
        self.signature_verifier: Optional[SignatureVerifier] = None

        self.connected_clients: Dict[WebSocket, dict] = {}
        self.chat_history: List[dict] = []

        self.cifrador = None
        self.tipo_cifrado = "simetrico"
        self.validador = ValidadorIntegridad()

    def initialize(self):
        """Inicializa los servicios"""
        try:
            Config.crear_directorios()

            print("\nInicializando firmador de documentos...")
            self.document_signer = DocumentSigner(
                private_key_path=Config.SIGNATURE_PRIVATE_KEY_PATH,
                public_key_path=Config.SIGNATURE_PUBLIC_KEY_PATH
            )

            print("Inicializando verificador de firmas...")
            self.signature_verifier = SignatureVerifier(
                public_key_path=Config.SIGNATURE_PUBLIC_KEY_PATH
            )

            print("Inicializando autenticación con Google...")
            try:
                self.google_auth = GoogleAuthManager(
                    credentials_file=Config.GOOGLE_CREDENTIALS_FILE,
                    token_file=Config.GOOGLE_TOKEN_FILE,
                    scopes=Config.GOOGLE_SCOPES
                )
                print("Google Auth inicializado correctamente")
            except Exception as e:
                print(f"Advertencia: No se pudo inicializar Google Auth: {e}")
                print("La firma de PDFs no estará disponible")
                self.google_auth = None

            print("Inicializando cifrador...")
            if self.tipo_cifrado == "simetrico":
                self.cifrador = CifradorSimetrico()
            else:
                self.cifrador = CifradorAsimetrico(es_servidor=True)

            print("\nServicios inicializados correctamente")

        except Exception as e:
            print(f"\nError al inicializar servicios: {e}")
            raise

    def ensure_google_authenticated(self):
        """Asegura autenticación con Google"""
        if not self.google_auth:
            raise HTTPException(status_code=500, detail="Gestor de autenticación no inicializado")

        if not self.google_auth.is_authenticated():
            creds = self.google_auth.authenticate()
            if not creds:
                raise HTTPException(
                    status_code=401,
                    detail="No se pudo autenticar con Google. Ejecuta authenticate_google.py primero."
                )

            self.drive_manager = GoogleDriveManager(creds)
            self.gmail_manager = GmailManager(creds)

        return True


state = AppState()


# ============================================================================
# FUNCIONES DE AUTENTICACIÓN
# ============================================================================

async def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> Usuario:
    """Obtiene el usuario actual desde el token JWT"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token no proporcionado")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Formato de token inválido")

    token = authorization[7:]

    valid, user_id, email = state.auth_service.verify_token(token)

    if not valid:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    user = state.auth_service.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return user


# ============================================================================
# EVENTOS DE INICIO/CIERRE
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Evento de inicio"""
    try:
        print("\n" + "="*70)
        print("INICIANDO SERVIDOR UNIFICADO - CHATSEC v5.0")
        print("="*70)
        Config.mostrar_configuracion()
        print("\nInicializando servicios...")
        state.initialize()
        print("\n" + "="*70)
        print(f"Servidor HTTP iniciado en http://{Config.API_HOST}:{Config.API_PORT}")
        print(f"WebSocket disponible en ws://{Config.API_HOST}:{Config.API_PORT}/ws/chat")
        print(f"Documentación: http://{Config.API_HOST}:{Config.API_PORT}/docs")
        print("="*70 + "\n")
    except Exception as e:
        print(f"\n[ERROR FATAL] Error al iniciar servidor: {e}")
        import traceback
        traceback.print_exc()
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre"""
    print("\nCerrando servidor...")


# ============================================================================
# ENDPOINTS - AUTENTICACIÓN
# ============================================================================

@app.post("/api/auth/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Registra un nuevo usuario"""
    try:
        print(f"[DEBUG] Intento de registro: {request.email}")
        success, message, user = state.auth_service.register_user(
            db, request.email, request.password
        )

        if not success:
            print(f"[DEBUG] Registro fallido: {message}")
            raise HTTPException(status_code=400, detail=message)

        print(f"[DEBUG] Registro exitoso: {request.email}")
        return {
            "success": True,
            "message": message,
            "user": user.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error en registro: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login con credenciales"""
    try:
        print(f"[DEBUG] Intento de login: {request.email}")
        success, message, token, user = state.auth_service.login_with_credentials(
            db, request.email, request.password
        )

        if not success:
            print(f"[DEBUG] Login fallido: {message}")
            raise HTTPException(status_code=401, detail=message)

        print(f"[DEBUG] Login exitoso: {request.email}")
        return {
            "success": True,
            "message": message,
            "token": token,
            "user": user.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error en login: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/google")
async def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Login con Google OAuth"""
    success, message, token, user = state.auth_service.login_with_google(
        db,
        request.email,
        request.google_id,
        request.nombre_google,
        request.foto_perfil_url
    )

    if not success:
        raise HTTPException(status_code=401, detail=message)

    return {
        "success": True,
        "message": message,
        "token": token,
        "user": user.to_dict()
    }


@app.post("/api/auth/set-nickname")
async def set_nickname(
    request: SetNicknameRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Establece el apodo del usuario"""
    success, message = state.auth_service.update_apodo(
        db, current_user.id, request.apodo
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "apodo": request.apodo
    }


@app.get("/api/auth/me")
async def get_me(current_user: Usuario = Depends(get_current_user)):
    """Obtiene información del usuario actual"""
    return {
        "success": True,
        "user": current_user.to_dict()
    }


# ============================================================================
# ENDPOINTS - PDF FIRMA
# ============================================================================

@app.post("/api/pdf/generate")
async def generate_pdf(
    request: GeneratePDFRequest,
    current_user: Usuario = Depends(get_current_user)
):
    """Genera un PDF de prueba con espacio para firma"""
    try:
        pdf_buffer = io.BytesIO()

        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height - 80, request.titulo)

        c.setFont("Helvetica", 10)
        c.drawString(50, height - 100, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

        c.setFont("Helvetica", 12)
        y = height - 150

        if request.contenido:
            lines = request.contenido.split('\n')
            for line in lines:
                c.drawString(50, y, line)
                y -= 20
                if y < 250:
                    break
        else:
            c.drawString(50, y, "Este es un documento de prueba para firma digital.")
            y -= 20
            c.drawString(50, y, "El documento contiene:")
            y -= 20
            c.drawString(70, y, "- Un titulo")
            y -= 20
            c.drawString(70, y, "- La fecha y hora actual")
            y -= 20
            c.drawString(70, y, "- Este texto de prueba")
            y -= 30
            c.drawString(50, y, "Despues de firmar, el PDF sera guardado en Google Drive")
            y -= 20
            c.drawString(50, y, "con firma digital agregada.")

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 200, "Espacio para Firma Digital:")

        c.rect(50, 80, 250, 100, stroke=1, fill=0)

        c.setFont("Helvetica", 9)
        c.drawString(50, 60, f"Usuario: ________________")
        c.drawString(250, 60, f"Firma: _________________")

        c.save()

        pdf_buffer.seek(0)
        pdf_base64 = base64.b64encode(pdf_buffer.read()).decode('utf-8')

        return {
            "success": True,
            "message": "PDF generado exitosamente",
            "pdf_base64": pdf_base64
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")


@app.post("/api/pdf/sign")
async def sign_pdf(
    request: SignPDFRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Firma un PDF con imagen de canvas y sube a Drive"""
    try:
        pdf_data = base64.b64decode(request.pdf_base64)
        signature_data = base64.b64decode(request.signature_image_base64)

        signature_image = Image.open(io.BytesIO(signature_data))

        sig_buffer = io.BytesIO()
        signature_image.save(sig_buffer, format='PNG')
        sig_buffer.seek(0)

        pdf_reader = PdfReader(io.BytesIO(pdf_data))
        pdf_writer = PdfWriter()

        temp_canvas = io.BytesIO()
        c = canvas.Canvas(temp_canvas, pagesize=letter)

        img_reader = ImageReader(sig_buffer)
        c.drawImage(img_reader, 50, 80, width=250, height=100, preserveAspectRatio=True, mask='auto')

        c.save()
        temp_canvas.seek(0)

        overlay_pdf = PdfReader(temp_canvas)

        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]

            if page_num == 0:
                page.merge_page(overlay_pdf.pages[0])

            pdf_writer.add_page(page)

        output_buffer = io.BytesIO()
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"signed_{current_user.email.split('@')[0]}_{timestamp}.pdf"

        signed_path = Path(Config.SIGNED_DOCUMENTS_PATH) / filename
        signed_path.parent.mkdir(parents=True, exist_ok=True)

        with open(signed_path, 'wb') as f:
            f.write(output_buffer.read())

        state.ensure_google_authenticated()

        file_info = state.drive_manager.upload_file(
            file_path=str(signed_path),
            folder_id=Config.GOOGLE_DRIVE_FOLDER_ID or None
        )

        if file_info:
            drive_link = file_info.get('webViewLink', '')
            return {
                "success": True,
                "message": "PDF firmado y subido a Drive exitosamente",
                "filename": filename,
                "drive_link": drive_link,
                "file_info": file_info
            }
        else:
            return {
                "success": True,
                "message": "PDF firmado localmente (Drive no disponible)",
                "filename": filename
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al firmar PDF: {str(e)}")


# ============================================================================
# WEBSOCKET - CHAT
# ============================================================================

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: Optional[str] = None):
    """WebSocket para chat en tiempo real"""
    await websocket.accept()

    user = None
    apodo = None

    try:
        if token:
            db = next(get_db())
            try:
                valid, user_id, email = state.auth_service.verify_token(token)

                if valid:
                    user = state.auth_service.get_user_by_id(db, user_id)
                    if user and user.apodo:
                        apodo = user.apodo
            finally:
                db.close()

        if not apodo:
            await websocket.send_json({
                "type": "system",
                "message": "Por favor ingresa tu apodo:"
            })

            data = await websocket.receive_json()
            apodo = data.get("apodo", "").strip()

            if not apodo or len(apodo) < 2:
                await websocket.send_json({
                    "type": "error",
                    "message": "Apodo inválido"
                })
                await websocket.close()
                return

        state.connected_clients[websocket] = {
            "apodo": apodo,
            "user": user,
            "connected_at": datetime.now()
        }

        await broadcast_message({
            "type": "user_joined",
            "apodo": apodo,
            "timestamp": datetime.now().isoformat()
        }, exclude=websocket)

        await websocket.send_json({
            "type": "welcome",
            "message": f"Bienvenido al chat, {apodo}!",
            "history": state.chat_history[-10:]
        })

        await websocket.send_json({
            "type": "users_list",
            "users": [client["apodo"] for client in state.connected_clients.values()]
        })

        while True:
            data = await websocket.receive_json()

            message_type = data.get("type")
            message_text = data.get("message", "")

            if message_type == "chat":
                chat_message = {
                    "type": "chat",
                    "apodo": apodo,
                    "message": message_text,
                    "timestamp": datetime.now().isoformat()
                }

                state.chat_history.append(chat_message)
                if len(state.chat_history) > 100:
                    state.chat_history.pop(0)

                await broadcast_message(chat_message)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Error en WebSocket: {e}")
    finally:
        if websocket in state.connected_clients:
            apodo = state.connected_clients[websocket]["apodo"]
            del state.connected_clients[websocket]

            await broadcast_message({
                "type": "user_left",
                "apodo": apodo,
                "timestamp": datetime.now().isoformat()
            })


async def broadcast_message(message: dict, exclude: Optional[WebSocket] = None):
    """Envía un mensaje a todos los clientes conectados"""
    for client_ws in list(state.connected_clients.keys()):
        if client_ws != exclude:
            try:
                await client_ws.send_json(message)
            except:
                pass


# ============================================================================
# ENDPOINTS - INFORMACIÓN
# ============================================================================

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "name": "CHATSEC - Servidor Unificado",
        "version": "5.0.0",
        "status": "running",
        "docs": f"http://{Config.API_HOST}:{Config.API_PORT}/docs",
        "endpoints": {
            "auth": "/api/auth/",
            "pdf": "/api/pdf/",
            "websocket": "/ws/chat"
        }
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connected_users": len(state.connected_clients),
        "services": {
            "auth": state.auth_service is not None,
            "signer": state.document_signer is not None,
            "google_auth": state.google_auth is not None
        }
    }


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

def main():
    """Inicia el servidor"""
    uvicorn.run(
        app,  # Usar app directamente en lugar de string para evitar problemas con reload
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=False,  # Desactivar reload temporalmente para depuración
        log_level="info"
    )


if __name__ == "__main__":
    main()
