from fastapi import FastAPI

from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.seed import router as seed_router
from backend.app.api.routes.outreach import router as outreach_router

app = FastAPI(title="Sponsorship Copilot API", version="0.1.0")

app.include_router(health_router)
app.include_router(seed_router)
app.include_router(outreach_router)
