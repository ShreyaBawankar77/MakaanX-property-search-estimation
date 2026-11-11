import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from google.auth import exceptions as google_auth_exceptions
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import PredictionHistory, User, UserCredential

router = APIRouter()
SESSION_COOKIE = "makaanx_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7
DEFAULT_SESSION_SECRET = "makaanx-development-session-secret-key-2026"
PASSWORD_HASH_ITERATIONS = 310_000


@router.get("/api/config")
def public_config() -> dict[str, str | None]:
    return {"google_client_id": os.getenv("GOOGLE_CLIENT_ID")}


class GoogleCredential(BaseModel):
    credential: str


class AccountCredentials(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().casefold()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Enter a valid email address.")
        return email


class RegisterAccount(AccountCredentials):
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Enter your name.")
        return name


class PredictionHistoryPayload(BaseModel):
    request: dict[str, Any]
    result: dict[str, Any]


def _encode_session(payload: dict[str, Any], secret: str) -> str:
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def _decode_session(token: str, secret: str) -> dict[str, Any] | None:
    try:
        encoded, signature = token.split(".", 1)
        expected = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except (ValueError, json.JSONDecodeError):
        return None


def _cookie_options() -> dict[str, Any]:
    return {
        "httponly": True,
        "secure": os.getenv("COOKIE_SECURE", "false").lower() == "true",
        "samesite": "lax",
        "max_age": SESSION_MAX_AGE,
        "path": "/",
    }


def _session_secret() -> str:
    return os.getenv("APP_SESSION_SECRET") or DEFAULT_SESSION_SECRET


def _set_user_session(
    response: Response,
    user: User,
    name: str,
    picture: str | None = None,
) -> None:
    payload = {
        "user_id": user.id,
        "email": user.email,
        "name": name,
        "picture": picture,
        "exp": int(time.time()) + SESSION_MAX_AGE,
    }
    response.set_cookie(SESSION_COOKIE, _encode_session(payload, _session_secret()), **_cookie_options())


def _authenticated_user(request: Request, db: Session) -> tuple[User, dict[str, Any]] | None:
    token = request.cookies.get(SESSION_COOKIE)
    payload = _decode_session(token, _session_secret()) if token else None
    if not payload:
        return None

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first() if user_id else None
    if user is None and payload.get("email"):
        user = db.query(User).filter(User.email == payload["email"]).first()
    return (user, payload) if user is not None else None


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, PASSWORD_HASH_ITERATIONS
    )
    return f"{PASSWORD_HASH_ITERATIONS}${salt.hex()}${password_hash.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        iterations_text, salt_hex, hash_hex = stored_hash.split("$", 2)
        iterations = int(iterations_text)
        expected = bytes.fromhex(hash_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), iterations
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def _history_entry(record: PredictionHistory) -> dict[str, Any]:
    return {
        "id": record.id,
        "request": json.loads(record.request_data),
        "result": json.loads(record.result_data),
        "created_at": record.created_at.isoformat(),
    }


@router.post("/api/auth/register", status_code=201)
def register_account(body: RegisterAccount, response: Response) -> dict[str, Any]:
    with SessionLocal() as db:
        if db.query(User).filter(User.email == body.email).first():
            raise HTTPException(status_code=409, detail="An account with this email already exists.")

        user = User(username=body.email, email=body.email)
        db.add(user)
        try:
            db.flush()
            db.add(UserCredential(user_id=user.id, password_hash=_hash_password(body.password)))
            db.commit()
        except IntegrityError as error:
            db.rollback()
            raise HTTPException(status_code=409, detail="An account with this email already exists.") from error
        db.refresh(user)
        _set_user_session(response, user, body.name)
        return {"user": {"email": user.email, "name": body.name, "picture": None}}


@router.post("/api/auth/login")
def sign_in_with_password(body: AccountCredentials, response: Response) -> dict[str, Any]:
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == body.email).first()
        credential = (
            db.query(UserCredential).filter(UserCredential.user_id == user.id).first()
            if user is not None
            else None
        )
        if credential is None or not _verify_password(body.password, credential.password_hash):
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")

        name = user.username if user.username != user.email else user.email.split("@", 1)[0]
        _set_user_session(response, user, name)
        return {"user": {"email": user.email, "name": name, "picture": None}}


