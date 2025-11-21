# Sistema de Chat con Cifrado

## Descripción del Proyecto

Sistema de chat multiusuario cliente-servidor desarrollado en Python con soporte para cifrado simétrico (Fernet/AES) y cifrado asimétrico (RSA). Permite comunicación segura entre múltiples clientes a través de una red con validación de integridad de mensajes mediante SHA-256.

---

## Historial de Versiones

### Versión 1.0 - Sistema Base

**Fecha:** 28/09/2025
**Estado:** Deprecado

#### Características

- Chat multiusuario
- Comunicación cliente-servidor
- Comandos básicos (/hist, /list, /help, /quit)
- Anti-spam (2 segundos entre mensajes)
- Validación de nombres de usuario
- Historial de mensajes (últimos 10)

#### Archivos

- `Servidor.py` - 9d3deefc1dcd0126cd27e2dd2b141538  - Servidor principal
- `Clientes.py` - bbeff2536122ffa41fb3f54a23091a50  - Cliente de chat
- `utils.py` - 23a938ee4a1cd187f1861f056f49e20d - Utilidades y validaciones

---

### Versión 2.0 - Sistema con Cifrado

**Fecha:** 11/10/2025
**Estado:** Deprecado

#### Cambios Principales

- Implementación de cifrado simétrico usando Fernet (AES-128)
- Implementación de cifrado asimétrico usando RSA-2048
- Uso de PBKDF2 con SHA-256 para derivación de claves
- Uso de OAEP con SHA-256 para padding en RSA
- Separación de módulos de cifrado en archivos independientes

#### Archivos Nuevos

- `cifrado_simetrico.py` - becf298b6719bc19cd714dce1a2103ab - Módulo de cifrado simétrico con Fernet
- `cifrado_asimetrico.py` - a3d1edbafb7c7a01fdda8c5a35bac0e4 - Módulo de cifrado asimétrico con RSA
- `pruebas_cifrado.py` - Suite de pruebas automatizadas
- `requirements.txt` - e6afd56cd80effd76d645f19ce47deb2 - Dependencias del proyecto

#### Archivos Modificados

- `Servidor.py` - 407dbf61eb3ae05be7295d79015fc26c - Integración con módulos de cifrado
- `Clientes.py` - 937c31e7b3f797e6ea203fe98326e669 - Integración con módulos de cifrado
- `utils.py` - 41e9af505672b77256b01e0dfca8e32a - Mejoras en validación de datos

#### Características

- **Cifrado Simétrico:** Fernet (AES-128 CBC + HMAC SHA-256)
- **Cifrado Asimétrico:** RSA-2048 con OAEP SHA-256
- **Hash:** SHA-256 para integridad
- **KDF:** PBKDF2 con 100,000 iteraciones

---

### Versión 3.0 - Sistema con Validación de Integridad

**Fecha:** 23/10/2025  
**Estado:** Producción

#### Cambios Principales

- Implementación de validación de integridad con SHA-256
- Detección automática de mensajes modificados en tránsito
- Protección contra ataques Man-in-the-Middle (MITM)
- Validación de nombres de usuario, mensajes y comandos
- Logs detallados de eventos de integridad en servidor
- Protección contra inyección de comandos maliciosos
- Protección contra corrupción de datos en transmisión
- Protección contra replay attacks (combinado con anti-spam)
- Selector interactivo del tipo de cifrado al iniciar el servidor (Simétrico/Asimétrico)
- Adaptación automática del cliente al tipo de cifrado del servidor
- Comando `/shutdown` para cierre ordenado del servidor desde la terminal

#### Archivos Nuevos

- `validacion_integridad.py` - 4f8e08038d4c3e70402d5223fbfade06 - Módulo de validación SHA-256

#### Archivos Modificados

- `Servidor.py` - a6c7db01a8d3cf773e15526f08e8718a - Integración con validación de integridad
- `Clientes.py` - ff90443a55f7e0d6ea10deae6ed0d651 - Integración con validación de integridad

#### Características de Seguridad

- **Validación de Integridad:** SHA-256 hash verification
- **Detección de Modificaciones:** Rechazo automático de mensajes alterados
- **Formato Seguro:** `mensaje_cifrado|||HASH|||hash_sha256`
- **Overhead Mínimo:** ~0.001ms por mensaje
- **Logs de Auditoría:** Registro de intentos de modificación

---

### Versión 4.0 - TLS/SSL, WebSockets y Variables de Entorno

**Fecha:** 03/11/2025
**Estado:** Deprecado

#### Cambios Principales

- Integración de WebSocket seguro (WSS) con soporte TLS/SSL
- Generación automática de certificados autofirmados y uso de rutas desde variables de entorno
- Selector interactivo de tipo de cifrado al iniciar el servidor (Simétrico/Asimétrico)
- Adaptación automática del cliente al tipo de cifrado del servidor
- Implementación completa de variables de entorno (.env) para configuración
- Mejora de estructura del proyecto: módulos reubicados bajo `src/` (config, crypto, security, utils)

