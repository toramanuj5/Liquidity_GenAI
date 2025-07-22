# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.router import router  # assuming your routes are defined in app/router.py
from app.db import init_db

app = FastAPI(
    title="Liquidity GenAI Compliance API",
    version="1.0"
)

# CORS config (modify as needed)
origins = [
    "http://localhost",
    "http://localhost:8501"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router)

# Init DB on startup
@app.on_event("startup")
def on_startup():
    init_db()




# Serve the vector store directory as static files
app.mount("/vector_store", StaticFiles(directory="vector_store"), name="vector_store")