@router.post("/api/auth/google")
def sign_in_with_google(body: GoogleCredential, response: Response) -> dict[str, Any]:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    session_secret = os.getenv("APP_SESSION_SECRET")
    if not client_id or not session_secret:
        raise HTTPException(status_code=503, detail="Google SSO is not configured on the server.")

    try:
        claims = id_token.verify_oauth2_token(body.credential, google_requests.Request(), client_id)
    except (ValueError, google_auth_exceptions.GoogleAuthError) as error:
        raise HTTPException(status_code=401, detail="Google could not verify this sign-in.") from error

    if claims.get("email_verified") is not True:
        raise HTTPException(status_code=403, detail="Use a Google account with a verified email address.")

    subject = claims.get("sub")
    email = claims.get("email")
    if not subject or not email:
        raise HTTPException(status_code=401, detail="Google did not return a verified account.")
    email = email.strip().casefold()

    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(username=f"google:{subject}", email=email)
            db.add(user)
            try:
                db.commit()
            except IntegrityError as error:
                db.rollback()
                user = db.query(User).filter(User.email == email).first()
                if user is None:
                    raise HTTPException(status_code=409, detail="Could not create this account.") from error
        name = claims.get("name") or email.split("@", 1)[0]
        picture = claims.get("picture")
        _set_user_session(response, user, name, picture)
        return {"user": {"email": user.email, "name": name, "picture": picture}}


@router.post("/api/auth/demo")
def sign_in_demo(response: Response) -> dict[str, Any]:
    email = "demo.buyer@makaanx.com"
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(username=email, email=email)
            db.add(user)
            db.commit()
            db.refresh(user)
        _set_user_session(response, user, "Demo Buyer")
        return {"user": {"email": user.email, "name": "Demo Buyer", "picture": None}}


@router.get("/api/auth/session")
def get_session(request: Request) -> dict[str, Any]:
    with SessionLocal() as db:
        authenticated = _authenticated_user(request, db)
        if authenticated is None:
            return {"user": None}
        user, payload = authenticated
        return {"user": {
            "email": user.email,
            "name": payload.get("name") or user.username,
            "picture": payload.get("picture"),
        }}


@router.get("/api/auth/history")
def get_prediction_history(request: Request) -> dict[str, Any]:
    with SessionLocal() as db:
        authenticated = _authenticated_user(request, db)
        if authenticated is None:
            raise HTTPException(status_code=401, detail="Sign in to view your saved estimates.")
        user, _ = authenticated
        records = (
            db.query(PredictionHistory)
            .filter(PredictionHistory.user_id == user.id)
            .order_by(desc(PredictionHistory.created_at), desc(PredictionHistory.id))
            .limit(50)
            .all()
        )
        return {"history": [_history_entry(record) for record in records]}


@router.post("/api/auth/history", status_code=201)
def save_prediction_history(
    body: PredictionHistoryPayload,
    request: Request,
) -> dict[str, Any]:
    try:
        serialized_request = json.dumps(body.request, separators=(",", ":"), allow_nan=False)
        serialized_result = json.dumps(body.result, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail="Estimate data must be valid JSON.") from error
    if len(serialized_request) + len(serialized_result) > 100_000:
        raise HTTPException(status_code=413, detail="This estimate is too large to save.")

    with SessionLocal() as db:
        authenticated = _authenticated_user(request, db)
        if authenticated is None:
            raise HTTPException(status_code=401, detail="Sign in to save your estimates.")
        user, _ = authenticated
        record = PredictionHistory(
            user_id=user.id,
            request_data=serialized_request,
            result_data=serialized_result,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return {"entry": _history_entry(record)}


@router.post("/api/auth/logout")
def sign_out(response: Response) -> dict[str, str]:
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="lax")
    return {"status": "signed_out"}