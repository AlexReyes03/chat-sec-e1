"""
Modelos de Datos para Firma Digital
====================================

Define las estructuras de datos utilizadas en el sistema de firma digital.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class DocumentType(Enum):
    """Tipos de documentos soportados para firma"""
    TXT = "txt"
    PDF = "pdf"
    ZIP = "zip"


class SignatureStatus(Enum):
    """Estados posibles de una firma digital"""
    VALID = "valid"               # Firma válida
    INVALID = "invalid"           # Firma inválida
    TAMPERED = "tampered"         # Documento alterado después de firma
    EXPIRED = "expired"           # Firma expirada
    KEY_MISMATCH = "key_mismatch" # Clave pública no coincide


@dataclass
class SignatureMetadata:
    """
    Metadatos de una firma digital

    Attributes:
        signer_name: Nombre del firmante
        signer_email: Email del firmante
        signature_date: Fecha y hora de la firma
        document_hash: Hash SHA-256 del documento original
        signature_algorithm: Algoritmo de firma utilizado
        key_fingerprint: Huella digital de la clave pública
        additional_info: Información adicional personalizada
    """
    signer_name: str
    signer_email: str
    signature_date: datetime
    document_hash: str
    signature_algorithm: str = "RSA-PSS with SHA-256"
    key_fingerprint: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte los metadatos a diccionario"""
        return {
            'signer_name': self.signer_name,
            'signer_email': self.signer_email,
            'signature_date': self.signature_date.isoformat(),
            'document_hash': self.document_hash,
            'signature_algorithm': self.signature_algorithm,
            'key_fingerprint': self.key_fingerprint,
            'additional_info': self.additional_info
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SignatureMetadata':
        """Crea metadatos desde un diccionario"""
        return cls(
            signer_name=data['signer_name'],
            signer_email=data['signer_email'],
            signature_date=datetime.fromisoformat(data['signature_date']),
            document_hash=data['document_hash'],
            signature_algorithm=data.get('signature_algorithm', 'RSA-PSS with SHA-256'),
            key_fingerprint=data.get('key_fingerprint'),
            additional_info=data.get('additional_info', {})
        )


@dataclass
class SignatureResult:
    """
    Resultado de una operación de firma o verificación

    Attributes:
        success: Si la operación fue exitosa
        status: Estado de la firma (para verificación)
        message: Mensaje descriptivo del resultado
        metadata: Metadatos de la firma
        signature_data: Datos de la firma (bytes)
        signed_file_path: Ruta al archivo firmado
        error: Mensaje de error (si aplica)
    """
    success: bool
    message: str
    status: Optional[SignatureStatus] = None
    metadata: Optional[SignatureMetadata] = None
    signature_data: Optional[bytes] = None
    signed_file_path: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el resultado a diccionario"""
        result = {
            'success': self.success,
            'message': self.message,
            'status': self.status.value if self.status else None,
            'signed_file_path': self.signed_file_path,
            'error': self.error
        }

        if self.metadata:
            result['metadata'] = self.metadata.to_dict()

        return result


@dataclass
class SignatureRequest:
    """
    Petición de firma digital

    Attributes:
        document_path: Ruta al documento a firmar
        signer_name: Nombre del firmante
        signer_email: Email del firmante
        output_path: Ruta donde guardar el documento firmado (opcional)
        additional_info: Información adicional a incluir en la firma
    """
    document_path: str
    signer_name: str
    signer_email: str
    output_path: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationRequest:
    """
    Petición de verificación de firma

    Attributes:
        signed_document_path: Ruta al documento firmado
        original_document_path: Ruta al documento original (opcional)
        public_key_path: Ruta a la clave pública (opcional)
    """
    signed_document_path: str
    original_document_path: Optional[str] = None
    public_key_path: Optional[str] = None
