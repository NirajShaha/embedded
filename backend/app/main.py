from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, async_session_factory, engine, ensure_database
from app.routers import pages, projects
from app.seed import ensure_attributes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_database()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_factory() as session:
        await ensure_attributes(session)
    yield
    await engine.dispose()


app = FastAPI(title="Embedded Config API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = "/api"
app.include_router(projects.router, prefix=api_prefix)
app.include_router(pages.router, prefix=api_prefix)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}