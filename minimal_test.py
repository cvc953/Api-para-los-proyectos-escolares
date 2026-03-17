# Minimal test to check if basic FastAPI works
try:
    from fastapi import FastAPI
    print("FastAPI import successful")
except Exception as e:
    print(f"FastAPI import failed: {e}")
    import traceback
    traceback.print_exc()

# Minimal test to check if SQLModel works
try:
    from sqlmodel import SQLModel, Field
    from typing import Optional
    
    class TestModel(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
    
    print("SQLModel import and model creation successful")
except Exception as e:
    print(f"SQLModel test failed: {e}")
    import traceback
    traceback.print_exc()