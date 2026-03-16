"""
Zynochat Auth Server — FastAPI
- HTML files serve karta hai /static folder se
- Supabase keys sirf .env mein hain
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
import httpx, os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL      = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("❌ .env mein SUPABASE_URL aur SUPABASE_ANON_KEY set karo!")

SUPABASE_HEADERS = {
    "Content-Type": "application/json",
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
}

app = FastAPI(title="Zynochat")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # production mein sirf apna domain
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ─────────────────────────────────────────────────────
#  HTML Pages Serve karo  (files: static/ folder mein)
# ─────────────────────────────────────────────────────
# Folder structure:
#   project/
#   ├── server.py
#   ├── .env
#   └── static/
#       ├── login.html
#       ├── otp.html
#       └── dashboard.html

@app.get("/")
async def root():
    return FileResponse("static/login.html")

@app.get("/login")
async def login_page():
    return FileResponse("static/login.html")

@app.get("/otp")
async def otp_page():
    return FileResponse("static/otp.html")

@app.get("/dashboard")
async def dashboard_page():
    return FileResponse("static/dashboard.html")

# Static assets (CSS, JS, images) ke liye
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─────────────────────────────────────────────────────
#  Auth API Routes
# ─────────────────────────────────────────────────────

class EmailRequest(BaseModel):
    email: EmailStr

class OtpVerifyRequest(BaseModel):
    email: EmailStr
    token: str


@app.post("/auth/send-otp")
async def send_otp(body: EmailRequest):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{SUPABASE_URL}/auth/v1/otp",
            headers=SUPABASE_HEADERS,
            json={"email": body.email, "create_user": True},
        )
    data = res.json()
    if not res.is_success:
        raise HTTPException(
            status_code=res.status_code,
            detail=data.get("msg") or data.get("error_description") or "OTP bhejne mein error"
        )
    return {"success": True, "message": "OTP bhej diya!"}


@app.post("/auth/verify-otp")
async def verify_otp(body: OtpVerifyRequest):
    if len(body.token) != 6 or not body.token.isdigit():
        raise HTTPException(status_code=400, detail="OTP 6 digits ka hona chahiye")

    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{SUPABASE_URL}/auth/v1/verify",
            headers=SUPABASE_HEADERS,
            json={"type": "email", "email": body.email, "token": body.token},
        )
    data = res.json()
    if not res.is_success:
        raise HTTPException(
            status_code=res.status_code,
            detail=data.get("msg") or data.get("error_description") or "OTP galat hai"
        )

    user = data.get("user", {})
    return {
        "success": True,
        "user": {
            "id": user.get("id"),
            "email": user.get("email"),
            "created_at": user.get("created_at"),
        }
    }

# ─────────────────────────────────────────────────────
# Run: uvicorn server:app --host 0.0.0.0 --port 8000
# ─────────────────────────────────────────────────────
