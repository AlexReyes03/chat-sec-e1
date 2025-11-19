import re
import time


def validar_mensaje(mensaje):
    if not mensaje or not mensaje.strip():
        return None

    mensaje = mensaje.strip()

    if len(mensaje) > 200:
        mensaje = mensaje[:200]

    mensaje = limpiar_caracteres_repetidos(mensaje)

    mensaje = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', mensaje)

    return mensaje if mensaje.strip() else None


def limpiar_caracteres_repetidos(texto):
    resultado = ""
    char_anterior = ""
    contador = 0

    for char in texto:
        if char.lower() == char_anterior.lower() and char.isalpha():
            contador += 1
            if contador <= 5:
                resultado += char
        else:
            contador = 1
            resultado += char
        char_anterior = char

    final = ""
    char_anterior = ""
    contador = 0

    for char in resultado:
        if char.lower() == char_anterior.lower() and char.isalpha():
            contador += 1
            if contador > 5:
                continue
            else:
                final += char
        else:
            if contador > 5 and char_anterior:
                if not final.endswith(char_anterior):
                    final += char_anterior
            contador = 1
            final += char
        char_anterior = char

    if contador > 5 and char_anterior:
        while final.endswith(char_anterior) and final.count(char_anterior[-1:]) > 1:
            final = final[:-1]

    return final


def es_comando(mensaje):
    return mensaje.strip().startswith('/')


def procesar_comando(comando, clientes, historial):
    comando = comando.strip().lower()

    if comando == "/hist":
        if not historial:
            return "No hay mensajes en el historial"

        respuesta = "Historial de mensajes (últimos 10):\n"
        for item in historial:
            if len(item) == 5:
                timestamp, nombre, ip, puerto, mensaje = item
                tiempo_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
                respuesta += f"[{tiempo_str}] [{ip}, {puerto}, {nombre}] {mensaje}\n"
            else:
                timestamp, nombre, mensaje = item
                tiempo_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
                respuesta += f"[{tiempo_str}] {nombre}: {mensaje}\n"
        return respuesta.strip()

    elif comando == "/list":
        if not clientes:
            return " No hay usuarios conectados"

        respuesta = f"Usuarios conectados ({len(clientes)}):\n"
        for i, info in enumerate(clientes.values(), 1):
            nombre = info['nombre']
            ip = info['ip']
            puerto = info.get('puerto', 'N/A')
            respuesta += f"{i}. [{ip}, {puerto}, {nombre}]\n"
        return respuesta.strip()

    elif comando == "/help":
        return """Comandos disponibles:
/hist - Ver historial de mensajes
/list - Ver usuarios conectados
/quit - Salir del chat
/help - Mostrar esta ayuda"""

    else:
        return "Comando no reconocido. Usa /help para ver comandos disponibles"


def validar_nombre_usuario(nombre):
    if not nombre or not nombre.strip():
        return False

    nombre = nombre.strip()

    if len(nombre) < 2 or len(nombre) > 20:
        return False

    if not re.match(r'^[a-zA-Z0-9_\-áéíóúÁÉÍÓÚñÑ]+$', nombre):
        return False

    return True


