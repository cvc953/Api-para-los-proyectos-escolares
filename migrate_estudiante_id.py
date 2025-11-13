#!/usr/bin/env python3
"""
Script to add estudiante_id column to proyectoversion table.
Run this with: python migrate_estudiante_id.py
"""

import os
from sqlalchemy import create_engine, text

# Get database URL from environment or use default
DATABASE_URL = os.environ.get("DATABASE_URL", "mysql+pymysql://root:rootpassword@db:3306/proyectos_db")

def run_migration():
    print(f"Connecting to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.begin() as connection:
            print("Running migration...")
            
            # Check if column already exists
            result = connection.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'proyectoversion'
                AND COLUMN_NAME = 'estudiante_id'
            """))
            
            if result.fetchone()[0] > 0:
                print("✓ Column 'estudiante_id' already exists. No migration needed.")
                return
            
            # Add the estudiante_id column
            print("Adding estudiante_id column...")
            connection.execute(text("""
                ALTER TABLE proyectoversion ADD COLUMN estudiante_id INT NULL
            """))
            print("✓ Column added successfully")
            
            # Add foreign key constraint
            print("Adding foreign key constraint...")
            connection.execute(text("""
                ALTER TABLE proyectoversion ADD CONSTRAINT fk_proyectoversion_estudiante 
                FOREIGN KEY (estudiante_id) REFERENCES estudiante(id) ON DELETE SET NULL
            """))
            print("✓ Foreign key constraint added")
            
            # Create index
            print("Creating index...")
            connection.execute(text("""
                CREATE INDEX idx_proyectoversion_estudiante_id ON proyectoversion(estudiante_id)
            """))
            print("✓ Index created")
            
            print("\n✅ Migration completed successfully!")
            print("\nNote: Existing proyectoversion records will have estudiante_id = NULL")
            print("You may want to update them manually if needed.")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
