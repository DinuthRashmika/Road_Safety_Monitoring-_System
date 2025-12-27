import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List

app = FastAPI(
    title = "Violence",
    description="Violence",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], #delete, put, post
    allow_headers=["*"] #block unrequired headers
)

@app.get("/hello-world")
def hello_world():
    return {"message": "Hi Pmalai Sapu"}





