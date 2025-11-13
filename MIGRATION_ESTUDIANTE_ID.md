# Migration: Add estudiante_id to ProyectoVersion

## Problem
The application was throwing `AttributeError: 'ProyectoVersion' object has no attribute 'estudiante_id'` because the database table doesn't have the `estudiante_id` column yet, even though the code expects it.

## What Changed
The multi-student versioning system was implemented, which requires tracking which student uploaded each version. This required:

1. Adding `estudiante_id` field to the `ProyectoVersion` model
2. Updating endpoints to filter and group versions by student
3. Implementing per-student version numbering

## Temporary Fix Applied
The code now uses `getattr(v, 'estudiante_id', None)` to safely access the field, allowing the app to work with both:
- **Old records** (without estudiante_id) - treated as if estudiante_id = None
- **New records** (with estudiante_id) - full multi-student functionality

## Migration Required
To fully enable the multi-student versioning system, you must add the `estudiante_id` column to the database.

### Option 1: Using Python Migration Script (Recommended)

Run this command from your project directory:

```bash
sudo docker compose exec api python3 /app/migrate_estudiante_id.py
```

Or use the bash script:

```bash
sudo docker compose exec api bash /app/scripts/run_migration.sh
```

### Option 2: Using Raw SQL

Connect to your MySQL database and run the SQL in `migration_add_estudiante_id.sql`:

```bash
# Copy SQL to container
sudo docker compose cp migration_add_estudiante_id.sql db:/tmp/migration.sql

# Execute it
sudo docker compose exec db mysql -uroot -prootpassword proyectos_db < /tmp/migration.sql
```

Or directly:

```bash
sudo docker compose exec db mysql -uroot -prootpassword proyectos_db -e "
ALTER TABLE proyectoversion ADD COLUMN estudiante_id INT NULL;
ALTER TABLE proyectoversion ADD CONSTRAINT fk_proyectoversion_estudiante 
    FOREIGN KEY (estudiante_id) REFERENCES estudiante(id) ON DELETE SET NULL;
CREATE INDEX idx_proyectoversion_estudiante_id ON proyectoversion(estudiante_id);
"
```

## After Migration

Once the migration is complete:

1. **New uploads** will automatically include the `estudiante_id` of the uploader
2. **Students** will see only their own versions when viewing a project
3. **Professors** will see all versions grouped by student
4. **Each student** will have independent version numbering (v1, v2, v3...)

## Old Records

Existing `proyectoversion` records will have `estudiante_id = NULL`. These will:
- Not appear for students (filtered out)
- Appear grouped under "Unknown Student" for professors
- Not interfere with new uploads

### Optional: Link Old Records to Students

If you want to assign old versions to students, you can run:

```sql
-- Link versions to the student assigned to their project
UPDATE proyectoversion pv
JOIN proyecto p ON pv.proyecto_id = p.id
SET pv.estudiante_id = p.estudiante_id
WHERE pv.estudiante_id IS NULL AND p.estudiante_id IS NOT NULL;
```

Note: This only works if projects were previously assigned to individual students. For course-wide projects, you may not be able to determine which student uploaded each old version.

## Verification

After running the migration, check that it worked:

```bash
sudo docker compose exec db mysql -uroot -prootpassword proyectos_db -e "DESCRIBE proyectoversion;"
```

You should see `estudiante_id` in the column list.

Then test the API:
1. Log in as a student
2. Upload a new version to a project
3. Check GET /proyectos/{id}/versiones - you should see your version with your student info
4. Log in as a professor and check the same endpoint - you should see versions grouped by student

## Rollback (If Needed)

If you need to revert the migration:

```bash
sudo docker compose exec db mysql -uroot -prootpassword proyectos_db -e "
ALTER TABLE proyectoversion DROP FOREIGN KEY fk_proyectoversion_estudiante;
ALTER TABLE proyectoversion DROP INDEX idx_proyectoversion_estudiante_id;
ALTER TABLE proyectoversion DROP COLUMN estudiante_id;
"
```

Then revert the code changes to remove references to `estudiante_id`.
