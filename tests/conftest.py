import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_db, get_current_user
from app.database import Base, TestSessionLocal, test_engine

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def test_db():
    db = TestSessionLocal()
    transaction = db.begin()
    try:
        yield db
    finally:
        transaction.rollback()
        db.close()

@pytest.fixture(scope="function")
def client(test_db):
    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[get_current_user] = lambda: "test_user"
    yield TestClient(app)
    app.dependency_overrides.clear()
