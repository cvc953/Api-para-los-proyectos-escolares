from typing import Optional
from sqlmodel import SQLModel, Field

# Test 1: Original approach that was failing
print("Test 1: Optional[int] with default=None")
try:
    class Test1(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")

# Test 2: int with default=None
print("\nTest 2: int with default=None")
try:
    class Test2(SQLModel, table=True):
        id: int = Field(default=None, primary_key=True)
        name: str
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")

# Test 3: Optional[int] without default
print("\nTest 3: Optional[int] without default")
try:
    class Test3(SQLModel, table=True):
        id: Optional[int] = Field(primary_key=True)
        name: str
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")

# Test 4: int without default
print("\nTest 4: int without default")
try:
    class Test4(SQLModel, table=True):
        id: int = Field(primary_key=True)
        name: str
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")

# Test 5: Optional[int] with None (not default=None)
print("\nTest 5: Optional[int] with None")
try:
    class Test5(SQLModel, table=True):
        id: Optional[int] = Field(None, primary_key=True)
        name: str
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")