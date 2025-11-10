from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from dependencies import extract_bearer_token
from schemas import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    Product,
    SignupRequest,
    TokenPayload,
    UserResponse,
)
from supabase_client import get_service_client
load_dotenv()  # Load environment variables from .env file
app = FastAPI(title="Filmee API")

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")

# Allow the static frontend (or other clients) to reach the API while iterating locally.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_token_payload(session: Any | None) -> TokenPayload | None:
    if not session:
        return None

    return TokenPayload(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_in=session.expires_in,
    )


@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request) -> HTMLResponse:
    base_url = str(request.base_url).rstrip("/")
    context = {"request": request, "api_base_url": base_url}
    return templates.TemplateResponse("index.html", context)


@app.post("/api/auth/signup", response_model=AuthResponse)
async def signup(payload: SignupRequest) -> AuthResponse:
    supabase = get_service_client()
    try:
        result = supabase.auth.sign_up({"email": payload.email, "password": payload.password})
    except Exception as exc:  # supabase-py raises generic exceptions for auth errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not result.user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")

    token_payload = _build_token_payload(result.session)

    return AuthResponse(user_id=result.user.id, email=result.user.email or payload.email, token=token_payload)


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(payload: LoginRequest) -> AuthResponse:
    supabase = get_service_client()
    try:
        result = supabase.auth.sign_in_with_password({"email": payload.email, "password": payload.password})
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    if not result.user or not result.session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return AuthResponse(
        user_id=result.user.id,
        email=result.user.email or payload.email,
        token=_build_token_payload(result.session),
    )


@app.post("/api/auth/logout")
async def logout(payload: LogoutRequest) -> dict[str, str]:
    supabase = get_service_client()
    try:
        supabase.auth.admin.sign_out(payload.refresh_token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"status": "ok"}


@app.get("/api/auth/me", response_model=UserResponse)
async def current_user(token: str = Depends(extract_bearer_token)) -> UserResponse:
    supabase = get_service_client()
    try:
        response = supabase.auth.get_user(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    if not response.user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse(user_id=response.user.id, email=response.user.email or "")


@app.get("/api/products", response_model=list[Product])
async def list_products() -> list[Product]:
    supabase = get_service_client()
    try:
        query = supabase.table("products").select("*").order("created_at")
        response = query.execute()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    data = response.data or []
    products: list[Product] = []
    for item in data:
        products.append(
            Product(
                id=item.get("id"),
                name=item.get("name", ""),
                headline=item.get("headline"),
                description=item.get("description"),
                price_cents=item.get("price_cents"),
                image_url=item.get("image_url"),
            )
        )

    return products