#### Archivos Nuevos

- `src/config/config.py` - dfa915afcdee8865808fcd199d447549 - Carga de variables de entorno y validaciones
- `src/security/ssl_manager.py` - 265e7499bfe6bf6e36ba1689e28aee86 - Gestión de certificados y contextos TLS/SSL
- `src/security/validacion_integridad.py` - 3516664df4a2029948b8c3ab5586f492 - Reubicado bajo `src/security`
- `src/crypto/cifrado_simetrico.py` - 3bc112bfff631c04164fd74b0a98a09f - Reubicado bajo `src/crypto`
- `src/crypto/cifrado_asimetrico.py` - 96868eb9ce204b5c9b05922c3503ed27 - Reubicado bajo `src/crypto`
- `src/utils/utils.py` - b0dbc19f7b5292beec4d84b645c46393 - Reubicado bajo `src/utils`

#### Archivos Modificados

- `Servidor.py` - 21ec11a4c1c5355f5f1c91a99d1f7530 - Menú de selección de cifrado, anuncio de modo al cliente, lectura de comandos (`/shutdown`), WSS
- `Clientes.py` - 6ca09d5c5c6e9e770c6d7bb1d7300acf - Adaptación automática al modo de cifrado del servidor
- `env.example` - d97f20f661f233c1157b81cb2b1c97e4 - Variables `SSL_*`, `CLAVE_SECRETA`, `SALT`, `PBKDF2_ITERATIONS`, `RSA_*`

#### Características

- **Transporte:** WebSockets seguros (WSS)
- **TLS/SSL:** Certificados autofirmados gestionados por el servidor
- **Configuración:** Variables de entorno centralizadas (.env)
- **Cifrado:** Selección Simétrico (Fernet) o Asimétrico (RSA) al iniciar el servidor

---

### Versión 5.0 - Servidor Unificado, Autenticación JWT, Firma Digital de PDFs

**Fecha:** 19/11/2025
**Estado:** Producción

#### Cambios Principales

- Servidor unificado FastAPI que combina REST API y WebSocket
- Sistema completo de autenticación con JWT (24 horas de expiración)
- Base de datos MySQL con SQLAlchemy ORM
- Login con credenciales (email/contraseña con BCrypt)
- Login con Google OAuth 2.0
- Sistema de apodos para usuarios
- Generación de PDFs de prueba con espacio para firma
- Firma digital de PDFs con canvas (dibujado con mouse)
- Subida automática de PDFs firmados a Google Drive
- Frontend React + TypeScript + Bootstrap
- Chat en tiempo real por WebSocket con autenticación JWT
- Soporte dual: CLI y navegador web

#### Archivos Nuevos

- `unified_server.py` - b171213a838836662aa3691b39d10ff1 - Servidor unificado FastAPI (REST + WebSocket)
- `init_database.py` - 02048607f29809067b9c5bb5d2ae1a1a - Script de inicialización de MySQL
- `src/database/models.py` - addc3e702db6e9442736b5eb8d6a464d - Modelos SQLAlchemy (Usuario)
- `src/database/connection.py` - b67756df76a410d9a20659dda677c80b - Conexión a MySQL
- `src/auth/auth_service.py` - eb951c2d9004e90cd33e2e65502432c0 - Servicio de autenticación
- `src/auth/password_manager.py` - 9ff5985cd58b336a85ded32d16f90769 - Gestión de contraseñas con BCrypt
- `src/auth/jwt_manager.py` - cddf5f6fa267a0076caedb0fd74122ca - Gestión de tokens JWT

#### Archivos Modificados

- `start.py` - 9bba325f03b6ced2b74fd656eee9945a - Actualizado para servidor unificado
- `requirements.txt` - 349f3de8156bb10436b4c28157c6e46d - Añadidas dependencias MySQL, BCrypt, JWT, SQLAlchemy
- `src/config/config.py` - 2a73643f2292f45bc319b6f16ef8e244 - Añadida configuración de base de datos

#### Características

- **Base de Datos:** MySQL con SQLAlchemy ORM
- **Autenticación:** JWT (HS256, 24 horas), BCrypt (12 rounds)
- **Endpoints REST:**
  - POST /api/auth/register - Registro de usuarios
  - POST /api/auth/login - Login con credenciales
  - POST /api/auth/google - Login con Google OAuth
  - POST /api/auth/set-nickname - Establecer apodo
  - GET /api/auth/me - Información del usuario actual
  - POST /api/pdf/generate - Generar PDF de prueba
  - POST /api/pdf/sign - Firmar PDF y subir a Drive
  - WS /ws/chat - WebSocket para chat en tiempo real
- **Frontend:** React 19 + TypeScript + Vite + Bootstrap 5
- **Chat:** WebSocket autenticado con JWT, historial, usuarios conectados
- **Firma PDF:** Canvas para firma con mouse, generación de PDF, inserción de firma, subida a Drive
- **Seguridad:** Tokens JWT, contraseñas hasheadas, validación de entrada, CORS configurado

