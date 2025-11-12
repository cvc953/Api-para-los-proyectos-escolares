# API Gestión Proyectos Escolares

## Descripción General

Esta es una **API REST moderna** construida con **FastAPI** para la gestión integral de proyectos escolares. Permite que estudiantes suban proyectos, profesores califiquen y proporcionen retroalimentación, y padres monitoren el progreso académico.

### Características Principales

✅ **Subida de Proyectos** - Estudiantes pueden subir y actualizar proyectos  
✅ **Historial de Versiones** - Mantiene control de todas las versiones de cada proyecto  
✅ **Calificaciones** - Profesores califican proyectos (escala 0-5)  
✅ **Reportes de Desempeño** - Estadísticas académicas por estudiante  
✅ **Autenticación JWT** - Seguridad con tokens JWT  
✅ **Roles de Usuario** - Estudiante, Profesor, Padre  
✅ **Base de Datos SQLite** - Persistencia local o en servidor

---

## Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| Framework Web | **FastAPI 0.95.2** |
| Servidor | **Uvicorn 0.22.0** |
| ORM/BD | **SQLModel 0.0.8** + **SQLite** |
| Autenticación | **PyJWT 3.3.0** + **Passlib** |
| Validación | **Pydantic** |

---

## Estructura del Proyecto

```
api_python/
├── app/
│   ├── __init__.py
│   ├── main.py              # Punto de entrada, rutas y endpoints
│   ├── database.py          # Configuración SQLite
│   ├── auth.py              # JWT y hash de contraseñas
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py        # Modelos SQLModel (Estudiante, Proyecto, etc.)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic DTOs para requests/responses
│   └── crud/
│       ├── __init__.py
│       └── crud.py          # Operaciones CRUD
├── requirements.txt         # Dependencias Python
├── README.md               # Este archivo
├── README-INSTALACION.md   # Guía de instalación y setup
├── README-ENDPOINTS.md     # Documentación de todos los endpoints
├── README-EJEMPLOS.md      # Ejemplos curl y casos de uso
└── plataforma_proyectos.db # Base de datos SQLite (se crea automáticamente)

## Notas importantes

- Almacenamiento de archivos: los proyectos se guardan en disco en el directorio configurado por `UPLOAD_DIR` (o `./uploads` por defecto). Si ejecutas con Docker, monta `./uploads` como volumen y asegúrate de que el contenedor tenga permisos de escritura.

- Hashing de contraseñas: para evitar dependencias nativas en imágenes "slim", el proyecto usa `pbkdf2_sha256` como esquema de hash por defecto en entornos Docker. Si necesitas usar `bcrypt`, instala la dependencia y reconstruye la imagen.
```

---

## Ruta Rápida

### 1. Instalar Dependencias
```bash
cd api_python
pip install -r requirements.txt
```

### 2. Ejecutar API
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Acceder a Documentación Interactiva
- **Swagger UI**: http://172.200.176.171:8000/docs
- **ReDoc**: http://172.200.176.171:8000/redoc

---

## Documentación Completa

Este proyecto incluye **4 documentos README** temáticos:

1. **README.md** (este archivo)  
   → Visión general, stack, estructura del proyecto

2. **README-INSTALACION.md**  
   → Requisitos del sistema, instalación paso a paso, configuración

3. **README-ENDPOINTS.md**  
   → Documentación detallada de cada endpoint, parámetros, respuestas

4. **README-EJEMPLOS.md**  
   → Ejemplos prácticos con curl, Postman, casos de uso reales

---

## Contacto y Soporte

- **Documentación Interactiva**: http://172.200.176.171:8000/docs
- **Archivo de Configuración**: `appsettings.json`
- **Base de Datos**: `plataforma_proyectos.db`

---

**Última actualización**: 11 de noviembre de 2025
