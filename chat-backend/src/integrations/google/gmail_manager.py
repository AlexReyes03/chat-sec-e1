"""
Gestor de Gmail
===============

Maneja el envío de correos electrónicos utilizando Gmail API.
"""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials


class GmailManager:
    """
    Gestor de operaciones con Gmail API

    Permite enviar correos electrónicos con o sin adjuntos
    utilizando Gmail API.
    """

    def __init__(self, credentials: Credentials):
        """
        Inicializa el gestor de Gmail

        Args:
            credentials: Credenciales de Google OAuth 2.0
        """
        self.credentials = credentials
        self.service = None
        self._build_service()

    def _build_service(self):
        """Construye el servicio de Gmail API"""
        try:
            self.service = build('gmail', 'v1', credentials=self.credentials)
            print("Servicio de Gmail inicializado")
        except Exception as e:
            print(f"Error al inicializar servicio de Gmail: {e}")
            raise

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        is_html: bool = False
    ) -> bool:
        """
        Envía un correo electrónico

        Args:
            to: Destinatario principal
            subject: Asunto del correo
            body: Cuerpo del mensaje
            from_email: Email del remitente (opcional, usa el autenticado)
            cc: Lista de correos en copia
            bcc: Lista de correos en copia oculta
            is_html: Si el cuerpo es HTML

        Returns:
            True si se envió exitosamente
        """
        try:
            # Crear mensaje
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject

            if from_email:
                message['from'] = from_email

            if cc:
                message['cc'] = ', '.join(cc)

            if bcc:
                message['bcc'] = ', '.join(bcc)

            # Agregar cuerpo
            if is_html:
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))

            # Enviar
            return self._send_message(message)

        except Exception as e:
            print(f"Error al enviar email: {e}")
            return False

    def send_email_with_attachment(
        self,
        to: str,
        subject: str,
        body: str,
        attachment_path: str,
        from_email: Optional[str] = None,
        is_html: bool = False
    ) -> bool:
        """
        Envía un correo con archivo adjunto

        Args:
            to: Destinatario
            subject: Asunto
            body: Cuerpo del mensaje
            attachment_path: Ruta al archivo a adjuntar
            from_email: Email del remitente
            is_html: Si el cuerpo es HTML

        Returns:
            True si se envió exitosamente
        """
        try:
            # Crear mensaje
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject

            if from_email:
                message['from'] = from_email

            # Agregar cuerpo
            if is_html:
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))

            # Agregar adjunto
            import os
            if not os.path.exists(attachment_path):
                print(f"Error: Archivo adjunto no encontrado: {attachment_path}")
                return False

            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())

            encoders.encode_base64(part)

            filename = os.path.basename(attachment_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )

            message.attach(part)

            # Enviar
            return self._send_message(message)

        except Exception as e:
            print(f"Error al enviar email con adjunto: {e}")
            return False

    def send_authorization_email(
        self,
        to: str,
        document_name: str,
        document_link: str,
        signer_name: str,
        from_email: Optional[str] = None,
        additional_info: Optional[str] = None
    ) -> bool:
        """
        Envía un correo de autorización para firma digital

        Args:
            to: Email del destinatario autorizado
            document_name: Nombre del documento
            document_link: Enlace al documento en Google Drive
            signer_name: Nombre del autorizador
            from_email: Email del remitente
            additional_info: Información adicional

        Returns:
            True si se envió exitosamente
        """
        subject = f"Autorización para Firma Digital - {document_name}"

        # Crear cuerpo HTML
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                    border-radius: 8px;
                }}
                .header {{
                    background-color: #4285f4;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 0 0 8px 8px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #4285f4;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #666;
                }}
                .info-box {{
                    background-color: #e8f0fe;
                    padding: 15px;
                    border-left: 4px solid #4285f4;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Autorizacion de Firma Digital</h1>
                </div>
                <div class="content">
                    <p>Estimado/a {to},</p>

                    <p>Se le ha otorgado autorizacion para <strong>firmar digitalmente</strong> el siguiente documento:</p>

                    <div class="info-box">
                        <p><strong>Documento:</strong> {document_name}</p>
                        <p><strong>Autorizado por:</strong> {signer_name}</p>
                        <p><strong>Fecha:</strong> {self._get_current_datetime()}</p>
                    </div>

                    {f'<p><strong>Informacion adicional:</strong><br>{additional_info}</p>' if additional_info else ''}

                    <p>Para acceder al documento y proceder con la firma, haga clic en el siguiente boton:</p>

                    <center>
                        <a href="{document_link}" class="button">Abrir Documento en Google Drive</a>
                    </center>

                    <p><strong>Instrucciones:</strong></p>
                    <ol>
                        <li>Haga clic en el boton de arriba para acceder al documento</li>
                        <li>Revise el documento cuidadosamente</li>
                        <li>Utilice la plataforma de firma digital para firmar el documento</li>
                        <li>El documento firmado se guardara automaticamente</li>
                    </ol>

                    <p><strong>Nota de Seguridad:</strong> Este enlace le otorga permisos especificos para firmar el documento. No comparta este correo con terceros.</p>

                    <p>Si tiene alguna pregunta o no esperaba recibir este correo, por favor contacte al remitente.</p>

                    <p>Saludos cordiales,<br>
                    <strong>Sistema de Firma Digital</strong></p>
                </div>
                <div class="footer">
                    <p>Este es un correo automatico. Por favor no responda a este mensaje.</p>
                    <p>2025 Sistema de Firma Digital - Todos los derechos reservados</p>
                </div>
            </div>
        </body>
        </html>
        """

        return self.send_email(
            to=to,
            subject=subject,
            body=body,
            from_email=from_email,
            is_html=True
        )

    def _send_message(self, message: MIMEMultipart) -> bool:
        """
        Envía un mensaje MIME

        Args:
            message: Mensaje MIME a enviar

        Returns:
            True si se envió exitosamente
        """
        try:
            # Codificar mensaje
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Enviar
            send_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            print(f"Correo enviado exitosamente. ID: {send_message['id']}")
            print(f"  Destinatario: {message['to']}")
            print(f"  Asunto: {message['subject']}")

            return True

        except HttpError as error:
            print(f"Error HTTP al enviar correo: {error}")
            return False
        except Exception as e:
            print(f"Error al enviar correo: {e}")
            return False

    def _get_current_datetime(self) -> str:
        """Obtiene la fecha y hora actual formateada"""
        from datetime import datetime
        return datetime.now().strftime("%d de %B de %Y a las %H:%M")

    def send_batch_authorization_emails(
        self,
        recipients: List[str],
        document_name: str,
        document_link: str,
        signer_name: str,
        from_email: Optional[str] = None
    ) -> dict:
        """
        Envía correos de autorización a múltiples destinatarios

        Args:
            recipients: Lista de emails de destinatarios
            document_name: Nombre del documento
            document_link: Enlace al documento
            signer_name: Nombre del autorizador
            from_email: Email del remitente

        Returns:
            Diccionario con resultados del envío
        """
        results = {
            'total': len(recipients),
            'sent': 0,
            'failed': 0,
            'errors': []
        }

        print(f"\nEnviando correos de autorización a {len(recipients)} destinatarios...")

        for i, recipient in enumerate(recipients, 1):
            print(f"\n[{i}/{len(recipients)}] Enviando a: {recipient}")

            success = self.send_authorization_email(
                to=recipient,
                document_name=document_name,
                document_link=document_link,
                signer_name=signer_name,
                from_email=from_email
            )

            if success:
                results['sent'] += 1
                print(f"  Enviado exitosamente")
            else:
                results['failed'] += 1
                results['errors'].append(recipient)
                print(f"  Error al enviar")

        # Resumen
        print(f"\n{'='*60}")
        print(f"Resumen de envío:")
        print(f"  Total: {results['total']}")
        print(f"  Enviados: {results['sent']}")
        print(f"  Fallidos: {results['failed']}")
        print(f"{'='*60}")

        return results
