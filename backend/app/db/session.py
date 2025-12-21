from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from backend.app.core.config import settings


def get_engine() -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True)


engine = get_engine()
