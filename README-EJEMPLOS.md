# README - EJEMPLOS

## 1. Registrar Usuario


### Estudiante (recomendado: form-data)
```bash
curl -X POST "http://localhost:8000/auth/registro" \
  -F 'email=juan@ejemplo.com' \
  -F 'password=123456' \
  -F 'nombre=Juan' \
  -F 'apellido=García' \
  -F 'rol=estudiante'
```

### Profesor (recomendado: form-data)
```bash
curl -X POST "http://localhost:8000/auth/registro" \
  -F 'email=profesor@ejemplo.com' \
  -F 'password=123456' \
  -F 'nombre=Dr.' \
  -F 'apellido=Fernández' \
  -F 'rol=profesor'
```

---

## 2. Login y Obtener Token

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -F 'email=juan@ejemplo.com' \
  -F 'password=123456'
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

## Ejecutar el script de pruebas

Hay un pequeño script de integración en `api_python/scripts/test_endpoints.sh` que ejecuta el flujo feliz (registra un estudiante y un profesor, crea un proyecto, sube versión, califica y obtiene el reporte). Requiere `jq`.

Ejecutar:
```bash
cd /home/christian/Proyecto-Plataformaproyectosescolares/api_python
chmod +x scripts/test_endpoints.sh
./scripts/test_endpoints.sh http://127.0.0.1:8000
```

---

## 3. Crear Proyecto

Crear proyecto con archivo (multipart/form-data):

```bash
curl -X POST "http://localhost:8000/proyectos" \
  -F 'titulo=Sistema de Biblioteca' \
  -F 'descripcion=Aplicación web para gestión de biblioteca' \
  -F 'estudiante_id=1' \
  -F 'profesor_id=2' \
  -F 'fecha_entrega=2025-12-20T23:59:59' \
  -F 'comentarios_version=Entrega inicial con modelos' \
  -F 'file=@/ruta/a/biblioteca-v1.zip'
```

---

## 4. Subir Nueva Versión

Subir nueva versión (multipart/form-data con archivo opcional):

```bash
curl -X POST "http://localhost:8000/proyectos/1/versiones" \
  -F 'descripcion=Agregada funcionalidad de búsqueda' \
  -F 'file=@/ruta/a/entrega_v2.zip'
```

Si estás ejecutando la API en Docker y ves errores de permisos al subir (Permission denied), crea y asigna permisos a la carpeta `uploads` en el host antes de arrancar los contenedores:

```bash
cd /home/christian/Proyecto-Plataformaproyectosescolares/api_python
mkdir -p uploads
sudo chown -R 1000:1000 uploads    # o usar chmod 0777 para desarrollo rápido
sudo docker compose up -d --build
```

## 11. Descargar archivo del proyecto (versión actual)

```bash
curl -O -J "http://localhost:8000/proyectos/1/archivo"
```

`-O -J` hace que curl guarde el archivo usando el filename provisto por el servidor.

Nota: el archivo se descargará con la misma extensión/formato con el que fue subido; el servidor intentará inferir el Content-Type a partir de la extensión.

## 12. Descargar archivo de una versión específica

```bash
curl -O -J "http://localhost:8000/proyectos/1/versiones/3/archivo"
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
