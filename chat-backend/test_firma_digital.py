"""
Script de Prueba - Firma Digital
=================================

ARCHIVO TEMPORAL - BORRAR DESPUÉS DE PRUEBAS

Este script prueba las funcionalidades de firma digital:
- Firma de documentos (TXT, PDF)
- Verificación de firmas
- Gestión de claves

Uso:
    python test_firma_digital.py
"""

import os
from pathlib import Path
from src.config.config import Config
from src.signature import DocumentSigner, SignatureVerifier, SignatureRequest, VerificationRequest


def crear_documento_prueba():
    """Crea un documento de texto de prueba"""
    Config.crear_directorios()

    documento_path = Path(Config.TEMP_DOCUMENTS_PATH) / "prueba.txt"

    with open(documento_path, 'w', encoding='utf-8') as f:
        f.write("Este es un documento de prueba para firma digital.\n")
        f.write("Contiene texto de ejemplo para verificar la firma.\n")
        f.write("Fecha: 2025-11-19\n")

    print(f"Documento de prueba creado: {documento_path}")
    return str(documento_path)


def test_firma_documento():
    """Prueba la firma de un documento"""
    print("\n" + "="*70)
    print("PRUEBA: FIRMA DE DOCUMENTO")
    print("="*70 + "\n")

    # Crear documento de prueba
    documento_path = crear_documento_prueba()

    # Inicializar firmador
    print("Inicializando firmador...")
    signer = DocumentSigner(
        private_key_path=Config.SIGNATURE_PRIVATE_KEY_PATH,
        public_key_path=Config.SIGNATURE_PUBLIC_KEY_PATH
    )

    # Crear petición de firma
    request = SignatureRequest(
        document_path=documento_path,
        signer_name="Usuario Prueba",
        signer_email="prueba@example.com",
        additional_info={"tipo": "documento_prueba", "version": "1.0"}
    )

    # Firmar documento
    print("\nFirmando documento...")
    result = signer.sign_document(request)

    # Mostrar resultado
    if result.success:
        print("\nRESULTADO: EXITO")
        print(f"Archivo de firma: {result.signed_file_path}")
        print(f"\nMetadatos:")
        print(f"  Firmante: {result.metadata.signer_name}")
        print(f"  Email: {result.metadata.signer_email}")
        print(f"  Fecha: {result.metadata.signature_date}")
        print(f"  Hash: {result.metadata.document_hash[:32]}...")
        print(f"  Algoritmo: {result.metadata.signature_algorithm}")
    else:
        print(f"\nRESULTADO: ERROR")
        print(f"Error: {result.error}")

    return result.success, documento_path


def test_verificacion_firma(documento_path):
    """Prueba la verificación de una firma"""
    print("\n" + "="*70)
    print("PRUEBA: VERIFICACION DE FIRMA")
    print("="*70 + "\n")

    # Inicializar verificador
    print("Inicializando verificador...")
    verifier = SignatureVerifier(
        public_key_path=Config.SIGNATURE_PUBLIC_KEY_PATH
    )

    # Crear petición de verificación
    request = VerificationRequest(
        signed_document_path=documento_path
    )

    # Verificar firma
    print("\nVerificando firma...")
    result = verifier.verify_document(request)

    # Mostrar resultado
    if result.success:
        print("\nRESULTADO: FIRMA VALIDA")
        print(f"Estado: {result.status.value}")
        print(f"Mensaje: {result.message}")
        if result.metadata:
            print(f"\nInformacion del firmante:")
            print(f"  Nombre: {result.metadata.signer_name}")
            print(f"  Email: {result.metadata.signer_email}")
            print(f"  Fecha: {result.metadata.signature_date}")
    else:
        print(f"\nRESULTADO: FIRMA INVALIDA")
        print(f"Estado: {result.status.value}")
        print(f"Error: {result.error}")

    return result.success


def test_firma_alterada(documento_path):
    """Prueba verificación de documento alterado"""
    print("\n" + "="*70)
    print("PRUEBA: DOCUMENTO ALTERADO")
    print("="*70 + "\n")

    # Alterar documento
    print("Alterando documento...")
    with open(documento_path, 'a', encoding='utf-8') as f:
        f.write("\nEsta línea fue agregada después de la firma.\n")

    # Verificar
    verifier = SignatureVerifier(
        public_key_path=Config.SIGNATURE_PUBLIC_KEY_PATH
    )
    request = VerificationRequest(signed_document_path=documento_path)
    result = verifier.verify_document(request)

    # Mostrar resultado
    if result.success:
        print(f"\nRESULTADO INESPERADO: Firma válida (debería ser inválida)")
        return False
    else:
        print(f"\nRESULTADO ESPERADO: Firma inválida")
        print(f"Estado: {result.status.value}")
        print(f"Mensaje: {result.message}")
        return True


def main():
    """Función principal de pruebas"""
    print("\n" + "="*70)
    print("PRUEBAS DE FIRMA DIGITAL")
    print("="*70)

    Config.crear_directorios()

    resultados = {
        'firma': False,
        'verificacion': False,
        'alteracion': False
    }

    try:
        # Test 1: Firmar documento
        success, documento_path = test_firma_documento()
        resultados['firma'] = success

        if not success:
            print("\nError en firma. Abortando pruebas.")
            return

        # Test 2: Verificar firma válida
        resultados['verificacion'] = test_verificacion_firma(documento_path)

        # Test 3: Detectar alteración
        resultados['alteracion'] = test_firma_alterada(documento_path)

    except Exception as e:
        print(f"\nError durante pruebas: {e}")
        import traceback
        traceback.print_exc()

    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE PRUEBAS")
    print("="*70)
    print(f"Firma de documento:       {'OK' if resultados['firma'] else 'FAIL'}")
    print(f"Verificacion de firma:    {'OK' if resultados['verificacion'] else 'FAIL'}")
    print(f"Deteccion de alteracion:  {'OK' if resultados['alteracion'] else 'FAIL'}")
    print("="*70 + "\n")

    # Limpieza
    print("Para limpiar archivos de prueba, ejecuta:")
    print(f"  rmdir /s /q {Config.TEMP_DOCUMENTS_PATH}")
    print(f"  rmdir /s /q {Config.SIGNED_DOCUMENTS_PATH}")


if __name__ == "__main__":
    main()
