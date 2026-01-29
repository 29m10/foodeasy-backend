# app/services/twilio_otp_service.py

"""
Send OTP via Twilio Messages API (SMS from your Twilio number) and verify codes
stored in the backend. Uses: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER.
"""

import json
import os
import secrets
import time
from typing import Dict, Any

from dotenv import load_dotenv

load_dotenv()

def _env(key: str, default: str = "") -> str:
    v = os.getenv(key) or default
    return v.strip() if isinstance(v, str) else ""

TWILIO_ACCOUNT_SID = _env("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = _env("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = _env("TWILIO_PHONE_NUMBER")  # From number, e.g. +18507887201
# Optional: Twilio Content Template SID (starts with HX, 34 chars). If set, SMS uses template.
# Template must use {{OTP}} = OTP code, {{X}} = validity in minutes (e.g. "10" for 600s).
TWILIO_OTP_CONTENT_SID = _env("TWILIO_OTP_CONTENT_SID")

# OTP config
OTP_LENGTH = 6
OTP_TTL_SECONDS = int(os.getenv("OTP_TTL_SECONDS", "600"))  # default 600s = 10 min → "2" = "10" in template

# In-memory store: phone_number -> {"code": str, "expires_at": float}
_otp_store: Dict[str, Dict[str, Any]] = {}
_twilio_client = None


def get_twilio_client():
    """Get or create Twilio client. Uses env vars for credentials."""
    global _twilio_client
    if _twilio_client is None:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            raise ValueError(
                "Twilio credentials not configured. "
                "Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in your .env file."
            )
        from twilio.rest import Client
        _twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    return _twilio_client


def _get_from_number() -> str:
    if not TWILIO_PHONE_NUMBER or not TWILIO_PHONE_NUMBER.strip():
        raise ValueError(
            "Twilio phone number not configured. "
            "Set TWILIO_PHONE_NUMBER in your .env (e.g. +18507887201)."
        )
    return TWILIO_PHONE_NUMBER


def _generate_otp() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(OTP_LENGTH))


def _clean_expired():
    now = time.time()
    expired = [p for p, v in _otp_store.items() if v["expires_at"] <= now]
    for p in expired:
        del _otp_store[p]


def send_otp(phone_number: str) -> None:
    """
    Generate a 6-digit OTP, store it (with TTL), and send it via Twilio Messages API (SMS).
    Uses Content Template (TWILIO_OTP_CONTENT_SID) if set; otherwise sends plain body.
    Phone number must be E.164 format (e.g. +919952907025).
    """
    _clean_expired()
    code = _generate_otp()
    expires_at = time.time() + OTP_TTL_SECONDS
    _otp_store[phone_number] = {"code": code, "expires_at": expires_at}

    client = get_twilio_client()
    from_number = _get_from_number()

    if TWILIO_OTP_CONTENT_SID:
        # Content SID must be HX + 32 chars (34 total). Template: {{OTP}} = code, {{X}} = validity minutes.
        _sid = TWILIO_OTP_CONTENT_SID.strip()
        if not (_sid.startswith("HX") and len(_sid) == 34):
            raise ValueError(
                f"TWILIO_OTP_CONTENT_SID must be a 34-character SID starting with HX (got {len(_sid)} chars). "
                "Check Twilio Console > Content Template Builder for the correct Content SID."
            )
        validity_minutes = str(OTP_TTL_SECONDS // 60)
        content_variables = json.dumps({"OTP": code, "X": validity_minutes})
        client.messages.create(
            to=phone_number,
            from_=from_number,
            content_sid=_sid,
            content_variables=content_variables,
        )
    else:
        body = f"Your FoodEasy verification code is {code}. Valid for {OTP_TTL_SECONDS // 60} minutes."
        client.messages.create(
            to=phone_number,
            from_=from_number,
            body=body,
        )
    print(f"[Twilio OTP] Code sent to {phone_number[:6]}*** (expires in {OTP_TTL_SECONDS}s)")


def verify_otp(phone_number: str, code: str) -> bool:
    """
    Verify the OTP code for the given phone number (backend-stored code).
    Returns True if code matches and is not expired, False otherwise.
    """
    _clean_expired()
    entry = _otp_store.get(phone_number)
    if not entry:
        print(f"[Twilio OTP] No OTP found for {phone_number[:6]}***")
        return False
    if entry["expires_at"] <= time.time():
        del _otp_store[phone_number]
        print(f"[Twilio OTP] OTP expired for {phone_number[:6]}***")
        return False
    if entry["code"] != code.strip():
        print(f"[Twilio OTP] Invalid code for {phone_number[:6]}***")
        return False
    del _otp_store[phone_number]
    print(f"[Twilio OTP] Verification approved for {phone_number[:6]}***")
    return True
