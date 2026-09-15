import pytest
from homegrownai.database.dependencies import get_db_session
from homegrownai.database.models import User
from homegrownai.schemas.settings import settings
from sqlalchemy.orm import Session


@pytest.fixture
def db_session():
    yield from get_db_session()


@pytest.fixture
def test_user(db_session: Session) -> User:
    user: User | None = (
        db_session.query(User).filter(User.username == settings.test_user).first()
    )

    assert user != None

    return user
