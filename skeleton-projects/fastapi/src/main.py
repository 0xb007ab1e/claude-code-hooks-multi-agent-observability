from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import os
from datetime import datetime

app = FastAPI(title="FastAPI Skeleton", version="1.0.0")

# Pydantic models
class User(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str

class MessageResponse(BaseModel):
    message: str

# In-memory storage for demo
users_db: List[UserResponse] = []
user_id_counter = 1

@app.get("/", response_model=MessageResponse)
async def root():
    return MessageResponse(message="FastAPI skeleton API is running!")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/users", response_model=List[UserResponse])
async def get_users():
    return users_db

@app.post("/api/users", response_model=UserResponse, status_code=201)
async def create_user(user: User):
    global user_id_counter
    new_user = UserResponse(
        id=user_id_counter,
        name=user.name,
        email=user.email
    )
    users_db.append(new_user)
    user_id_counter += 1
    return new_user

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    for user in users_db:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
