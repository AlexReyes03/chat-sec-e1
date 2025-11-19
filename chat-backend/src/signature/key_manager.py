"""
Gestión de Claves para Firma Digital
====================================

Maneja la generación, carga y almacenamiento de claves RSA
para firma digital de documentos.
"""

import os
from pathlib import Path
from typing import Tuple, Optional
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class KeyManager:
    """
    Gestor de claves RSA para firma digital

    Maneja la generación, carga y almacenamiento de pares de claves RSA
    utilizadas para firmar digitalmente documentos.
    """

    def __init__(self, key_size: int = 2048):
        """
        Inicializa el gestor de claves

        Args:
            key_size: Tamaño de la clave RSA en bits (2048, 3072, 4096)
        """
        if key_size not in [2048, 3072, 4096]:
            raise ValueError("El tamaño de clave debe ser 2048, 3072 o 4096 bits")

        self.key_size = key_size
        self.private_key = None
        self.public_key = None

    def generate_key_pair(self) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """
        Genera un nuevo par de claves RSA

        Returns:
            Tupla (clave_privada, clave_publica)
        """
        print(f"Generando par de claves RSA de {self.key_size} bits...")

        # Generar clave privada
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size,
            backend=default_backend()
        )

        # Extraer clave pública
        self.public_key = self.private_key.public_key()

        print("Par de claves generado exitosamente")
        return self.private_key, self.public_key

    def save_private_key(self, filepath: str, password: Optional[bytes] = None) -> bool:
        """
        Guarda la clave privada en un archivo PEM

        Args:
            filepath: Ruta donde guardar la clave privada
            password: Contraseña para cifrar la clave (opcional pero recomendado)

        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        if not self.private_key:
            print("Error: No hay clave privada para guardar")
            return False

        try:
            # Crear directorio si no existe
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            # Serializar clave privada
            if password:
                encryption = serialization.BestAvailableEncryption(password)
            else:
                encryption = serialization.NoEncryption()

            pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=encryption
            )

            # Guardar en archivo
            with open(filepath, 'wb') as f:
                f.write(pem)

            print(f"Clave privada guardada en: {filepath}")
            return True

        except Exception as e:
            print(f"Error al guardar clave privada: {e}")
            return False

    def save_public_key(self, filepath: str) -> bool:
        """
        Guarda la clave pública en un archivo PEM

        Args:
            filepath: Ruta donde guardar la clave pública

        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        if not self.public_key:
            print("Error: No hay clave pública para guardar")
            return False

        try:
            # Crear directorio si no existe
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            # Serializar clave pública
            pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Guardar en archivo
            with open(filepath, 'wb') as f:
                f.write(pem)

            print(f"Clave pública guardada en: {filepath}")
            return True

        except Exception as e:
            print(f"Error al guardar clave pública: {e}")
            return False

    def load_private_key(self, filepath: str, password: Optional[bytes] = None) -> Optional[rsa.RSAPrivateKey]:
        """
        Carga una clave privada desde un archivo PEM

        Args:
            filepath: Ruta al archivo de clave privada
            password: Contraseña para descifrar la clave (si está cifrada)

        Returns:
            Clave privada cargada o None si hay error
        """
        try:
            if not os.path.exists(filepath):
                print(f"Error: Archivo no encontrado: {filepath}")
                return None

            with open(filepath, 'rb') as f:
                pem_data = f.read()

            self.private_key = serialization.load_pem_private_key(
                pem_data,
                password=password,
                backend=default_backend()
            )

            # Extraer clave pública de la privada
            self.public_key = self.private_key.public_key()

            print(f"Clave privada cargada desde: {filepath}")
            return self.private_key

        except Exception as e:
            print(f"Error al cargar clave privada: {e}")
            return None

    def load_public_key(self, filepath: str) -> Optional[rsa.RSAPublicKey]:
        """
        Carga una clave pública desde un archivo PEM

        Args:
            filepath: Ruta al archivo de clave pública

        Returns:
            Clave pública cargada o None si hay error
        """
        try:
            if not os.path.exists(filepath):
                print(f"Error: Archivo no encontrado: {filepath}")
                return None

            with open(filepath, 'rb') as f:
                pem_data = f.read()

            self.public_key = serialization.load_pem_public_key(
                pem_data,
                backend=default_backend()
            )

            print(f"Clave pública cargada desde: {filepath}")
            return self.public_key

        except Exception as e:
            print(f"Error al cargar clave pública: {e}")
            return None

    def get_public_key_fingerprint(self) -> Optional[str]:
        """
        Obtiene la huella digital (fingerprint) de la clave pública

        Returns:
            Fingerprint en formato hexadecimal o None si no hay clave
        """
        if not self.public_key:
            return None

        try:
            # Serializar clave pública
            pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # Calcular hash SHA-256
            from cryptography.hazmat.primitives import hashes
            digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
            digest.update(pem)
            fingerprint = digest.finalize()

            # Convertir a hexadecimal
            return fingerprint.hex()

        except Exception as e:
            print(f"Error al calcular fingerprint: {e}")
            return None

    @staticmethod
    def verify_key_files_exist(private_key_path: str, public_key_path: str) -> bool:
        """
        Verifica si existen los archivos de claves

        Args:
            private_key_path: Ruta a la clave privada
            public_key_path: Ruta a la clave pública

        Returns:
            True si ambos archivos existen
        """
        return os.path.exists(private_key_path) and os.path.exists(public_key_path)

    @staticmethod
    def generate_and_save_keys(
        private_key_path: str,
        public_key_path: str,
        key_size: int = 2048,
        password: Optional[bytes] = None
    ) -> bool:
        """
        Genera un nuevo par de claves y las guarda en archivos

        Args:
            private_key_path: Ruta donde guardar la clave privada
            public_key_path: Ruta donde guardar la clave pública
            key_size: Tamaño de la clave en bits
            password: Contraseña para cifrar la clave privada (opcional)

        Returns:
            True si se generaron y guardaron correctamente
        """
        try:
            manager = KeyManager(key_size)
            manager.generate_key_pair()

            if not manager.save_private_key(private_key_path, password):
                return False

            if not manager.save_public_key(public_key_path):
                return False

            print("Par de claves generado y guardado correctamente")
            return True

        except Exception as e:
            print(f"Error al generar y guardar claves: {e}")
            return False
