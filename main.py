import hashlib
import hmac
import os
import secrets
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from email_validator import EmailNotValidError, validate_email
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from database import get_connection, initialize_database


BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app):
    initialize_database()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET") or secrets.token_hex(32),
    same_site="lax",
    max_age=86400,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def render(request, page, **context):
    return templates.TemplateResponse(request=request, name=page, context=context)


def normalize_email(email):
    return validate_email(email.strip(), check_deliverability=False).normalized.lower()


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600000)
    return f"{salt}${digest.hex()}"


@app.get("/")
def home(request: Request):
    return RedirectResponse("/dashboard" if request.session.get("user_id") else "/signup", status_code=303)


@app.get("/signup")
def signup_page(request: Request):
    return render(request, "signup.html")


@app.post("/signup")
def signup(request: Request, name: str = Form(""), email: str = Form(""), password: str = Form("")):
    name = name.strip()
    error = None
    if not name or not email.strip() or not password:
        error = "Please fill out all fields."
    else:
        try:
            email = normalize_email(email)
        except EmailNotValidError:
            error = "Please enter a valid email address."
        if not error and len(password) < 6:
            error = "Your password must be at least 6 characters."
    if not error:
        with get_connection() as connection:
            if connection.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
                error = "This email is already registered. Please log in."
            else:
                try:
                    connection.execute(
                        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                        (name, email, hash_password(password)),
                    )
                except sqlite3.IntegrityError:
                    error = "This email is already registered. Please log in."
    if error:
        return render(request, "signup.html", error=error, name=name, email=email)
    return RedirectResponse("/login?created=1", status_code=303)


@app.get("/login")
def login_page(request: Request):
    message = "Your account is ready. Log in to get started." if request.query_params.get("created") == "1" else None
    return render(request, "login.html", message=message)


@app.post("/login")
def login(request: Request, email: str = Form(""), password: str = Form("")):
    with get_connection() as connection:
        user = connection.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    if user and hmac.compare_digest(hash_password(password, user["password"].split("$")[0]), user["password"]):
        request.session.clear()
        request.session["user_id"] = user["id"]
        return RedirectResponse("/dashboard", status_code=303)
    return render(request, "login.html", error="Email or password is incorrect. Please try again.", email=email)


@app.get("/forgot-password")
def forgot_password_page(request: Request):
    return render(request, "forgot_password.html")


@app.post("/forgot-password")
def forgot_password(request: Request, email: str = Form("")):
    try:
        email = normalize_email(email)
    except EmailNotValidError:
        return render(request, "forgot_password.html", error="Please enter a valid email address.", email=email)
    with get_connection() as connection:
        user = connection.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        return render(request, "forgot_password.html", error="No account was found with this email.", email=email)
    return render(request, "forgot_password.html", message="Account found. This local demo cannot send reset emails yet.", email=email)


@app.get("/dashboard")
def dashboard(request: Request):
    with get_connection() as connection:
        user = connection.execute("SELECT name, email FROM users WHERE id = ?", (request.session.get("user_id"),)).fetchone()
    if not user:
        request.session.clear()
        return RedirectResponse("/login", status_code=303)
    return render(request, "dashboard.html", user=user)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
