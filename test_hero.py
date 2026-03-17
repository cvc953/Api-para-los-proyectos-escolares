from typing import Optional
from sqlmodel import Field, SQLModel

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = Field(default=None)

if __name__ == "__main__":
    print("Hero model created successfully")
    # Try to create an instance
    hero = Hero(name="Deadpond", secret_name="Dive Wilson")
    print(f"Hero: {hero}")