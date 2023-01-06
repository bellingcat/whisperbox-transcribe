from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
import app.db.models as models

client = TestClient(app)


def test_create_task(db_session: Session) -> None:
    jobs = db_session.query(models.Job).all()
    assert len(jobs) == 0
