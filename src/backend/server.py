from sqlalchemy import create_engine
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from os import environ
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
db = create_engine(environ['DATABASE_URL'])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
async def default():
    raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown route."
        )

@app.post("/login")
async def login():
    pass
