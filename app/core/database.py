from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def create_tables() -> None:
    """Creates all tables if they don't exist yet. Called on app startup."""
    import app.models.user  # noqa: F401
    import app.models.video  # noqa: F401
    import app.models.quiz  # noqa: F401
    import app.models.flashcard  # noqa: F401
    import app.models.session  # noqa: F401

    Base.metadata.create_all(bind=engine)
