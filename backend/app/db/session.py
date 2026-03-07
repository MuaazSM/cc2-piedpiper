"""
Database engine and session factory.

Sets up the SQLAlchemy engine (using the URL from config) and provides:
- SessionLocal: a session factory for creating DB sessions
- get_db(): a FastAPI dependency that yields a session per request
  and ensures it gets closed afterward (no leaked connections).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import settings

# SQLite doesn't support multiple threads hitting the same connection by default.
# check_same_thread=False is required so FastAPI's async workers don't crash.
# This isn't needed for PostgreSQL, so we only add it for SQLite URLs.
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create the engine — this is the actual connection pool to the database.
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

# Session factory — each call to SessionLocal() gives us a fresh DB session.
# autocommit=False means we control when commits happen (explicit > implicit).
# autoflush=False means we decide when to flush pending changes to the DB.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency for database sessions.

    Usage in any route:
        @router.get("/something")
        def my_route(db: Session = Depends(get_db)):
            ...

    The `yield` makes this a generator — FastAPI will call next() to get
    the session, run the route, and then hit the `finally` block to close it.
    This guarantees cleanup even if the route throws an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()