# README - ENDPOINTS

## Autenticación

### Registro
```
POST /auth/registro
```
**Parámetros Query:**
- `email` (string, requerido)
- `password` (string, requerido)
- `nombre` (string, requerido)
- `apellido` (string, requerido)
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
**Parámetros Query:**
- `email` (string, requerido)
- `password` (string, requerido)

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
**Body (JSON):**
```json
{
  "titulo": "App Mobile",
  "descripcion": "Aplicación de reservas",
  "estudiante_id": 1,
  "profesor_id": 2,
  "fecha_entrega": "2025-12-15T23:59:59",
  "nombre_archivo": "app-v1.zip",
  "comentarios_version": "Primera entrega"
}
```

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
**Parámetros Query:**
- `descripcion` (string, requerido): Cambios realizados

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
