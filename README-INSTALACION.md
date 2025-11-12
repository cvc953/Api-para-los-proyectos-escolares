# README - INSTALACIÓN Y CONFIGURACIÓN

## Requisitos Previos

Antes de instalar la API, asegúrate de tener:

- **Python 3.9+** (recomendado 3.10+)
- **pip** (gestor de paquetes Python)
- **git** (opcional, para clonar el repo)

### Verificar Versión de Python

```bash
python --version
# o
python3 --version
```

Si no tienes Python instalado, descárgalo desde https://www.python.org/downloads/

---

## Pasos de Instalación

### 1. Clonar o Navegar al Directorio

```bash
# Opción A: Si es tu primer acceso
cd /home/christian/Proyecto-Plataformaproyectosescolares/api_python

# Opción B: O desde la carpeta del proyecto
cd Proyecto-Plataformaproyectosescolares/api_python
```

### 2. Crear un Entorno Virtual (Recomendado)

```bash
# En Windows
python -m venv venv
venv\Scripts\activate

# En macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Dependencias principales:**
- `fastapi==0.95.2` - Framework web asincrónico
- `uvicorn[standard]==0.22.0` - Servidor ASGI
- `sqlmodel==0.0.8` - ORM combinado SQLAlchemy + Pydantic
- `python-jose==3.3.0` - JWT para autenticación
- `passlib` - Hash seguro de contraseñas (el proyecto usa `pbkdf2_sha256` como esquema por defecto en contenedores slim)
- `python-multipart==0.0.5` - Soporte para multipart/form-data

### 4. Verificar la Instalación

```bash
python -c "import fastapi; print(fastapi.__version__)"
```

Debería mostrar: `0.95.2`

---

## Configuración

### Archivo de Configuración (database.py)

El archivo `app/database.py` contiene la configuración de la base de datos:

```python
DATABASE_URL = "sqlite:///./plataforma_proyectos.db"
```

**Opciones:**
- **SQLite local** (predeterminado): `sqlite:///./plataforma_proyectos.db`
- **SQLite con ruta absoluta**: `sqlite:////tmp/plataforma_proyectos.db`
- **MySQL** (producción): `mysql+pymysql://user:pass@localhost/dbname`

### Variables de Entorno (Opcional)

Puedes crear un archivo `.env` para configurar variables:

```bash
# .env
DATABASE_URL=sqlite:///./plataforma_proyectos.db
SECRET_KEY=tu_clave_secreta_aqui_cambia_esto
DEBUG=True
```

**Importante en Producción**: 
- Cambiar `SECRET_KEY` a un valor seguro
- Establecer `DEBUG=False`
- Usar variables de entorno para credenciales

---

## Ejecutar la API

### Opción 1: Modo Desarrollo (con Reload)

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- `--reload`: Reinicia automáticamente cuando hay cambios en el código
- `--host 0.0.0.0`: Accessible desde cualquier IP (no solo localhost)
- `--port 8000`: Puerto en el que corre la API

### Opción 2: Modo Producción

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

- `--workers 4`: Usa 4 procesos para mayor concurrencia
- Sin `--reload` para mejor rendimiento

### Opción 3: Ejecutar directamente con Python

```bash
python app/main.py
```

---

## Verificación Inicial

Una vez ejecutada la API, deberías ver algo como:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Prueba Rápida

Abre en tu navegador:

```
http://localhost:8000
```

Debería devolver:

```json
{
  "mensaje": "API de Gestión de Proyectos Escolares",
  "version": "1.0.0",
  "documentacion": "/docs",
  "endpoints": {...}
}
```

---

## Acceso a Documentación Interactiva

La API genera documentación automáticamente:

### Swagger UI (Recomendado)
```
http://localhost:8000/docs
```
- Interfaz interactiva para probar endpoints
- Descarga de especificación OpenAPI

### ReDoc (Alternativa)
```
http://localhost:8000/redoc
```

## Docker / docker-compose (opción recomendada para desarrollo)

Si prefieres ejecutar la API junto con una base de datos MySQL en contenedores, existe un `docker-compose.yml` en este directorio que levanta ambos servicios (`api` y `db`).

