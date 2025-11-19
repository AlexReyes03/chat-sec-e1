import hashlib


class ValidadorIntegridad:
    """
    Clase para validar la integridad de mensajes usando SHA-256
    Compatible con cifrado simetrico y asimetrico
    """

    @staticmethod
    def calcular_hash(mensaje):
        try:
            mensaje_bytes = mensaje.encode('utf-8')
            hash_objeto = hashlib.sha256(mensaje_bytes)
            return hash_objeto.hexdigest()
        except Exception as e:
            print(f"Error calculando hash: {e}")
            return None

    @staticmethod
    def agregar_hash(mensaje, mensaje_cifrado):
        try:
            hash_sha256 = ValidadorIntegridad.calcular_hash(mensaje)
            if not hash_sha256:
                return None
            return f"{mensaje_cifrado}|||HASH|||{hash_sha256}"
        except Exception as e:
            print(f"Error agregando hash: {e}")
            return None

    @staticmethod
    def validar_y_extraer(mensaje_con_hash):
        try:
            if "|||HASH|||" not in mensaje_con_hash:
                return None, False
            partes = mensaje_con_hash.split("|||HASH|||")
            if len(partes) != 2:
                return None, False
            mensaje_cifrado = partes[0]
            hash_recibido = partes[1]
            if not hash_recibido or len(hash_recibido) != 64:
                return None, False
            return mensaje_cifrado, True
        except Exception as e:
            print(f"Error extrayendo hash: {e}")
            return None, False

    @staticmethod
    def validar_integridad(mensaje_descifrado, hash_recibido):
        try:
            hash_calculado = ValidadorIntegridad.calcular_hash(mensaje_descifrado)
            if not hash_calculado:
                return False
            return hash_calculado == hash_recibido
        except Exception as e:
            print(f"Error validando integridad: {e}")
            return False


if __name__ == "__main__":
    print("Probando modulo de validacion de integridad...")
    mensaje_original = "Hola mundo!"
    print(f"\nMensaje original: {mensaje_original}")
    hash_calculado = ValidadorIntegridad.calcular_hash(mensaje_original)
    print(f"Hash SHA-256: {hash_calculado}")
    mensaje_cifrado_simulado = "gAAAAABmX1Y2Z3..."
    mensaje_con_hash = ValidadorIntegridad.agregar_hash(mensaje_original, mensaje_cifrado_simulado)
    print(f"\nMensaje con hash: {mensaje_con_hash[:50]}...")
    mensaje_extraido, hash_valido = ValidadorIntegridad.validar_y_extraer(mensaje_con_hash)
    print(f"\nMensaje extraido: {mensaje_extraido[:30]}...")
    print(f"Formato valido: {hash_valido}")
    hash_recibido = mensaje_con_hash.split("|||HASH|||")[1]
    integridad_ok = ValidadorIntegridad.validar_integridad(mensaje_original, hash_recibido)
    print(f"\nIntegridad validada: {integridad_ok}")
    print("\n--- Prueba de mensaje modificado ---")
    mensaje_modificado = "Hola mundo modificado!"
    integridad_modificado = ValidadorIntegridad.validar_integridad(mensaje_modificado, hash_recibido)
    print(f"Integridad de mensaje modificado: {integridad_modificado}")


