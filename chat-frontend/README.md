# Frontend - Sistema de Chat con Firma Digital

## Descripción

Frontend en desarrollo para el sistema de chat con firma digital. Desarrollado con React 19, TypeScript y Vite.

**Estado:** En Desarrollo

---

## Tecnologías

- **React:** 19.2.0
- **TypeScript:** 5.9.3
- **Build Tool:** Vite 7.2.2
- **Estilos:** Bootstrap 5 + Bootstrap Icons
- **Linting:** ESLint 9.39.1

---

## Instalación

### Requisitos Previos

- Node.js 18 o superior
- npm o yarn

### Instalar Dependencias

```bash
npm install
```

---

## Scripts Disponibles

### Desarrollo

```bash
npm run dev
```

Inicia servidor de desarrollo en http://localhost:5173

### Build

```bash
npm run build
```

Genera build de producción en `dist/`

### Preview

```bash
npm run preview
```

Previsualiza el build de producción

### Lint

```bash
npm run lint
```

Ejecuta ESLint para verificar código

---

## Estructura

```
chat-frontend/
├── src/
│   ├── main.tsx          # Punto de entrada
│   ├── App.tsx           # Componente principal
│   ├── App.css           # Estilos del componente
│   ├── index.css         # Estilos globales
│   └── assets/           # Recursos estáticos
├── public/               # Archivos públicos
├── index.html            # HTML base
├── package.json          # Dependencias
├── tsconfig.json         # Configuración TypeScript
├── vite.config.ts        # Configuración Vite
└── eslint.config.js      # Configuración ESLint
```

---

## Conexión con Backend

El frontend se conectará a los siguientes endpoints del backend:

### REST API
```
Base URL: http://localhost:5000
Documentación: http://localhost:5000/docs
```

### WebSocket (Chat)
```
URL: wss://localhost:5555
```

---

## Configuración

### Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
VITE_API_URL=http://localhost:5000
VITE_WS_URL=wss://localhost:5555
```

### CORS

El backend ya está configurado para aceptar peticiones desde:
- http://localhost:3000
- http://localhost:5173

---

## Bootstrap

### Importar Bootstrap

Bootstrap ya está instalado. Para usarlo, importar en `main.tsx` o `App.tsx`:

```typescript
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
```

### Ejemplos de Uso

```tsx
// Botón con ícono
<button className="btn btn-primary">
  <i className="bi bi-file-earmark-pdf"></i> Subir PDF
</button>

// Card
<div className="card">
  <div className="card-header">
    <i className="bi bi-shield-check"></i> Documento Firmado
  </div>
  <div className="card-body">
    Contenido
  </div>
</div>
```

---

## Desarrollo Futuro

### Componentes a Implementar

- Componente de autenticación Google
- Componente de subida de archivos
- Componente de firma digital
- Componente de lista de documentos
- Componente de chat en tiempo real
- Componente de verificación de firmas

### APIs a Integrar

- /api/auth/ - Autenticación
- /api/sign/ - Firma digital
- /api/drive/ - Google Drive
- /api/gmail/ - Gmail
- WebSocket - Chat en tiempo real

---

## Notas de Desarrollo

- Usar hooks de React (useState, useEffect, useContext)
- Implementar manejo de errores
- Validar formularios antes de enviar
- Mostrar loaders durante operaciones
- Implementar notificaciones (toast/alert)
- Responsive design (Bootstrap Grid)

---

## Licencia

Proyecto personal - Todos los derechos reservados

---

**Última actualización:** 19 Noviembre 2025
**Versión:** 0.1.0 (En Desarrollo)
