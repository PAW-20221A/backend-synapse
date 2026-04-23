from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import create_tables
from app.routers import auth, quiz, sessions, transcript


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="Synapse API",
    version="0.1.0",
    description="Plataforma de estudos que transforma vídeos do YouTube em sessões interativas.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(quiz.router)
app.include_router(sessions.router)
app.include_router(transcript.router)


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {"message": "Synapse API online"}
