import asyncio
import websockets
from src.config.config import Config
from src.security.ssl_manager import SSLManager
from src.security.validacion_integridad import ValidadorIntegridad

class ClienteChat:
    def __init__(self):
        self.host = Config.SERVER_HOST
        self.puerto = Config.SERVER_PORT
        self.websocket = None
        self.nombre = ""
        self.conectado = False
        self.cifrador = None
        self.es_asimetrico = False
        
    def configurar_cifrador(self, tipo_cifrado):
        if tipo_cifrado == "simetrico":
            from src.crypto.cifrado_simetrico import Cifrador
            self.cifrador = Cifrador()
            self.es_asimetrico = False
        else:
            from src.crypto.cifrado_asimetrico import Cifrador
            self.cifrador = Cifrador(es_servidor=False)
            self.es_asimetrico = True
    
    async def conectar(self):
        try:
            contexto_ssl = SSLManager.crear_contexto_ssl_cliente()
            if not contexto_ssl:
                print("Error: No se pudo crear el contexto SSL para el cliente")
                return False
            
            uri = f"wss://{self.host}:{self.puerto}"
            print(f"Conectando a {uri}...")
            
            self.websocket = await websockets.connect(uri, ssl=contexto_ssl)
            
            respuesta = await self.websocket.recv()
            
            # Recibir configuracion del servidor y adaptarse
            if respuesta.startswith("CONFIG:"):
                modo = respuesta.split(":", 1)[1].strip().upper()
                tipo_cifrado = "asimetrico" if modo == "ASIMETRICO" else "simetrico"
                self.configurar_cifrador(tipo_cifrado)
                # esperar la siguiente orden
                respuesta = await self.websocket.recv()
            
            if respuesta == "NOMBRE_USUARIO":
                while True:
                    self.nombre = input("Ingresa tu nombre: ").strip()
                    if not self.nombre:
                        print("Por favor ingresa un nombre valido.")
                        continue
                    
                    nombre_cifrado = self.cifrador.cifrar_mensaje(self.nombre)
                    if not nombre_cifrado:
                        print("Error al cifrar el nombre. Intenta de nuevo.")
                        continue
                    
                    nombre_con_hash = ValidadorIntegridad.agregar_hash(self.nombre, nombre_cifrado)
                    if not nombre_con_hash:
                        print("Error al agregar validacion de integridad. Intenta de nuevo.")
                        continue
                    
                    await self.websocket.send(nombre_con_hash)
                    
                    confirmacion = await self.websocket.recv()
                    
                    if confirmacion == "CONECTADO":
                        print("\nBienvenido al chat!")
                        tipo_cifrado = "Asimetrico (RSA)" if self.es_asimetrico else "Simetrico (Fernet)"
                        print(f"Tipo de cifrado: {tipo_cifrado}")
                        print("Protocolo: WSS (WebSocket Secure)")
                        print("Comandos disponibles: /hist, /list, /quit, /help")
                        print("Escribe tus mensajes:")
                        print("-" * 50)
                        self.conectado = True
                        return True
                    
                    elif confirmacion == "NOMBRE_INVALIDO":
                        print("Nombre invalido. Use solo letras, numeros, guiones y acentos (2-20 caracteres).")
                        continue
                    
                    elif confirmacion == "NOMBRE_EN_USO":
                        print("Ese nombre ya esta en uso. Por favor elige otro.")
                        continue
                    
                    elif confirmacion == "INTEGRIDAD_FALLIDA":
                        print("Error de integridad en la comunicacion. Intenta de nuevo.")
                        continue
                    
                    else:
                        print("Error inesperado del servidor")
                        return False
            else:
                print("Error en la comunicacion con el servidor")
                return False
        
        except ConnectionRefusedError:
            print("Error: No se pudo conectar al servidor. Esta el servidor ejecutandose?")
            return False
        except Exception as e:
            print(f"Error de conexion: {e}")
            return False
    
    async def escuchar_servidor(self):
        try:
            async for mensaje in self.websocket:
                try:
                    if mensaje == "SPAM_DETECTADO":
                        print("Anti-spam: Espera 2 segundos entre mensajes")
                    elif mensaje == "MENSAJE_INVALIDO":
                        print("Mensaje invalido")
                    elif mensaje == "INTEGRIDAD_FALLIDA":
                        print("Su mensaje no pudo ser enviado (error de integridad)")
                    elif mensaje.startswith("COMANDO_RESPUESTA:"):
                        respuesta = mensaje.replace("COMANDO_RESPUESTA:", "")
                        print(respuesta)
                    elif mensaje.startswith("MENSAJE_CHAT:"):
                        try:
                            datos = mensaje.replace("MENSAJE_CHAT:", "")
                            partes = datos.split("###SEP###")
                            
                            if len(partes) == 4:
                                ip_parte, puerto_parte, nombre_parte, mensaje_parte = partes
                                
                                if self.es_asimetrico:
                                    ip = ip_parte
                                    puerto = puerto_parte
                                    nombre = nombre_parte
                                    mensaje_texto = mensaje_parte
                                else:
                                    ip = self.cifrador.descifrar_mensaje(ip_parte)
                                    puerto = self.cifrador.descifrar_mensaje(puerto_parte)
                                    nombre = self.cifrador.descifrar_mensaje(nombre_parte)
                                    mensaje_texto = self.cifrador.descifrar_mensaje(mensaje_parte)
                                
                                if mensaje_texto == "DESCONEXION_CLIENTE":
                                    continue
                                
                                if ip and puerto and nombre and mensaje_texto:
                                    print(f"[{ip}, {puerto}, {nombre}] {mensaje_texto}")
                                else:
                                    print("Error al descifrar mensaje del servidor")
                            else:
                                print("Formato de mensaje incorrecto")
                        except Exception as e:
                            print(f"Error procesando mensaje cifrado: {e}")
                    
                    elif mensaje == "El servidor se esta cerrando. Conexion terminada.":
                        print("\n " + mensaje)
                        self.conectado = False
                        break
                    else:
                        print(f"Sistema: {mensaje}")
                
                except Exception as e:
                    print(f"Error procesando mensaje: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            print("\n Conexion con el servidor perdida.")
            self.conectado = False
        except Exception as e:
            if self.conectado:
                print(f"Error recibiendo mensaje: {e}")
            self.conectado = False
    
    async def enviar_mensajes(self):
        try:
            while self.conectado:
                try:
                    mensaje = await asyncio.get_event_loop().run_in_executor(None, input)
                    
                    if mensaje.strip() == "":
                        continue
                    
                    if mensaje.lower() == "/quit":
                        await self.desconectar()
                        break
                    
                    mensaje_cifrado = self.cifrador.cifrar_mensaje(mensaje)
                    
                    if not mensaje_cifrado:
                        print("Error al cifrar mensaje. Intenta de nuevo.")
                        continue
                    
                    mensaje_con_hash = ValidadorIntegridad.agregar_hash(mensaje, mensaje_cifrado)
                    
                    if not mensaje_con_hash:
                        print("Error al agregar validacion de integridad. Intenta de nuevo.")
                        continue
                    
                    await self.websocket.send(mensaje_con_hash)
                    
                    if not mensaje.startswith('/'):
                        print(f"Tu: {mensaje}")
                
                except Exception as e:
                    if self.conectado:
                        print(f"Error enviando mensaje: {e}")
                    break
        
        except Exception as e:
            print(f"Error en enviar_mensajes: {e}")
    
    async def desconectar(self):
        if self.conectado and self.websocket:
            try:
                mensaje_desconexion_cifrado = self.cifrador.cifrar_mensaje("DESCONEXION_CLIENTE")
                mensaje_desconexion_con_hash = ValidadorIntegridad.agregar_hash("DESCONEXION_CLIENTE", mensaje_desconexion_cifrado)
                await self.websocket.send(mensaje_desconexion_con_hash)
            except:
                pass
        
        self.conectado = False
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
        print("Desconectado del servidor")
    
    async def iniciar(self):
        print("\n" + "="*70)
        print("CLIENTE DE CHAT SEGURO")
        print("="*70)
        # Ya no se selecciona manualmente; el cliente se adapta a la CONFIG del servidor
        
        if not await self.conectar():
            return
        
        tarea_escuchar = asyncio.create_task(self.escuchar_servidor())
        tarea_enviar = asyncio.create_task(self.enviar_mensajes())
        
        try:
            await asyncio.gather(tarea_escuchar, tarea_enviar)
        except KeyboardInterrupt:
            await self.desconectar()


async def main():
    try:
        cliente = ClienteChat()
        await cliente.iniciar()
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario.")
    except Exception as e:
        print(f"Error fatal: {e}")
    finally:
        print("Cliente terminado.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPrograma terminado por el usuario")