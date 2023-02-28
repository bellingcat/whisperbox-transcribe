from typing import Any, Generator

from sqlalchemy.engine import Connection
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.shared.settings import settings

engine = create_engine(settings.DATABASE_URI, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def set_sqlite_pragma(conn: Connection, _: Any) -> None:
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
