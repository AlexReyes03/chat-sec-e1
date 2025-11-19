import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from src.config.config import Config


class Cifrador:
    def __init__(self):
        self.clave_fernet = self._generar_clave_fernet()

    def _generar_clave_fernet(self):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=Config.SALT,
            iterations=Config.PBKDF2_ITERATIONS,
        )
        clave_derivada = kdf.derive(Config.CLAVE_SECRETA.encode())
        clave_base64 = base64.urlsafe_b64encode(clave_derivada)
        return clave_base64

    def cifrar_mensaje(self, mensaje):
        try:
            mensaje_cifrado = self._cifrar_fernet(mensaje)
            return mensaje_cifrado.decode('utf-8')
        except Exception as e:
            print(f"Error cifrando mensaje: {e}")
            return None

    def descifrar_mensaje(self, mensaje_cifrado):
        try:
            mensaje_bytes = mensaje_cifrado.encode('utf-8')
            mensaje_descifrado = self._descifrar_fernet(mensaje_bytes)
            return mensaje_descifrado
        except Exception as e:
            print(f"Error descifrando mensaje: {e}")
            return None

    def cifrar_datos_usuario(self, nombre, ip, puerto):
        try:
            nombre_cifrado = self._cifrar_fernet(nombre).decode('utf-8')
            ip_cifrada = self._cifrar_fernet(ip).decode('utf-8')
            puerto_cifrado = self._cifrar_fernet(str(puerto)).decode('utf-8')
            return nombre_cifrado, ip_cifrada, puerto_cifrado
        except Exception as e:
            print(f"Error cifrando datos de usuario: {e}")
            return None, None, None

    def descifrar_datos_usuario(self, nombre_cifrado, ip_cifrada, puerto_cifrado):
        try:
            nombre = self._descifrar_fernet(nombre_cifrado.encode('utf-8'))
            ip = self._descifrar_fernet(ip_cifrada.encode('utf-8'))
            puerto = int(self._descifrar_fernet(puerto_cifrado.encode('utf-8')))
            return nombre, ip, puerto
        except Exception as e:
            print(f"Error descifrando datos de usuario: {e}")
            return None, None, None

    def _cifrar_fernet(self, texto_plano):
        try:
            f = Fernet(self.clave_fernet)
            texto_bytes = texto_plano.encode('utf-8')
            datos_cifrados = f.encrypt(texto_bytes)
            return datos_cifrados
        except Exception as e:
            print(f"Error en cifrado Fernet: {e}")
            return None

    def _cifrar_nombre_usuario(self, nombre):
        try:
            if len(nombre) < 2 or len(nombre) > 20:
                return None
            return self._cifrar_fernet(nombre).decode('utf-8')
        except Exception as e:
            print(f"Error cifrando nombre: {e}")
            return None

    def _descifrar_fernet(self, datos_cifrados):
        try:
            f = Fernet(self.clave_fernet)
            texto_bytes = f.decrypt(datos_cifrados)
            texto_plano = texto_bytes.decode('utf-8')
            return texto_plano
        except Exception as e:
            print(f"Error en descifrado Fernet: {e}")
            return None

    def _descifrar_puerto(self, puerto_cifrado):
        try:
            puerto_str = self._descifrar_fernet(puerto_cifrado.encode('utf-8'))
            return int(puerto_str) if puerto_str else None
        except Exception as e:
            print(f"Error descifrando puerto: {e}")
            return None


if __name__ == "__main__":
    print("Probando modulo de cifrado simetrico...")

    cifrador = Cifrador()

    mensaje_original = "Hola mundo!"
    mensaje_cifrado = cifrador.cifrar_mensaje(mensaje_original)
    mensaje_descifrado = cifrador.descifrar_mensaje(mensaje_cifrado)

    print(f"Mensaje original: {mensaje_original}")
    print(f"Mensaje cifrado: {mensaje_cifrado}")
    print(f"Mensaje descifrado: {mensaje_descifrado}")
    print(f"Coinciden: {mensaje_original == mensaje_descifrado}")

    nombre, ip, puerto = "Usuario1", "127.0.0.1", 54321
    nombre_c, ip_c, puerto_c = cifrador.cifrar_datos_usuario(nombre, ip, puerto)
    nombre_d, ip_d, puerto_d = cifrador.descifrar_datos_usuario(nombre_c, ip_c, puerto_c)

    print(f"\nDatos originales: {nombre}, {ip}, {puerto}")
    print(f"Datos descifrados: {nombre_d}, {ip_d}, {puerto_d}")
    print(f"Coinciden: {nombre == nombre_d and ip == ip_d and puerto == puerto_d}")


