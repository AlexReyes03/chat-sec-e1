"""
Firmador de Documentos
======================

Implementa la firma digital de documentos de múltiples formatos
(txt, pdf, zip) utilizando criptografía RSA-PSS.
"""

import os
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature

from .models import (
    SignatureMetadata,
    SignatureResult,
    SignatureStatus,
    DocumentType,
    SignatureRequest
)
from .key_manager import KeyManager


class DocumentSigner:
    """
    Firmador de documentos digitales

    Soporta firma de documentos en formatos txt, pdf y zip.
    La firma se almacena junto con metadatos en un archivo separado.
    """

    def __init__(self, private_key_path: str, public_key_path: str, password: Optional[bytes] = None):
        """
        Inicializa el firmador de documentos

        Args:
            private_key_path: Ruta a la clave privada RSA
            public_key_path: Ruta a la clave pública RSA
            password: Contraseña de la clave privada (si está cifrada)
        """
        self.key_manager = KeyManager()
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path

        # Cargar claves
        if not self._load_keys(password):
            raise ValueError("No se pudieron cargar las claves de firma")

    def _load_keys(self, password: Optional[bytes] = None) -> bool:
        """
        Carga las claves de firma

        Args:
            password: Contraseña de la clave privada

        Returns:
            True si se cargaron correctamente
        """
        # Si las claves no existen, generarlas
        if not KeyManager.verify_key_files_exist(self.private_key_path, self.public_key_path):
            print("Claves de firma no encontradas. Generando nuevas claves...")
            if not KeyManager.generate_and_save_keys(
                self.private_key_path,
                self.public_key_path,
                key_size=2048,
                password=password
            ):
                return False

        # Cargar clave privada
        if not self.key_manager.load_private_key(self.private_key_path, password):
            return False

        return True

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

    def _create_signature(self, document_hash: str) -> bytes:
        """
        Crea una firma digital del hash del documento

        Args:
            document_hash: Hash SHA-256 del documento

        Returns:
            Firma digital (bytes)
        """
        # Firmar con RSA-PSS (Probabilistic Signature Scheme)
        signature = self.key_manager.private_key.sign(
            document_hash.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return signature

    def _get_signature_file_path(self, document_path: str) -> str:
        """
        Obtiene la ruta del archivo de firma para un documento

        Args:
            document_path: Ruta al documento original

        Returns:
            Ruta al archivo .sig que contendrá la firma y metadatos
        """
        return f"{document_path}.sig"

    def _detect_document_type(self, file_path: str) -> Optional[DocumentType]:
        """
        Detecta el tipo de documento por su extensión

        Args:
            file_path: Ruta al documento

        Returns:
            Tipo de documento o None si no es soportado
        """
        extension = Path(file_path).suffix.lower()

        if extension == '.txt':
            return DocumentType.TXT
        elif extension == '.pdf':
            return DocumentType.PDF
        elif extension == '.zip':
            return DocumentType.ZIP
        else:
            return None

    def sign_document(self, request: SignatureRequest) -> SignatureResult:
        """
        Firma un documento digitalmente

        Args:
            request: Petición de firma con toda la información necesaria

        Returns:
            Resultado de la operación de firma
        """
        try:
            # Validar que el archivo existe
            if not os.path.exists(request.document_path):
                return SignatureResult(
                    success=False,
                    message="Documento no encontrado",
                    error=f"El archivo {request.document_path} no existe"
                )

            # Detectar tipo de documento
            doc_type = self._detect_document_type(request.document_path)
            if not doc_type:
                return SignatureResult(
                    success=False,
                    message="Tipo de documento no soportado",
                    error="Solo se soportan archivos .txt, .pdf y .zip"
                )

            # Calcular hash del documento
            document_hash = self._calculate_document_hash(request.document_path)

            # Crear metadatos de firma
            metadata = SignatureMetadata(
                signer_name=request.signer_name,
                signer_email=request.signer_email,
                signature_date=datetime.now(),
                document_hash=document_hash,
                key_fingerprint=self.key_manager.get_public_key_fingerprint(),
                additional_info={
                    'document_type': doc_type.value,
                    'document_name': Path(request.document_path).name,
                    **request.additional_info
                }
            )

            # Crear firma digital
            signature_data = self._create_signature(document_hash)

            # Determinar ruta del archivo de firma
            if request.output_path:
                signature_file_path = request.output_path
            else:
                signature_file_path = self._get_signature_file_path(request.document_path)

            # Guardar firma y metadatos
            self._save_signature(signature_file_path, signature_data, metadata)

            return SignatureResult(
                success=True,
                message="Documento firmado exitosamente",
                status=SignatureStatus.VALID,
                metadata=metadata,
                signature_data=signature_data,
                signed_file_path=signature_file_path
            )

        except Exception as e:
            return SignatureResult(
                success=False,
                message="Error al firmar documento",
                error=str(e)
            )

    def _save_signature(self, signature_file_path: str, signature_data: bytes, metadata: SignatureMetadata):
        """
        Guarda la firma y metadatos en un archivo .sig

        Args:
            signature_file_path: Ruta donde guardar el archivo de firma
            signature_data: Datos de la firma (bytes)
            metadata: Metadatos de la firma
        """
        # Crear estructura de datos para guardar
        signature_package = {
            'signature': signature_data.hex(),  # Convertir a hex para JSON
            'metadata': metadata.to_dict()
        }

        # Guardar en archivo JSON
        with open(signature_file_path, 'w', encoding='utf-8') as f:
            json.dump(signature_package, f, indent=2, ensure_ascii=False)

        print(f"Firma guardada en: {signature_file_path}")

    def sign_batch(self, document_paths: list, signer_name: str, signer_email: str) -> list:
        """
        Firma múltiples documentos en batch

        Args:
            document_paths: Lista de rutas a documentos
            signer_name: Nombre del firmante
            signer_email: Email del firmante

        Returns:
            Lista de resultados de firma
        """
        results = []

        print(f"\nFirmando {len(document_paths)} documentos...")

        for i, doc_path in enumerate(document_paths, 1):
            print(f"\n[{i}/{len(document_paths)}] Firmando: {doc_path}")

            request = SignatureRequest(
                document_path=doc_path,
                signer_name=signer_name,
                signer_email=signer_email
            )

            result = self.sign_document(request)
            results.append(result)

            if result.success:
                print(f"  ✓ Firmado exitosamente")
            else:
                print(f"  ✗ Error: {result.error}")

        # Resumen
        successful = sum(1 for r in results if r.success)
        print(f"\n{'='*60}")
        print(f"Resumen: {successful}/{len(document_paths)} documentos firmados exitosamente")
        print(f"{'='*60}")

        return results

    @staticmethod
    def create_signed_package(document_path: str, signature_path: str, output_zip: str) -> bool:
        """
        Crea un paquete ZIP con el documento y su firma

        Args:
            document_path: Ruta al documento original
            signature_path: Ruta al archivo de firma
            output_zip: Ruta del ZIP de salida

        Returns:
            True si se creó correctamente
        """
        try:
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Agregar documento original
                zipf.write(document_path, Path(document_path).name)

                # Agregar archivo de firma
                zipf.write(signature_path, Path(signature_path).name)

                # Agregar clave pública (opcional)
                # zipf.write(public_key_path, 'public_key.pem')

            print(f"Paquete firmado creado: {output_zip}")
            return True

        except Exception as e:
            print(f"Error al crear paquete firmado: {e}")
            return False
