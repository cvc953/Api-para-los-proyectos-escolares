# Based on SQLModel documentation examples
from typing import Optional
from sqlmodel import SQLModel, Field

class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: Optional[int] = Field(default=None)

if __name__ == "__main__":
    # Test creating an instance
    hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
    print(f"Hero created: {hero_1}")
    print(f"Hero ID: {hero_1.id}")