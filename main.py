import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

class UserRegister(BaseModel):
    email: str
    phone: str
    password: str

@app.get("/")
async def root():
    return {"message": "Casino Backend is Running!"}

@app.post("/register")
async def register(user: UserRegister):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "INSERT INTO Users (email, phone, password_hash, balance) VALUES ($1, $2, $3, $4)",
            user.email, user.phone, user.password, "1000"
        )
        return {"status": "success", "message": "User registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await conn.close()
      
