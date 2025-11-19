import asyncio
import websockets
import time
from src.utils.utils import validar_mensaje, es_comando, procesar_comando
from src.config.config import Config
from src.security.ssl_manager import SSLManager
from src.security.validacion_integridad import ValidadorIntegridad

class ServidorChat:
    def __init__(self):
        self.host = Config.SERVER_HOST
        self.puerto = Config.SERVER_PORT
        self.clientes = {}
        self.historial = []
        self.servidor_activo = True
        self.cifrador = None
        self.tipo_cifrado = None
        self.servidor_websocket = None
        
    def seleccionar_cifrado(self):
        print("\n" + "="*70)
        print("CONFIGURACION DE CIFRADO")
        print("="*70)
        
        print("\nSelecciona el tipo de cifrado a utilizar:")
        print("1. Cifrado Simetrico (Fernet/AES-128)")
        print("2. Cifrado Asimetrico (RSA-2048)")
        
        while True:
            try:
                opcion = input("\nOpcion (1-2): ").strip()
                if opcion == "1":
                    self.tipo_cifrado = "simetrico"
                    break
                elif opcion == "2":
                    self.tipo_cifrado = "asimetrico"
                    break
                else:
                    print("Opcion invalida. Selecciona 1 o 2")
            except KeyboardInterrupt:
                print("\n\nConfiguracion cancelada")
                return False
        
        print(f"\nTipo de cifrado seleccionado: {self.tipo_cifrado.upper()}")
        
        if self.tipo_cifrado == "simetrico":
            from src.crypto.cifrado_simetrico import Cifrador
            self.cifrador = Cifrador()
            self.es_asimetrico = False
        else:
            from src.crypto.cifrado_asimetrico import Cifrador
            self.cifrador = Cifrador(es_servidor=True)
            self.es_asimetrico = True
        
        print("Cifrador inicializado correctamente")
        return True
    
    def configurar_ssl(self):
        print("\n" + "="*70)
        print("CONFIGURACION SSL/TLS")
        print("="*70)
        
        cert_file = Config.SSL_CERT_FILE
        key_file = Config.SSL_KEY_FILE
        
        if Config.SSL_AUTO_GENERAR:
            print("\nGenerando certificados SSL autofirmados...")
            if not SSLManager.verificar_certificados_existen(cert_file, key_file):
                if not SSLManager.generar_certificado_autofirmado(
                    cert_file, key_file, Config.SSL_CERT_VALIDITY_DAYS
                ):
                    print("Error: No se pudieron generar los certificados SSL")
                    return None
            else:
                print(f"Certificados SSL existentes encontrados:")
                print(f"  Certificado: {cert_file}")
                print(f"  Clave: {key_file}")
        
        contexto_ssl = SSLManager.crear_contexto_ssl_servidor(cert_file, key_file)
        if not contexto_ssl:
            print("Error: No se pudo crear el contexto SSL")
            return None
        
        print("Contexto SSL creado exitosamente")
        return contexto_ssl
    
    async def iniciar_servidor(self):
        if not self.seleccionar_cifrado():
            return
        
        contexto_ssl = self.configurar_ssl()
        if not contexto_ssl:
            print("Error: No se pudo configurar SSL/TLS")
            return
        
        print("\n" + "="*70)
        print("SERVIDOR INICIADO")
        print("="*70)
        print(f"Escuchando en: wss://{self.host}:{self.puerto}")
        tipo_cifrado_str = "Asimetrico (RSA)" if self.es_asimetrico else "Simetrico (Fernet)"
        print(f"Tipo de cifrado: {tipo_cifrado_str}")
        print("Validacion de integridad: SHA-256 activa")
        print("Comandos del servidor: /shutdown - Cerrar servidor")
        print("-" * 70)
        print("Escribe comandos en la terminal del servidor (ej: /shutdown)")
        
        asyncio.create_task(self.manejar_comandos_servidor())
        
        async with websockets.serve(
            self.manejar_cliente,
            self.host,
            self.puerto,
            ssl=contexto_ssl
        ) as servidor:
            self.servidor_websocket = servidor
            # Esperar hasta que el servidor se cierre
            while self.servidor_activo:
                await asyncio.sleep(0.1)
    
    async def manejar_comandos_servidor(self):
        while self.servidor_activo:
            try:
                # Leer comandos de la terminal de manera asíncrona
                loop = asyncio.get_event_loop()
                comando = await loop.run_in_executor(None, input)
                
                if not comando or not comando.strip():
                    continue
                
                comando = comando.strip()
                
                if comando.lower() == "/shutdown":
                    print("\nIniciando cierre del servidor...")
                    await self.cerrar_servidor()
                    break
                elif comando.lower() == "/help":
                    print("\nComandos disponibles:")
                    print("  /shutdown - Cerrar el servidor y desconectar todos los clientes")
                    print("  /help - Mostrar esta ayuda")
                else:
                    print(f"Comando no reconocido: {comando}. Usa /help para ver comandos disponibles.")
                
            except EOFError:
                # Ctrl+D o fin de entrada
                break
            except Exception as e:
                if self.servidor_activo:
                    print(f"Error en manejar_comandos_servidor: {e}")
                await asyncio.sleep(0.1)
    
    async def manejar_cliente(self, websocket):
        cliente_ip = websocket.remote_address[0]
        cliente_puerto = websocket.remote_address[1]
        
        print(f"Nueva conexion desde {cliente_ip}:{cliente_puerto} - Procesando registro...")
        
        try:
            # Informar al cliente el tipo de cifrado del servidor para que se adapte
            await websocket.send(f"CONFIG:{'ASIMETRICO' if self.es_asimetrico else 'SIMETRICO'}")
            await websocket.send("NOMBRE_USUARIO")
            
            nombre_con_hash = await asyncio.wait_for(websocket.recv(), timeout=30.0)
            
            if not nombre_con_hash or not self.servidor_activo:
                await websocket.close()
                return
            
            nombre_cifrado, hash_valido = ValidadorIntegridad.validar_y_extraer(nombre_con_hash)
            
            if not hash_valido:
                await websocket.send("INTEGRIDAD_FALLIDA")
                await websocket.close()
                print(f"[INTEGRIDAD] Registro rechazado desde {cliente_ip}: formato de hash invalido")
                return
            
            nombre = self.cifrador.descifrar_mensaje(nombre_cifrado)
            
            if not nombre:
                await websocket.send("NOMBRE_INVALIDO")
                await websocket.close()
                print(f"Registro rechazado desde {cliente_ip}: error al descifrar nombre")
                return
            
            hash_recibido = nombre_con_hash.split("|||HASH|||")[1]
            if not ValidadorIntegridad.validar_integridad(nombre, hash_recibido):
                await websocket.send("INTEGRIDAD_FALLIDA")
                await websocket.close()
                print(f"[INTEGRIDAD] Registro rechazado desde {cliente_ip}: hash SHA-256 no coincide")
                return
            
            from src.utils.utils import validar_nombre_usuario
            if not validar_nombre_usuario(nombre):
                await websocket.send("NOMBRE_INVALIDO")
                await websocket.close()
                print(f"Registro rechazado desde {cliente_ip}: nombre invalido '{nombre}'")
                return
            
            nombres_en_uso = [info['nombre'].lower() for info in self.clientes.values()]
            if nombre.lower() in nombres_en_uso:
                await websocket.send("NOMBRE_EN_USO")
                await websocket.close()
                print(f"Registro rechazado desde {cliente_ip}: nombre '{nombre}' ya esta en uso")
                return
            
            self.clientes[websocket] = {
                'nombre': nombre,
                'ip': cliente_ip,
                'puerto': cliente_puerto,
                'ultimo_mensaje': 0
            }
            
            print(f"Cliente registrado exitosamente: {nombre} desde {cliente_ip}:{cliente_puerto}")
            
            await websocket.send("CONECTADO")
            
            mensaje_conexion = f"{nombre} se ha unido al chat"
            await self.enviar_a_todos(mensaje_conexion, excluir=websocket)
            
            await self.procesar_mensajes_cliente(websocket)
            
        except asyncio.TimeoutError:
            print(f"Timeout en registro desde {cliente_ip} - conexion cerrada")
            try:
                await websocket.close()
            except:
                pass
        except Exception as e:
            print(f"Error procesando nuevo cliente desde {cliente_ip}: {e}")
            try:
                await websocket.close()
            except:
                pass
    
    async def procesar_mensajes_cliente(self, websocket):
        try:
            async for mensaje_con_hash in websocket:
                try:
                    if not self.servidor_activo:
                        break
                    
                    if websocket not in self.clientes:
                        break
                    
                    mensaje_cifrado, hash_valido = ValidadorIntegridad.validar_y_extraer(mensaje_con_hash)
                    
                    if not hash_valido:
                        await websocket.send("INTEGRIDAD_FALLIDA")
                        continue
                    
                    mensaje = self.cifrador.descifrar_mensaje(mensaje_cifrado)
                    
                    if not mensaje:
                        await websocket.send("MENSAJE_INVALIDO")
                        continue
                    
                    hash_recibido = mensaje_con_hash.split("|||HASH|||")[1]
                    if not ValidadorIntegridad.validar_integridad(mensaje, hash_recibido):
                        info_cliente = self.clientes[websocket]
                        print(f"[INTEGRIDAD] Mensaje rechazado de {info_cliente['nombre']}: hash SHA-256 no coincide")
                        await websocket.send("INTEGRIDAD_FALLIDA")
                        continue
                    
                    if mensaje == "DESCONEXION_CLIENTE":
                        break
                    
                    info_cliente = self.clientes[websocket]
                    nombre = info_cliente['nombre']
                    ip = info_cliente['ip']
                    puerto = info_cliente['puerto']
                    
                    tiempo_actual = time.time()
                    if tiempo_actual - info_cliente['ultimo_mensaje'] < 2:
                        await websocket.send("SPAM_DETECTADO")
                        continue
                    
                    if es_comando(mensaje):
                        respuesta = procesar_comando(mensaje, self.clientes, self.historial)
                        await websocket.send(f"COMANDO_RESPUESTA:{respuesta}")
                        continue
                    
                    mensaje_limpio = validar_mensaje(mensaje)
                    if not mensaje_limpio:
                        await websocket.send("MENSAJE_INVALIDO")
                        continue
                    
                    info_cliente['ultimo_mensaje'] = tiempo_actual
                    
                    if self.es_asimetrico:
                        mensaje_completo = f"MENSAJE_CHAT:{ip}###SEP###{puerto}###SEP###{nombre}###SEP###{mensaje_limpio}"
                        
                        print("\n\nDATOS ENVIADOS (sin cifrar, RSA solo Cliente->Servidor):")
                        print(f"[{ip}, {puerto}, {nombre}] {mensaje_limpio}")
                    else:
                        nombre_cifrado, ip_cifrada, puerto_cifrado = self.cifrador.cifrar_datos_usuario(nombre, ip, puerto)
                        mensaje_cifrado_enviar = self.cifrador.cifrar_mensaje(mensaje_limpio)
                        
                        print("\n\nDATOS CIFRADOS:")
                        print(f"[{ip_cifrada[:20]}..., {puerto_cifrado[:20]}..., {nombre_cifrado[:20]}...] {mensaje_cifrado_enviar[:30]}...")
                        print("\nDATOS DESCIFRADOS:")
                        print(f"[{ip}, {puerto}, {nombre}] {mensaje_limpio}")
                        
                        mensaje_completo = f"MENSAJE_CHAT:{ip_cifrada}###SEP###{puerto_cifrado}###SEP###{nombre_cifrado}###SEP###{mensaje_cifrado_enviar}"
                    
                    self.historial.append((tiempo_actual, nombre, ip, puerto, mensaje_limpio))
                    if len(self.historial) > 10:
                        self.historial.pop(0)
                    
                    await self.enviar_a_todos(mensaje_completo, excluir=websocket)
                    
                except Exception as e:
                    if self.servidor_activo:
                        print(f"Error procesando mensaje: {e}")
                    break
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            if self.servidor_activo:
                print(f"Error en procesar_mensajes_cliente: {e}")
        finally:
            await self.desconectar_cliente(websocket)
    
    async def enviar_a_todos(self, mensaje, excluir=None):
        clientes_desconectados = []
        
        for websocket in list(self.clientes.keys()):
            if websocket == excluir:
                continue
            
            try:
                await websocket.send(mensaje)
            except:
                clientes_desconectados.append(websocket)
        
        for websocket in clientes_desconectados:
            await self.desconectar_cliente(websocket)
    
    async def desconectar_cliente(self, websocket):
        try:
            if websocket in self.clientes:
                info_cliente = self.clientes[websocket]
                nombre = info_cliente['nombre']
                print(f"Cliente desconectado: {nombre}")
                
                if self.servidor_activo:
                    mensaje_desconexion = f"{nombre} ha salido del chat"
                    await self.enviar_a_todos(mensaje_desconexion, excluir=websocket)
                
                del self.clientes[websocket]
            
            await websocket.close()
        except:
            pass
    
    async def cerrar_servidor(self):
        """Cierra el servidor y desconecta todos los clientes"""
        print("\nCerrando servidor...")
        self.servidor_activo = False
        
        mensaje_cierre = "El servidor se esta cerrando. Conexion terminada."
        
        # Desconectar todos los clientes
        clientes_desconectar = list(self.clientes.keys())
        for websocket in clientes_desconectar:
            try:
                await websocket.send(mensaje_cierre)
                await websocket.close()
            except:
                pass
        
        self.clientes.clear()
        
        # Cerrar el servidor
        if self.servidor_websocket:
            try:
                self.servidor_websocket.close()
                # Esperar un poco para que el servidor se cierre correctamente
                await asyncio.sleep(0.5)
            except:
                pass
        
        print("Servidor cerrado correctamente.")


async def main():
    try:
        servidor = ServidorChat()
        await servidor.iniciar_servidor()
    except KeyboardInterrupt:
        print("\n\nServidor interrumpido por el usuario")
    except Exception as e:
        print(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Servidor terminado.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPrograma terminado por el usuario")