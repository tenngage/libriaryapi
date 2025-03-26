from fastapi.testclient import TestClient
from app.main import app
from app.models import Book

def test_post_books(client, test_db):
    book_data = {
        "title" : "Idiot",
        "author" : "Dostoevsky",
        "year" : 1868
    }

    response = client.post("/books/", json=book_data)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == book_data["title"]
    assert data["author"] == book_data["author"]
    assert data["year"] == book_data["year"]
    assert "id" in data

    book = test_db.query(Book).filter(Book.id == data["id"]).first()
    assert book is not None
