from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

LOCAL_UI_ORIGINS = (
    "http://127.0.0.1:1420",
    "http://localhost:1420",
    "tauri://localhost",
)


app = FastAPI(
    title="Ligent Backend",
    version="0.1.0",
    description="Local backend boundary for the Ligent desktop app.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(LOCAL_UI_ORIGINS),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(router)
