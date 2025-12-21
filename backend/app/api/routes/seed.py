from fastapi import APIRouter

from backend.app.db.session import engine
from backend.app.services.seed_fake_data import SeedConfig, seed_fake_data

router = APIRouter(prefix="/seed", tags=["seed"])


@router.post("")
def seed() -> dict[str, int]:
    return seed_fake_data(engine=engine, config=SeedConfig())
