import os
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from app.captcha import get_captcha_text
from app.main import app
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import database_exists, create_database, drop_database
from app.database import Base, get_db

load_dotenv()

TEST_DATABASE_URL = os.getenv("DATABASE_URL") + "_test"

engine = create_engine(TEST_DATABASE_URL)
if not database_exists(engine.url):
    create_database(engine.url)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    drop_database(engine.url)


@pytest.fixture()
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    return TestClient(app)


route_prefix = "/captcha"


def test_get_captcha(client: TestClient):
    response = client.get(route_prefix)
    assert response.status_code == 200
    assert "id" in response.json()
    assert "image" in response.json()


def test_validate_captcha(client: TestClient, db: Session):
    response = client.get(route_prefix)
    assert response.status_code == 200
    data = response.json()
    id = data["id"]
    text = "wrong"

    response = client.post(route_prefix + "/validate", json={"id": id, "text": text})
    assert not response.json()

    text = get_captcha_text(db, id)
    assert text

    response = client.post(route_prefix + "/validate", json={"id": id, "text": text})
    assert response.json()
