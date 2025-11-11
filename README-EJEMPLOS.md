# README - EJEMPLOS

## 1. Registrar Usuario

### Estudiante
```bash
curl -X POST "http://localhost:8000/auth/registro?email=juan@ejemplo.com&password=123456&nombre=Juan&apellido=García&rol=estudiante"
```

### Profesor
```bash
curl -X POST "http://localhost:8000/auth/registro?email=profesor@ejemplo.com&password=123456&nombre=Dr.&apellido=Fernández&rol=profesor"
```

---

## 2. Login y Obtener Token

```bash
curl -X POST "http://localhost:8000/auth/login?email=juan@ejemplo.com&password=123456"
```

**Salida:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "usuario_id": 1
}
```

**Guardar token para próximos requests:**
```bash
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

## 3. Crear Proyecto

```bash
curl -X POST "http://localhost:8000/proyectos" \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Sistema de Biblioteca",
    "descripcion": "Aplicación web para gestión de biblioteca",
    "estudiante_id": 1,
    "profesor_id": 2,
    "fecha_entrega": "2025-12-20T23:59:59",
    "nombre_archivo": "biblioteca-v1.zip",
    "comentarios_version": "Entrega inicial con modelos"
  }'
```

---

## 4. Subir Nueva Versión

```bash
curl -X POST "http://localhost:8000/proyectos/1/versiones?descripcion=Agregada%20funcionalidad%20de%20búsqueda"
```

---

## 5. Ver Historial de Versiones

```bash
curl -X GET "http://localhost:8000/proyectos/1/versiones"
```

---

## 6. Calificar Proyecto

```bash
curl -X POST "http://localhost:8000/calificaciones" \
  -H "Content-Type: application/json" \
  -d '{
    "proyecto_id": 1,
    "profesor_id": 2,
    "puntaje": 4.7,
    "comentarios": "Excelente código. Interfaz muy intuitiva. Documentación faltante."
  }'
```

---

## 7. Ver Calificaciones de Proyecto

```bash
curl -X GET "http://localhost:8000/calificaciones/proyecto/1"
```

---

## 8. Ver Todas las Calificaciones de un Estudiante

```bash
curl -X GET "http://localhost:8000/calificaciones/estudiante/1"
```

---

## 9. Generar Reporte de Desempeño

```bash
curl -X GET "http://localhost:8000/reportes/desempeño/estudiante/1"
```

**Salida:**
```json
{
  "estudiante_id": 1,
  "nombre_estudiante": "Estudiante",
  "promedio_calificaciones": 4.3,
  "total_proyectos": 3,
  "proyectos_aprobados": 3,
  "tasa_aprobacion": 100.0,
  "calificacion_mas_alta": 4.8,
  "calificacion_mas_baja": 3.9,
  "total_versiones": 7,
  "detalle_proyectos": [
    {
      "proyecto_id": 1,
      "titulo_proyecto": "Sistema de Biblioteca",
      "calificacion": 4.7,
      "estado": "Aprobado",
      "versiones_cargadas": 3
    }
  ]
}
```

---

## 10. Flujo Completo de Usuario

### Paso 1: Registrar estudiante
```bash
curl -X POST "http://localhost:8000/auth/registro?email=maria@ejemplo.com&password=pwd123&nombre=María&apellido=López&rol=estudiante"
```

### Paso 2: Login
```bash
curl -X POST "http://localhost:8000/auth/login?email=maria@ejemplo.com&password=pwd123"
# Guardar token
```

### Paso 3: Crear proyecto
```bash
curl -X POST "http://localhost:8000/proyectos" \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Web App","descripcion":"E-commerce","estudiante_id":1,"profesor_id":2,"nombre_archivo":"web-app.zip"}'
```

### Paso 4: Profesor califica
```bash
curl -X POST "http://localhost:8000/calificaciones" \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id":1,"profesor_id":2,"puntaje":4.2,"comentarios":"Buen trabajo"}'
```

### Paso 5: Ver reporte
```bash
curl -X GET "http://localhost:8000/reportes/desempeño/estudiante/1"
```

---

## Tips

- **URL Encoding**: Para parámetros con espacios, usa `%20` o entrecomilla
- **JSON**: Usa `-H "Content-Type: application/json"` con `-d` para body JSON
- **Variables en Bash**: `TOKEN="..."` y luego `$TOKEN`
- **Pretty Print**: Agregar `| jq` al final (requiere `jq` instalado)

---

**Última actualización**: 11 de noviembre de 2025
