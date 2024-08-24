from contextlib import asynccontextmanager
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from fastapi import FastAPI
from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow


@asynccontextmanager
async def lifespan(app: FastAPI):
    # This should be a remote Redis or Firestore...
    # for expiry and horizontal scalability
    app.state.fake_sessions = {}
    yield


app = FastAPI(title="My Google OAuth middleware", lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/session")
def create_session():
    flow = Flow.from_client_secrets_file(
        "./client_secret.json",
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/calendar.events.readonly",
        ],
    )
    flow.redirect_uri = "https://fastapi.example.test/oauth2callback"
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="select_account",
    )
    body = {
        "state": state,
        "auth_url": auth_url,
    }
    app.state.fake_sessions[state] = body
    return body


@app.get(
    "/oauth2callback",
)
def callback_google_oauth2(state: str, code: str):
    # Check state from auth server actually exists
    if state not in app.state.fake_sessions:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    flow = Flow.from_client_secrets_file(
        "./client_secret.json",
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/calendar.events.readonly",
        ],
    )
    flow.redirect_uri = "https://fastapi.example.test/oauth2callback"
    flow.fetch_token(code=code)

    credentials = flow.credentials
    access_token = credentials.token
    refresh_token = credentials.refresh_token
    token = credentials.id_token

    id_info = id_token.verify_token(
        credentials.id_token,
        requests.Request(),
    )

    app.state.fake_sessions[state]["access_token"] = access_token
    app.state.fake_sessions[state]["refresh_token"] = refresh_token
    app.state.fake_sessions[state]["id_token"] = token
    app.state.fake_sessions[state]["id_info"] = id_info

    response = RedirectResponse("https://streamlit.example.test")
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    response.set_cookie(
        "__streamlit_session",
        state,
        domain="example.test",
        expires=expires_at,
        secure=True,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        "__streamlit_access_token",
        access_token,
        domain="example.test",
        expires=expires_at,
        secure=True,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        "__streamlit_refresh_token",
        refresh_token,
        domain="example.test",
        expires=expires_at,
        secure=True,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        "__streamlit_id_token",
        token,
        domain="example.test",
        expires=expires_at,
        secure=True,
        httponly=True,
        samesite="lax",
    )
    return response
