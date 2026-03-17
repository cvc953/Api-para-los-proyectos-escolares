from sqlmodel import SQLModel, Field, create_engine
from typing import Optional

class TestModel(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str

if __name__ == "__main__":
    print("Test model created successfully")
    print(TestModel.__annotations__)