"""
Zynochat Auth Proxy — FastAPI
Keys sirf .env file mein hain, frontend ko kabhi nahi milti
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import httpx
import os
from dotenv import load_dotenv

load_dotenv()  # .env file se keys lo

# ── Keys sirf yahan, .env se ──────────────────
SUPABASE_URL      = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
# ─────────────────────────────────────────────

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("❌ .env mein SUPABASE_URL aur SUPABASE_ANON_KEY set karo!")

SUPABASE_HEADERS = {
    "Content-Type": "application/json",
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
}

app = FastAPI(title="Zynochat Auth Proxy")

# ── CORS — sirf apna domain allow karo ────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "https://APNI-WEBSITE.com",   # ← apna production domain
    ],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


# ── Models ─────────────────────────────────────
class EmailRequest(BaseModel):
    email: EmailStr

class OtpVerifyRequest(BaseModel):
    email: EmailStr
    token: str


# ── Route 1: OTP Bhejo ─────────────────────────
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


# ── Route 2: OTP Verify karo ───────────────────
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

    # ⚠️ Access token frontend ko mat bhejo — sirf zaroorat ki info bhejo
    user = data.get("user", {})
    return {
        "success": True,
        "user": {
            "id": user.get("id"),
            "email": user.get("email"),
            "created_at": user.get("created_at"),
        }
        # access_token yahan NAHI bhej rahe — server pe session manage karo
    }


# ── Run ────────────────────────────────────────
# uvicorn server:app --host 0.0.0.0 --port 8000
