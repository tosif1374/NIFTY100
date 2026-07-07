import os
import sqlite3
from typing import Annotated, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .auth import verify_token

DB_PATH = os.getenv("DB_PATH", "./db/nifty100.db")
SNAPSHOT_DIR = os.getenv("SNAPSHOT_DIR", "./data/snapshots")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    FastAPI dependency: yields a read-only SQLite connection per request.
    Connection is automatically closed after the response is sent.
    """
    conn = sqlite3.connect(
    f"file:{DB_PATH}?mode=ro",
    uri=True,
    check_same_thread=False
)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """
    FastAPI dependency: decodes JWT and returns the payload dict.
    Raises 401 if token is missing, expired, or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    return payload


def get_snapshot_dir() -> str:
    """Return path to pre-computed snapshot directory."""
    return SNAPSHOT_DIR


# Type aliases for cleaner route signatures
DbDep = Annotated[sqlite3.Connection, Depends(get_db)]
CurrentUser = Annotated[dict, Depends(get_current_user)]
SnapshotDir = Annotated[str, Depends(get_snapshot_dir)]