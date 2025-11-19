import os
import ssl
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


class SSLManager:
    @staticmethod
    def generar_certificado_autofirmado(cert_file, key_file, dias_validez=365):
        try:
            os.makedirs(os.path.dirname(cert_file), exist_ok=True)

            clave_privada = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )

            with open(key_file, 'wb') as f:
                f.write(clave_privada.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))

            nombre = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, 'MX'),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, 'Estado'),
                x509.NameAttribute(NameOID.LOCALITY_NAME, 'Ciudad'),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Chat Seguro'),
                x509.NameAttribute(NameOID.COMMON_NAME, 'localhost'),
            ])

            certificado = x509.CertificateBuilder().subject_name(
                nombre
            ).issuer_name(
                nombre
            ).public_key(
                clave_privada.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=dias_validez)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName('localhost'),
                    x509.DNSName('127.0.0.1'),
                ]),
                critical=False,
            ).sign(clave_privada, hashes.SHA256(), default_backend())

            with open(cert_file, 'wb') as f:
                f.write(certificado.public_bytes(serialization.Encoding.PEM))

            print(f"\nCertificado SSL autofirmado generado:")
            print(f"  Certificado: {cert_file}")
            print(f"  Clave privada: {key_file}")
            print(f"  Validez: {dias_validez} dias")

            return True

        except Exception as e:
            print(f"Error generando certificado autofirmado: {e}")
            return False

    @staticmethod
    def crear_contexto_ssl_servidor(cert_file, key_file):
        try:
            contexto_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            contexto_ssl.load_cert_chain(cert_file, key_file)

            contexto_ssl.check_hostname = False
            contexto_ssl.verify_mode = ssl.CERT_NONE

            return contexto_ssl
        except Exception as e:
            print(f"Error creando contexto SSL para servidor: {e}")
            return None

    @staticmethod
    def crear_contexto_ssl_cliente():
        try:
            contexto_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

            contexto_ssl.check_hostname = False
            contexto_ssl.verify_mode = ssl.CERT_NONE

            return contexto_ssl
        except Exception as e:
            print(f"Error creando contexto SSL para cliente: {e}")
            return None

    @staticmethod
    def verificar_certificados_existen(cert_file, key_file):
        return os.path.exists(cert_file) and os.path.exists(key_file)


if __name__ == '__main__':
    print('Probando generacion de certificados SSL...')

    cert_file = 'certs/test.crt'
    key_file = 'certs/test.key'

    if SSLManager.generar_certificado_autofirmado(cert_file, key_file, dias_validez=30):
        print('\nCertificado de prueba generado exitosamente')

        contexto_servidor = SSLManager.crear_contexto_ssl_servidor(cert_file, key_file)
        if contexto_servidor:
            print('Contexto SSL del servidor creado exitosamente')

        contexto_cliente = SSLManager.crear_contexto_ssl_cliente()
        if contexto_cliente:
            print('Contexto SSL del cliente creado exitosamente')
    else:
        print('\nError generando certificado de prueba')


