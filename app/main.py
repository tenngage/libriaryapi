from typing import List, Callable
from fastapi import FastAPI, Depends, HTTPException, status, Response, Cookie
from datetime import datetime
from sqlalchemy.orm import Session
from . import crud, models, schemas, auth
from .database import engine
from .dependencies import get_db, get_current_user

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

@app.post("/books/", response_model=schemas.Book)
def create_book(
    book: schemas.BookCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    return crud.create_book(db, book)

@app.get("/books/", response_model=list[schemas.Book])
def read_books(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    return crud.get_books(db, skip=skip, limit=limit)

@app.delete("/books/delete/{book_id}", response_model=schemas.Book)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    db_book = crud.delete_book(db, book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return db_book

@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=schemas.AccessToken)
def login(
    response: Response,
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    db_user = crud.get_user_by_username(db, username=user.username)
    if not db_user or not auth.verify_password(
        user.password,
        db_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token = auth.create_access_token(data={"sub": db_user.username})
    refresh_token = auth.create_refresh_token(data={"sub": db_user.username})
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/refresh-token", response_model=schemas.AccessToken)
def get_new_access_token(
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh-token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    username = auth.verify_refresh_token(refresh_token, db)
    access_token = auth.create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/revoke-token", response_model=schemas.RevokedToken)
def revoke_token(
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    jti = auth.get_jti(refresh_token)
    if db.query(models.RevokedToken).filter(models.RevokedToken.jti == jti).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token already revoked"
        )
    db_revoked_token = models.RevokedToken(jti=jti)
    db.add(db_revoked_token)
    db.commit()
    db.refresh(db_revoked_token)
    return db_revoked_token

@app.get("/me", response_model=schemas.User)
def read_users_me(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    return crud.get_user_by_username(db, username=current_user)
