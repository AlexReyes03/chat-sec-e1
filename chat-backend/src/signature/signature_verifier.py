"""
Verificador de Firmas Digitales
================================

Implementa la verificación de firmas digitales de documentos
firmados con RSA-PSS.
"""

import os
import json
from typing import Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

from .models import (
    SignatureMetadata,
    SignatureResult,
    SignatureStatus,
    VerificationRequest
)
from .key_manager import KeyManager
from .document_signer import DocumentSigner


class SignatureVerifier:
    """
    Verificador de firmas digitales

    Verifica la autenticidad e integridad de documentos firmados
    digitalmente utilizando criptografía RSA-PSS.
    """

    def __init__(self, public_key_path: Optional[str] = None):
        """
        Inicializa el verificador de firmas

        Args:
            public_key_path: Ruta a la clave pública (opcional si está en la firma)
        """
        self.key_manager = KeyManager()
        self.public_key_path = public_key_path

        # Cargar clave pública si se proporcionó
        if public_key_path and os.path.exists(public_key_path):
            self.key_manager.load_public_key(public_key_path)

    def _load_signature_file(self, signature_file_path: str) -> Optional[dict]:
        """
        Carga un archivo de firma (.sig)

        Args:
            signature_file_path: Ruta al archivo de firma

        Returns:
            Diccionario con firma y metadatos o None si hay error
        """
        try:
            if not os.path.exists(signature_file_path):
                print(f"Error: Archivo de firma no encontrado: {signature_file_path}")
                return None

            with open(signature_file_path, 'r', encoding='utf-8') as f:
                signature_package = json.load(f)

            return signature_package

        except Exception as e:
            print(f"Error al cargar archivo de firma: {e}")
            return None

    def _calculate_document_hash(self, file_path: str) -> str:
        """
        Calcula el hash SHA-256 de un documento

        Args:
            file_path: Ruta al documento

        Returns:
            Hash SHA-256 en formato hexadecimal
        """
        hash_obj = hashes.Hash(hashes.SHA256())

        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hash_obj.update(chunk)

        return hash_obj.finalize().hex()

    def _verify_signature(self, document_hash: str, signature_data: bytes) -> bool:
        """
        Verifica una firma digital

        Args:
            document_hash: Hash SHA-256 del documento
            signature_data: Datos de la firma (bytes)

        Returns:
            True si la firma es válida
        """
        try:
            self.key_manager.public_key.verify(
                signature_data,
                document_hash.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True

        except InvalidSignature:
            return False
        except Exception as e:
            print(f"Error al verificar firma: {e}")
            return False

    def verify_document(self, request: VerificationRequest) -> SignatureResult:
        """
        Verifica la firma de un documento

        Args:
            request: Petición de verificación

        Returns:
            Resultado de la verificación
        """
        try:
            # Validar que el documento firmado existe
            if not os.path.exists(request.signed_document_path):
                return SignatureResult(
                    success=False,
                    message="Documento firmado no encontrado",
                    status=SignatureStatus.INVALID,
                    error=f"El archivo {request.signed_document_path} no existe"
                )

            # Determinar ruta del archivo de firma
            # Puede ser el documento original con .sig o un archivo separado
            if request.signed_document_path.endswith('.sig'):
                signature_file_path = request.signed_document_path
                # Inferir ruta del documento original
                document_path = request.original_document_path or request.signed_document_path[:-4]
            else:
                document_path = request.signed_document_path
                signature_file_path = f"{document_path}.sig"

            # Validar que el documento original existe
            if not os.path.exists(document_path):
                return SignatureResult(
                    success=False,
                    message="Documento original no encontrado",
                    status=SignatureStatus.INVALID,
                    error=f"El archivo {document_path} no existe"
                )

            # Cargar archivo de firma
            signature_package = self._load_signature_file(signature_file_path)
            if not signature_package:
                return SignatureResult(
                    success=False,
                    message="No se pudo cargar el archivo de firma",
                    status=SignatureStatus.INVALID,
                    error="El archivo de firma es inválido o está corrupto"
                )

            # Extraer firma y metadatos
            signature_data = bytes.fromhex(signature_package['signature'])
            metadata = SignatureMetadata.from_dict(signature_package['metadata'])

            # Cargar clave pública si se proporcionó una diferente
            if request.public_key_path:
                if not self.key_manager.load_public_key(request.public_key_path):
                    return SignatureResult(
                        success=False,
                        message="No se pudo cargar la clave pública",
                        status=SignatureStatus.KEY_MISMATCH,
                        error="Error al cargar la clave pública proporcionada"
                    )

            # Verificar que tenemos una clave pública
            if not self.key_manager.public_key:
                return SignatureResult(
                    success=False,
                    message="No hay clave pública disponible",
                    status=SignatureStatus.KEY_MISMATCH,
                    error="Se requiere una clave pública para verificar la firma"
                )

            # Calcular hash actual del documento
            current_hash = self._calculate_document_hash(document_path)

            # Comparar con el hash almacenado en los metadatos
            if current_hash != metadata.document_hash:
                return SignatureResult(
                    success=False,
                    message="El documento ha sido modificado después de la firma",
                    status=SignatureStatus.TAMPERED,
                    metadata=metadata,
                    error="El hash del documento no coincide con el hash firmado"
                )

            # Verificar la firma digital
            is_valid = self._verify_signature(current_hash, signature_data)

            if is_valid:
                return SignatureResult(
                    success=True,
                    message="Firma válida - El documento es auténtico y no ha sido modificado",
                    status=SignatureStatus.VALID,
                    metadata=metadata
                )
            else:
                return SignatureResult(
                    success=False,
                    message="Firma inválida",
                    status=SignatureStatus.INVALID,
                    metadata=metadata,
                    error="La firma digital no pudo ser verificada"
                )

        except Exception as e:
            return SignatureResult(
                success=False,
                message="Error al verificar documento",
                status=SignatureStatus.INVALID,
                error=str(e)
            )

    def verify_batch(self, document_paths: list) -> list:
        """
        Verifica múltiples documentos en batch

        Args:
            document_paths: Lista de rutas a documentos firmados

        Returns:
            Lista de resultados de verificación
        """
        results = []

        print(f"\nVerificando {len(document_paths)} documentos...")

        for i, doc_path in enumerate(document_paths, 1):
            print(f"\n[{i}/{len(document_paths)}] Verificando: {doc_path}")

            request = VerificationRequest(signed_document_path=doc_path)
            result = self.verify_document(request)
            results.append(result)

            # Mostrar resultado
            status_icon = "✓" if result.status == SignatureStatus.VALID else "✗"
            print(f"  {status_icon} {result.message}")

            if result.metadata:
                print(f"     Firmante: {result.metadata.signer_name} ({result.metadata.signer_email})")
                print(f"     Fecha: {result.metadata.signature_date}")

        # Resumen
        valid = sum(1 for r in results if r.status == SignatureStatus.VALID)
        print(f"\n{'='*60}")
        print(f"Resumen: {valid}/{len(document_paths)} firmas válidas")
        print(f"{'='*60}")

        return results

    @staticmethod
    def extract_metadata_from_signature(signature_file_path: str) -> Optional[SignatureMetadata]:
        """
        Extrae metadatos de un archivo de firma sin verificarla

        Args:
            signature_file_path: Ruta al archivo de firma

        Returns:
            Metadatos de la firma o None si hay error
        """
        try:
            with open(signature_file_path, 'r', encoding='utf-8') as f:
                signature_package = json.load(f)

            return SignatureMetadata.from_dict(signature_package['metadata'])

        except Exception as e:
            print(f"Error al extraer metadatos: {e}")
            return None

    @staticmethod
    def get_signature_info(document_path: str) -> dict:
        """
        Obtiene información resumida de una firma

        Args:
            document_path: Ruta al documento firmado

        Returns:
            Diccionario con información de la firma
        """
        signature_file_path = f"{document_path}.sig"

        if not os.path.exists(signature_file_path):
            return {
                'has_signature': False,
                'message': 'No se encontró archivo de firma'
            }

        metadata = SignatureVerifier.extract_metadata_from_signature(signature_file_path)

        if not metadata:
            return {
                'has_signature': True,
                'is_valid': False,
                'message': 'Archivo de firma corrupto'
            }

        return {
            'has_signature': True,
            'signer_name': metadata.signer_name,
            'signer_email': metadata.signer_email,
            'signature_date': metadata.signature_date.isoformat(),
            'algorithm': metadata.signature_algorithm,
            'document_hash': metadata.document_hash[:16] + '...',  # Primeros 16 caracteres
            'additional_info': metadata.additional_info
        }
