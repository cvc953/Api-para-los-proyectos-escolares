#!/usr/bin/env python3
"""
Script to add estudiante_id and version_id to calificacion table for per-student grading.
Run this with: python migrate_calificacion_per_student.py
"""

import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "mysql+pymysql://appuser:apppassword@db:3306/plataforma_proyectos?charset=utf8mb4")

def run_migration():
    print(f"Connecting to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.begin() as connection:
            print("Running migration for calificacion table...")
            
            # Check if estudiante_id column exists
            result = connection.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'calificacion'
                AND COLUMN_NAME = 'estudiante_id'
            """))
            
            if result.fetchone()[0] > 0:
                print("✓ Column 'estudiante_id' already exists in calificacion.")
            else:
                print("Adding estudiante_id column...")
                connection.execute(text("""
                    ALTER TABLE calificacion ADD COLUMN estudiante_id INT NULL
                """))
                connection.execute(text("""
                    ALTER TABLE calificacion ADD CONSTRAINT fk_calificacion_estudiante 
                    FOREIGN KEY (estudiante_id) REFERENCES estudiante(id) ON DELETE CASCADE
                """))
                print("✓ estudiante_id column added")
            
            # Check if version_id column exists
            result = connection.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'calificacion'
                AND COLUMN_NAME = 'version_id'
            """))
            
            if result.fetchone()[0] > 0:
                print("✓ Column 'version_id' already exists in calificacion.")
            else:
                print("Adding version_id column...")
                connection.execute(text("""
                    ALTER TABLE calificacion ADD COLUMN version_id INT NULL
                """))
                connection.execute(text("""
                    ALTER TABLE calificacion ADD CONSTRAINT fk_calificacion_version 
                    FOREIGN KEY (version_id) REFERENCES proyectoversion(id) ON DELETE CASCADE
                """))
                print("✓ version_id column added")
            
            # Create indexes
            try:
                connection.execute(text("""
                    CREATE INDEX idx_calificacion_estudiante_id ON calificacion(estudiante_id)
                """))
                print("✓ Index on estudiante_id created")
            except:
                print("  (Index on estudiante_id may already exist)")
            
            try:
                connection.execute(text("""
                    CREATE INDEX idx_calificacion_version_id ON calificacion(version_id)
                """))
                print("✓ Index on version_id created")
            except:
                print("  (Index on version_id may already exist)")
            
            print("\n✅ Migration completed successfully!")
            print("\nNow you can grade individual student submissions.")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