## Requisitos del Sistema

### Requisitos de Software

- **Python:** 3.8 o superior
- **Sistema Operativo:** Windows, Linux, macOS
- **Red:** Conexión TCP/IP

### Dependencias

- `cryptography>=41.0.0` - Librería de criptografía
- `websockets>=15.0.0` - Comunicación WebSocket segura
- `fastapi>=0.110.0` - Framework web moderno
- `uvicorn[standard]>=0.27.0` - Servidor ASGI
- `SQLAlchemy>=2.0.0` - ORM para base de datos
- `PyMySQL>=1.1.0` - Driver de MySQL
- `bcrypt>=4.1.0` - Hash de contraseñas
- `python-jose[cryptography]>=3.3.0` - JWT
- `passlib[bcrypt]>=1.7.4` - Framework de hashing
- `PyPDF2>=3.0.0` - Manipulación de PDFs
- `reportlab>=4.0.0` - Generación de PDFs
- `google-api-python-client>=2.115.0` - Google APIs

---

## Instalación

### 1. Instalar Python

#### Windows

```bash

# Descargar desde https://www.python.org/downloads/
# Durante la instalacion, marcar "Add Python to PATH"

# Verificar instalacion
python --version
pip --version
```

#### Linux/macOS

```bash

# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# macOS (con Homebrew)
brew install python3

# Verificar instalacion
python3 --version
pip3 --version
```

### 2. Instalar Dependencias

```bash
# Metodo recomendado
pip install -r requirements.txt
```

---

## Configuración

### Base de Datos MySQL

Configurar en `.env`:

```bash
DB_HOST=localhost
DB_PORT=3306
DB_NAME=chatsec
DB_USER=root
DB_PASSWORD=tu_password
```

Inicializar base de datos:

```bash
python start.py --init-db
```

### Cifrado Simétrico (Fernet)

Configurar en `.env`:

```bash
CLAVE_SECRETA=mi_clave_super_secreta_2025_chat_grupal_v4
SALT=salt_estatico_seguro_2025_v4
PBKDF2_ITERATIONS=100000
```

### Cifrado Asimétrico (RSA)

Generar claves nuevas (opcional):

```bash
python -m src.crypto.cifrado_asimetrico
# Seleccionar opcion 1 y copiar las PEM resultantes
```

Configurar en `.env` usando PEM embebidas o rutas a archivos:

```bash
# Opción A: Pegar PEM completas entre comillas
CLAVE_PRIVADA_PEM=""  
CLAVE_PUBLICA_PEM=""

# Opción B: Usar rutas a archivos (por defecto en keys/)
RSA_PRIVATE_KEY_PATH=keys/rsa_private.pem
RSA_PUBLIC_KEY_PATH=keys/rsa_public.pem
```

### Seleccionar Tipo de Cifrado

Al iniciar `Servidor.py` se mostrará un menú interactivo para seleccionar el tipo de cifrado:

1. Cifrado Simétrico (Fernet/AES-128)
2. Cifrado Asimétrico (RSA-2048)

El cliente (`Clientes.py`) detecta automáticamente el tipo de cifrado del servidor y se adapta sin requerir selección manual.

### Validación de Integridad

La validación SHA-256 está activa por defecto en ambos modos de cifrado.
No requiere configuración adicional.

---

## Uso

### Inicio Completo del Sistema

```bash
cd chat-backend

# Inicializar base de datos (primera vez)
python start.py --init-db

# Autenticar con Google (primera vez)
python start.py --auth

# Iniciar servidor
python start.py
```

Salida esperada:

```bash
SERVIDOR INICIADO

Servidor HTTP/REST API:
   http://localhost:5000
   Documentacion: http://localhost:5000/docs

WebSocket para Chat:
   ws://localhost:5000/ws/chat

Frontend React:
   http://localhost:3000 o http://localhost:5173
```

### Iniciar Frontend

En otra terminal:

```bash
cd chat-frontend
npm install
npm run dev
```

Acceder a: `http://localhost:5173`

### Cliente CLI (Terminal)

Para usar el chat desde terminal sin interfaz web:

```bash
python Clientes.py
```

El cliente CLI solo permite:

- Login con credenciales (email/contraseña)
- Chat en tiempo real
- No tiene acceso a firma de PDF

---

## Licencia

Proyecto personal - Todos los derechos reservados

## Autores

Administrador: @AlexReyes03

## Contacto

Para soporte o consultas, contactar al administrador del proyecto.

---

## Notas Adicionales

### Cumplimiento

Este sistema implementa estándares criptográficos modernos:

- NIST SP 800-132 (PBKDF2)
- RFC 3447 (RSA PKCS #1)
- RFC 8017 (PKCS #1 v2.2)
- FIPS 180-4 (SHA-256)

### Compatibilidad

- Compatible con cifrado simétrico y asimétrico
- Compatible con caracteres especiales (UTF-8)

---

**Última actualización:** 19 Noviembre 2025
**Versión del documento:** 5.0
