-- Migration to add estudiante_id column to proyectoversion table
-- Run this SQL script on your MySQL database

-- Add the estudiante_id column (nullable to allow existing records)
ALTER TABLE proyectoversion ADD COLUMN estudiante_id INT NULL;

-- Add foreign key constraint
ALTER TABLE proyectoversion ADD CONSTRAINT fk_proyectoversion_estudiante 
    FOREIGN KEY (estudiante_id) REFERENCES estudiante(id) ON DELETE SET NULL;

-- Create index for better query performance
CREATE INDEX idx_proyectoversion_estudiante_id ON proyectoversion(estudiante_id);

-- Optional: Update existing records to link them to a student if needed
-- You can run queries like this to assign existing versions to students:
-- UPDATE proyectoversion pv
-- JOIN proyecto p ON pv.proyecto_id = p.id
-- SET pv.estudiante_id = p.estudiante_id
-- WHERE pv.estudiante_id IS NULL AND p.estudiante_id IS NOT NULL;
