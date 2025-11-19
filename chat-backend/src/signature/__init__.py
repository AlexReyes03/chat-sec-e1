"""
Módulo de Firma Digital
=======================

Implementa funcionalidad de firma digital para documentos (txt, pdf, zip)
utilizando criptografía RSA y estándares PKI.

Componentes principales:
- KeyManager: Generación y gestión de claves RSA para firma
- DocumentSigner: Firma de documentos de múltiples tipos
- SignatureVerifier: Verificación de firmas digitales
- SignatureMetadata: Información sobre firmas aplicadas
"""

from .key_manager import KeyManager
from .document_signer import DocumentSigner
from .signature_verifier import SignatureVerifier
from .models import (
    SignatureMetadata,
    SignatureResult,
    SignatureRequest,
    VerificationRequest
)

__all__ = [
    'KeyManager',
    'DocumentSigner',
    'SignatureVerifier',
    'SignatureMetadata',
    'SignatureResult',
    'SignatureRequest',
    'VerificationRequest'
]
