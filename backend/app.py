from fastapi import FastAPI

from api.routes import router


app = FastAPI(
    title="Ligent Backend",
    version="0.1.0",
    description="Local backend boundary for the Ligent desktop app.",
)

app.include_router(router)

