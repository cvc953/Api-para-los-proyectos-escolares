# Despliegue en Vercel

## Archivos creados/configurados

1. **vercel.json** - Configuración de Vercel
2. **api/index.py** - Entry point para las serverless functions
3. **.vercelignore** - Archivos a ignorar en el despliegue
4. **app/database.py** - Actualizado para soportar PostgreSQL
5. **app/main.py** - Actualizado para usar lifespan en lugar de eventos deprecated

## Requisitos previos

### 1. Base de datos externa (OBLIGATORIO)

Vercel tiene un filesystem efímero, **no puedes usar SQLite**. Necesitás una base de datos externa:

**Opción gratuita recomendada: Neon (PostgreSQL)**
1. Ve a https://neon.tech
2. Crea una cuenta gratuita
3. Crea un nuevo proyecto
4. Copia la conexión string (similar a `postgresql://user:password@ep-xxx.us-east-1.aws.neon.tech/dbname`)

**Otras opciones:**
- Supabase (PostgreSQL)
- Railway (PostgreSQL)
- Render (PostgreSQL)

### 2. Cuenta en Vercel

1. Ve a https://vercel.com
2. Registrate con GitHub
3. Instala la CLI: `npm install -g vercel`

## Variables de entorno requeridas

En el dashboard de Vercel, configurá estas variables:

| Variable | Valor |
|----------|-------|
| `DATABASE_URL` | Tu connection string de PostgreSQL (ej: `postgresql://...`) |
| `SECRET_KEY` | Una clave secreta larga para JWT (generala con `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `UPLOAD_DIR` | (Opcional) Si usás un servicio de almacenamiento externo |

## Despliegue

### Opción A: CLI de Vercel

```bash
# Login
vercel login

# Desplegar (desde la raíz del proyecto)
vercel

# Para producción
vercel --prod
```

### Opción B: GitHub

1. Hacé commit de los cambios:
   ```bash
   git add .
   git commit -m "Add Vercel configuration"
   ```

2. Subí a GitHub:
   ```bash
   git push origin main
   ```

3. En Vercel:
   - New Project → Import from GitHub
   - Seleccioná tu repositorio
   - En Environment Variables, agregá `DATABASE_URL` y `SECRET_KEY`
   - Deploy

## Notas importantes

### Uploads de archivos

Si tu API permite subir archivos, necesitás integrar con un servicio externo:
- **Cloudinary** (gratis hasta cierto límite)
- **AWS S3**
- **UploadCare**

No podés guardar archivos en el filesystem de Vercel.

### cold starts

Las serverless functions de Vercel pueden tener "cold starts" (inicio lento en la primera petición). Usá el plan Pro si necesitas mejor rendimiento.

### Límites gratuitos

- 100GB de bandwidth/mes
- 100 horas de serverless functions/mes
- Para uso intensivo, considerá upgrading a Pro ($20/mes)

## Verificación

Después del despliegue, verificá que funciona:
```bash
curl https://tu-proyecto.vercel.app/
```

Debería devolver:
```json
{"mensaje": "API de Gestión de Proyectos Escolares", "version": "1.0.0", ...}
```
