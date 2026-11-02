"""Virasat — Heritage, Rediscovered (Backend)

FastAPI application for the heritage walk planner.
"""

import os
import sys

# Ensure the backend directory is on the path so relative imports work
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Add the core and db subdirectories for direct imports
core_dir = os.path.join(backend_dir, "core")
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

db_dir = os.path.join(backend_dir, "db")
if db_dir not in sys.path:
    sys.path.insert(0, db_dir)

# Add api subdirectory for v1 imports
api_dir = os.path.join(backend_dir, "api")
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API routes using relative imports within the api package
from api.v1 import auth, plans, sites, routes, submissions, moderation, translations

app = FastAPI(
    title="Virasat API",
    description="Heritage, Rediscovered — Intelligent, constraint-aware heritage walk planner",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Restrict browser origins; set VIRASAT_CORS_ORIGINS to a comma-separated list
# of the production frontend URL(s) when deploying.
cors_origins = [origin.strip() for origin in os.getenv(
    'VIRASAT_CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000'
).split(',') if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(plans.router, prefix="/plans", tags=["plans"])
app.include_router(sites.router, prefix="/sites", tags=["sites"])
app.include_router(routes.router, prefix="/routes", tags=["routes"])
app.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
app.include_router(moderation.router, prefix="/moderation", tags=["moderation"])
app.include_router(translations.router, prefix="/translations", tags=["translations"])


@app.get("/", tags=["root"])
async def root() -> dict:
    return {"message": "Virasat API is running", "version": "0.1.0"}


@app.get("/health", tags=["root"])
async def health_check() -> dict:
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
