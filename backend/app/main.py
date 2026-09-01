from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.prisma_client import db
from app.routers import projects, ecu_details, pages, test_cases
from app.seed import ensure_attributes


@asynccontextmanager
async def lifespan(app:FastAPI):
    await db.connect()
    await ensure_attributes()
    yield
    await db.disconnect()


app = FastAPI(title="Embedded Config API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

api_prefix = "/api"
app.include_router(projects.router, prefix=api_prefix)
app.include_router(ecu_details.router, prefix=api_prefix)
app.include_router(pages.router, prefix=api_prefix)
app.include_router(test_cases.router, prefix=api_prefix)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}