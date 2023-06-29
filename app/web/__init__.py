from app.shared.db.base import get_session
from app.web.main import app_factory

app = app_factory(get_session)
