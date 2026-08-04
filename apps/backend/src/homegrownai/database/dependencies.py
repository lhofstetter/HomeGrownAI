from .db import DB, DBSession
from ..schemas.settings import settings

db = DB(
    db_driver=settings.db_driver,
    db_host=settings.db_host,
    db_name=settings.db_name,
    db_port=settings.db_port,
    db_password=settings.db_passwd,
    db_user=settings.db_user,
)

def get_db_session():
    with DBSession(db) as session:
        yield session
