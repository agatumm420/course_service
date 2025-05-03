from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
import Controllers
from database import SessionLocal
from pydantic import BaseModel
from app import app
from fastapi_pagination import Page, add_pagination
import uvicorn



if __name__ == "__main__":



    app.mount(
        "/resources",
        StaticFiles(directory="resources"),
        name="uploads",
    )
    add_pagination(app)
    uvicorn.run(app, host="127.0.0.1", port=8000)

