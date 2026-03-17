from typing import Optional
from sqlmodel import SQLModel, Field

print("Creating model...")
try:
    class TestModel(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
    
    print("Model created successfully!")
    print(f"Model annotations: {TestModel.__annotations__}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()