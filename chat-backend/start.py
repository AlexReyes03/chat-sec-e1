"""
Script de Inicio del Sistema
=============================

Inicia el servidor unificado CHATSEC v5.0:
- Servidor HTTP/REST API en puerto 5000
- WebSocket para chat en puerto 5000/ws/chat
- Autenticación JWT
- Firma digital de PDFs

Uso:
    python start.py [opciones]

Opciones:
    --auth          Ejecutar flujo de autenticación con Google primero
    --init-db       Inicializar base de datos MySQL
"""

import sys
import subprocess
import argparse
import time
from pathlib import Path


def print_banner():
    """Imprime el banner de inicio"""
    print("\n" + "="*70)
    print("CHATSEC - CHAT SEGURO CON FIRMA DIGITAL")
    print("="*70)
    print("Versión 5.0 - Servidor Unificado")
    print("="*70 + "\n")


def run_google_auth():
    """Ejecuta el flujo de autenticación con Google"""
    print("\n" + "="*70)
    print("AUTENTICACIÓN CON GOOGLE")
    print("="*70)
    print("\nIniciando flujo de autenticación OAuth 2.0...")
    print("Se abrirá tu navegador para autorizar la aplicación.\n")

    try:
        subprocess.run([sys.executable, "authenticate_google.py"], check=True)
        print("\nAutenticacion completada exitosamente")
        return True
    except subprocess.CalledProcessError:
        print("\nError en la autenticacion")
        return False
    except FileNotFoundError:
        print("\nArchivo authenticate_google.py no encontrado")
        return False


def init_database():
    """Inicializa la base de datos MySQL"""
    print("\n" + "="*70)
    print("INICIALIZACIÓN DE BASE DE DATOS")
    print("="*70)
    print("\nEjecutando script de inicialización...\n")

    try:
        subprocess.run([sys.executable, "init_database.py"], check=True)
        print("\nBase de datos inicializada exitosamente")
        return True
    except subprocess.CalledProcessError:
        print("\nError al inicializar base de datos")
        return False
    except FileNotFoundError:
        print("\nArchivo init_database.py no encontrado")
        return False


def start_unified_server():
    """Inicia el servidor unificado (REST API + WebSocket)"""
    print("\n[SERVIDOR] Iniciando servidor unificado...")
    return subprocess.Popen(
        [sys.executable, "unified_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )


def monitor_process(process, name):
    """Monitorea la salida de un proceso"""
    try:
        for line in process.stdout:
            print(f"[{name}] {line}", end='')
    except KeyboardInterrupt:
        pass


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Inicia el servidor unificado CHATSEC"
    )
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Inicializar base de datos MySQL antes de iniciar'
    )
    parser.add_argument(
        '--auth',
        action='store_true',
        help='Ejecutar autenticación con Google antes de iniciar'
    )

    args = parser.parse_args()

    print_banner()

    # Inicializar base de datos si se solicita
    if args.init_db:
        if not init_database():
            print("\nAdvertencia: Continuar sin base de datos inicializada.")
            print("Algunas funcionalidades pueden no estar disponibles.\n")
            time.sleep(2)

    # Autenticación con Google si se solicita
    if args.auth:
        if not run_google_auth():
            print("\nAdvertencia: Continuar sin autenticación de Google.")
            print("La firma de PDFs no estará disponible sin Google Drive.\n")
            time.sleep(2)

    processes = []

    try:
        print("\n" + "="*70)
        print("INICIANDO SERVIDOR UNIFICADO")
        print("="*70)
        print("\nPresiona Ctrl+C para detener el servidor\n")

        # Iniciar servidor unificado
        server_process = start_unified_server()
        processes.append(('SERVIDOR', server_process))

        # Información de acceso
        time.sleep(3)
        print("\n" + "="*70)
        print("SERVIDOR INICIADO")
        print("="*70)
        print("\nServidor HTTP/REST API:")
        print("   http://localhost:5000")
        print("   Documentacion: http://localhost:5000/docs")
        print("\nWebSocket para Chat:")
        print("   ws://localhost:5000/ws/chat")
        print("\nFrontend React:")
        print("   http://localhost:3000 o http://localhost:5173")
        print("   (ejecutar: cd ../chat-frontend && npm run dev)")
        print("\n" + "="*70)
        print("Presiona Ctrl+C para detener el servidor")
        print("="*70 + "\n")

        # Mantener proceso vivo
        while True:
            time.sleep(1)
            # Verificar si el proceso murió
            if server_process.poll() is not None:
                print("\n[SERVIDOR] Proceso terminado inesperadamente")
                raise KeyboardInterrupt

    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("DETENIENDO SERVIDORES")
        print("="*70)

        # Terminar todos los procesos
        for name, proc in processes:
            print(f"\n[{name}] Deteniendo servidor...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
                print(f"[{name}] Servidor detenido")
            except subprocess.TimeoutExpired:
                print(f"[{name}] Forzando cierre...")
                proc.kill()

        print("\n" + "="*70)
        print("TODOS LOS SERVIDORES DETENIDOS")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\nError: {e}")
        # Terminar procesos en caso de error
        for name, proc in processes:
            proc.terminate()


if __name__ == "__main__":
    main()
