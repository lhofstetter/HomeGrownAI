from typing import Annotated
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/")
async def home(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"message": "hello world!", "token": token}