Pasos rápidos:

```bash
cd /home/christian/Proyecto-Plataformaproyectosescolares/api_python
# Build y levantar (primera vez o después de cambios en el código)
sudo docker compose build --no-cache api
sudo docker compose up -d

# Ver logs del API
sudo docker compose logs --no-color --tail 200 api
```

Nota: Si cambias el código en el workspace debes reconstruir la imagen del servicio `api` para que los cambios se reflejen (ver pasos anteriores).
- Documentación legible en formato de referencia

## Gestión de archivos subidos (UPLOAD_DIR) y permisos

La aplicación guarda los archivos subidos (proyectos / versiones) en un directorio configurable a través de la variable de entorno `UPLOAD_DIR`.

- Comportamiento al arrancar:
  - Si se define `UPLOAD_DIR` en el entorno, la app intentará usar ese directorio.
  - Si no existe, la app intentará crear `./uploads` dentro del workspace.
  - Si `./uploads` no es creable (p. ej. filesystem read-only), la app intentará `/tmp/uploads`.
  - Si no hay un directorio disponible o escribible, la funcionalidad de subida quedará deshabilitada y la API devolverá 503 al intentar subir archivos.

Recomendación para desarrollo con Docker Compose: montar un volumen en el host y asignar permisos para que el contenedor pueda escribir archivos.

Ejemplo (en tu host):

```bash
cd /home/christian/Proyecto-Plataformaproyectosescolares/api_python
# crear carpeta uploads en el host
mkdir -p uploads
# (opcional) ajustar propietario al UID/GID del contenedor para evitar Permission denied
# sustituye 1000:1000 por el UID:GID apropiado si conoces el usuario del contenedor
sudo chown -R 1000:1000 uploads
# para desarrollo rápido (menos seguro):
chmod -R 0777 uploads
```

En `docker-compose.yml` puedes añadir algo así al servicio `api` para montar la carpeta:

```yaml
services:
  api:
    volumes:
      - ./uploads:/app/uploads
    environment:
      - UPLOAD_DIR=/app/uploads
```

Nota sobre producción: para entornos reales se recomienda usar un almacenamiento de objetos (S3, MinIO) o un volumen gestionado, y no permisos 0777.

### Compatibilidad MySQL y dependencias nativas
Si usas MySQL 8 con el plugin de autenticación `caching_sha2_password`, `pymysql` puede requerir la librería `cryptography`. En imágenes "slim" esto puede necesitar instalar paquetes de compilación o incluir la rueda. Alternativa rápida: crear el usuario MySQL con `mysql_native_password`.

### Cambio de esquema de hashing de contraseñas
Para evitar problemas con dependencias nativas (bcrypt) en contenedores ligeros, el proyecto usa `pbkdf2_sha256` como esquema de hashing por defecto en entornos Docker. Esto no cambia la seguridad esperada para la mayoría de los casos de uso de la aplicación.

---

## Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'fastapi'"

**Solución:**
```bash
# Verifica que estés en el entorno virtual
which python  # En Linux/Mac
# Debería mostrar ruta del venv

# Reinstala dependencias
pip install -r requirements.txt
```

### Error: "Port 8000 already in use"

**Solución:**
```bash
# Usar otro puerto
python -m uvicorn app.main:app --port 8001

# O matar el proceso en el puerto 8000 (Linux/Mac)
lsof -ti:8000 | xargs kill -9
```

### Error: "Database is locked"

**Solución:**
```bash
# Elimina la BD y deja que se recree
rm plataforma_proyectos.db

# Reinicia la API
python -m uvicorn app.main:app --reload
```

### Contraseña Olvidada

**Nota**: En desarrollo, puedes borrar la BD y comenzar de nuevo. En producción, necesitarás un mecanismo de recuperación.

---

## Próximos Pasos

1. Leer **README-ENDPOINTS.md** para conocer todos los endpoints disponibles
2. Consultar **README-EJEMPLOS.md** para ejemplos prácticos con curl
3. Explorar la API interactivamente en `/docs`

---

**Última actualización**: 11 de noviembre de 2025
