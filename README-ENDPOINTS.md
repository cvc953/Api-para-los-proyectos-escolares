# README - ENDPOINTS

## Autenticación

### Registro
```
POST /auth/registro
```
**Entrada:**
- Preferible: enviar como form-data (multipart/form-data) usando `-F` en curl.
- Alternativa: la API ofrece un *fallback* y aceptará también parámetros por query (ej. `?email=...&password=...`) pero el método recomendado es form-data.

Campos (obligatorios):
- `email` (string)
- `password` (string)
- `nombre` (string)
- `apellido` (string)
- `rol` (string, opcional): `estudiante` | `profesor` (default: `estudiante`)

**Respuesta (200):**
```json
{
  "id": 1,
  "email": "juan@ejemplo.com",
  "rol": "estudiante"
}
```

---

### Login
```
POST /auth/login
```
**Entrada:** enviar `email` y `password` como form-data (`-F`) — la ruta actual está preparada para recibir form-data.

**Respuesta (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "usuario_id": 1
}
```

**Usar Token:**
Incluir en header `Authorization: Bearer {token}` en requests posteriores.

---

## Proyectos

### Crear Proyecto
```
POST /proyectos
```
**Entrada:**
- Preferible: enviar multipart/form-data (curl `-F`) con los campos del proyecto y un archivo opcional en el campo `file`.

Campos:
- `titulo` (string, requerido)
- `descripcion` (string, requerido)
- `estudiante_id` (int, requerido)
- `profesor_id` (int, requerido)
- `fecha_entrega` (ISO datetime string, opcional) e.g. `2025-12-15T23:59:59`
- `comentarios_version` (string, opcional)
- `file` (file, opcional): archivo del proyecto que se guardará y asociará a la primera versión

**Respuesta (201):**
```json
{
  "id": 5,
  "titulo": "App Mobile",
  "version_actual": 1,
  "total_versiones": 1
}
```

---

### Obtener Proyecto
```
GET /proyectos/{proyecto_id}
```

### Descargar archivo del proyecto (versión actual)
```
GET /proyectos/{proyecto_id}/archivo
```
- Descarga el archivo asociado a la versión actual del proyecto (si existe).
- Respuesta: binary file (Content-Disposition con filename).
 - Descarga el archivo asociado a la versión actual del proyecto (si existe).
 - El archivo se servirá con su nombre y formato original (extensión) y con el Content-Type detectado por extensión; curl con `-O -J` guardará el archivo con su nombre y extensión originales.

**Nota sobre almacenamiento de archivos**: La API utiliza una ruta de filesystem para almacenar archivos. Si `UPLOAD_DIR` no está disponible o no es escribible, las rutas de subida devolverán HTTP 503. Revisa `README-INSTALACION.md` para pasos rápidos sobre montaje de volumen y permisos.

### Descargar archivo de una versión específica
```
GET /proyectos/{proyecto_id}/versiones/{version_id}/archivo
```
- Descarga el archivo asociado a la versión indicada.

---

### Listar Proyectos por Estudiante
```
GET /proyectos/estudiante/{estudiante_id}
```

---

### Listar Proyectos por Profesor
```
GET /proyectos/profesor/{profesor_id}
```

---

## Versiones

### Subir Nueva Versión
```
POST /proyectos/{proyecto_id}/versiones
```
**Entrada (multipart/form-data):**
- Preferible: enviar `descripcion` como campo form-data y un archivo opcional en el campo `file`.
- Ejemplo curl: `-F 'descripcion=Corrección de errores' -F 'file=@/ruta/a/archivo.zip'`

La API aceptará también `descripcion` por query en modo fallback, pero el método recomendado para subir archivos es multipart/form-data.

**Respuesta (200):**
```json
{
  "id": 8,
  "numero_version": 2,
  "fecha": "2025-11-11T10:30:00"
}
```

---

### Obtener Historial de Versiones
```
GET /proyectos/{proyecto_id}/versiones
```

**Respuesta (200):**
```json
[
  {
    "id": 8,
    "numero_version": 2,
    "descripcion": "Correcciones de bugs",
    "fecha_subida": "2025-11-11T10:30:00",
    "es_version_actual": true
  },
  {
    "id": 7,
    "numero_version": 1,
    "descripcion": "Primera entrega",
    "fecha_subida": "2025-11-10T14:15:00",
    "es_version_actual": false
  }
]
```

---

## Calificaciones

### Calificar Proyecto
```
POST /calificaciones
```
**Body (JSON):**
```json
{
  "proyecto_id": 5,
  "profesor_id": 2,
  "puntaje": 4.5,
  "comentarios": "Excelente implementación. Mejorar documentación."
}
```

**Validación:** Puntaje debe estar entre 0.0 y 5.0

---

### Obtener Calificaciones de Proyecto
```
GET /calificaciones/proyecto/{proyecto_id}
```

---

### Obtener Calificaciones de Estudiante
```
GET /calificaciones/estudiante/{estudiante_id}
```

---

## Reportes

### Reporte de Desempeño
```
GET /reportes/desempeño/estudiante/{estudiante_id}
```

**Respuesta (200):**
```json
{
  "estudiante_id": 1,
  "nombre_estudiante": "Estudiante",
  "promedio_calificaciones": 4.1,
  "total_proyectos": 5,
  "proyectos_aprobados": 5,
  "tasa_aprobacion": 100.0,
  "calificacion_mas_alta": 4.8,
  "calificacion_mas_baja": 3.5,
  "total_versiones": 12,
  "detalle_proyectos": [...]
}
```

---

**Última actualización**: 11 de noviembre de 2025
