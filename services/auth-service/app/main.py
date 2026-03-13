from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from prometheus_client import Counter, generate_latest
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.auth import (
    create_access_token,
    get_password_hash,
    invalidate_token,
    verify_password,
    verify_token,
)
from app.database import Base, engine, get_db
from app.models import User
from app.schemas import Token, UserCreate, UserResponse

app = FastAPI(title="FIAP X - Auth Service", version="1.0.0")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Prometheus metrics
REQUEST_COUNT = Counter(
    "auth_requests_total", "Total auth requests", ["method", "endpoint"]
)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


@app.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    REQUEST_COUNT.labels(method="POST", endpoint="/register").inc()

    existing_user = (
        db.query(User)
        .filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        )
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    REQUEST_COUNT.labels(method="POST", endpoint="/login").inc()

    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    REQUEST_COUNT.labels(method="GET", endpoint="/me").inc()
    return current_user


@app.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    REQUEST_COUNT.labels(method="POST", endpoint="/logout").inc()
    invalidate_token(str(current_user.id))
    return {"message": "Logout successful"}


@app.get("/validate")
def validate_token_endpoint(current_user: User = Depends(get_current_user)):
    return {"user_id": current_user.id, "username": current_user.username}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "auth-service"}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
