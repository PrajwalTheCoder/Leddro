import base64
import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import encrypt_credential, decrypt_credential, redact_sensitive
from backend.app.models.google_auth import GoogleAccountModel, OAuthStateModel

logger = logging.getLogger("leddro.google_oauth")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GMAIL_PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"

def get_missing_configuration() -> List[str]:
    """
    Returns list of missing Google OAuth environment variable keys.
    """
    missing = []
    if not settings.GOOGLE_CLIENT_ID:
        missing.append("GOOGLE_CLIENT_ID")
    if not settings.GOOGLE_CLIENT_SECRET:
        missing.append("GOOGLE_CLIENT_SECRET")
    if not settings.GOOGLE_REDIRECT_URI:
        missing.append("GOOGLE_REDIRECT_URI")
    return missing

def is_google_configured() -> bool:
    return len(get_missing_configuration()) == 0

def get_oauth_status(db: Session) -> Dict[str, Any]:
    """
    Returns public Google connection status. Never exposes client secrets,
    access tokens, or refresh tokens.
    """
    missing = get_missing_configuration()
    configured = len(missing) == 0

    account = db.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()

    if not account or not account.is_connected:
        return {
            "is_configured": configured,
            "missing_config": missing,
            "is_connected": False,
            "email": None,
            "scopes": [],
            "last_verified": None,
            "connected_at": None,
            "expires_at": None,
            "requires_reauth": False
        }

    scopes_list = []
    if account.scopes:
        try:
            scopes_list = json.loads(account.scopes)
        except Exception:
            scopes_list = account.scopes.split()

    # Determine if expired and lacking refresh token
    has_refresh = bool(account.encrypted_refresh_token)
    is_expired = False
    if account.expires_at:
        now_utc = datetime.now(timezone.utc)
        exp = account.expires_at if account.expires_at.tzinfo else account.expires_at.replace(tzinfo=timezone.utc)
        is_expired = now_utc >= exp

    requires_reauth = is_expired and not has_refresh

    return {
        "is_configured": configured,
        "missing_config": missing,
        "is_connected": True,
        "email": account.email,
        "scopes": scopes_list,
        "last_verified": account.last_verified_at.strftime("%Y-%m-%d %H:%M UTC") if account.last_verified_at else None,
        "connected_at": account.connected_at.strftime("%Y-%m-%d %H:%M UTC") if account.connected_at else None,
        "expires_at": account.expires_at.strftime("%Y-%m-%d %H:%M UTC") if account.expires_at else None,
        "requires_reauth": requires_reauth
    }

def create_authorization_url(db: Session) -> Dict[str, str]:
    """
    Generates a cryptographically secure authorization URL with CSRF state and PKCE challenge.
    """
    missing = get_missing_configuration()
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth credentials missing: {', '.join(missing)}. Please set these in backend environment."
        )

    # Clean expired states
    now_utc = datetime.now(timezone.utc)
    try:
        db.query(OAuthStateModel).filter(OAuthStateModel.expires_at < now_utc).delete()
        db.commit()
    except Exception as e:
        logger.warning(f"Error purging expired states: {e}")
        db.rollback()

    # Cryptographically secure CSRF state
    state = secrets.token_urlsafe(32)

    # PKCE code verifier and challenge (RFC 7636)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")

    # Store state with 10-minute validity
    expires_at = now_utc + timedelta(minutes=10)
    state_record = OAuthStateModel(
        state=state,
        code_verifier=code_verifier,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
        expires_at=expires_at
    )
    db.add(state_record)
    db.commit()

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": settings.GOOGLE_OAUTH_SCOPES,
        "access_type": "offline",
        "prompt": "consent",  # Force consent to ensure refresh_token is returned
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return {
        "authorization_url": auth_url,
        "state": state
    }

async def handle_oauth_callback(code: str, state: str, db: Session) -> Dict[str, Any]:
    """
    Validates CSRF state, exchanges authorization code with Google token endpoint,
    fetches authenticated identity, and securely stores encrypted tokens in database.
    """
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code from Google")
    if not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing OAuth state parameter")

    # Locate and consume state to prevent replay attacks
    state_record = db.query(OAuthStateModel).filter(OAuthStateModel.state == state).first()
    if not state_record:
        logger.warning(f"OAuth state mismatch or replayed: {redact_sensitive(state)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state. Please initiate connection again."
        )

    now_utc = datetime.now(timezone.utc)
    exp = state_record.expires_at if state_record.expires_at.tzinfo else state_record.expires_at.replace(tzinfo=timezone.utc)
    if now_utc > exp:
        db.delete(state_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth authorization session expired. Please try connecting again."
        )

    code_verifier = state_record.code_verifier
    redirect_uri = state_record.redirect_uri

    # Delete state immediately (single use)
    db.delete(state_record)
    db.commit()

    # Exchange code for tokens
    token_payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    if code_verifier:
        token_payload["code_verifier"] = code_verifier

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(GOOGLE_TOKEN_URL, data=token_payload)
    except httpx.RequestError as e:
        logger.error(f"Network error exchanging OAuth code: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to reach Google OAuth token endpoint. Check your internet connection."
        )

    if token_resp.status_code != 200:
        logger.error(f"Google token exchange failed ({token_resp.status_code}): {token_resp.text}")
        err_detail = "Failed to exchange authorization code with Google."
        try:
            err_json = token_resp.json()
            if "error_description" in err_json:
                err_detail = f"Google OAuth error: {err_json['error_description']}"
            elif "error" in err_json:
                err_detail = f"Google OAuth error: {err_json['error']}"
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_detail)

    tokens = token_resp.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_in = tokens.get("expires_in", 3600)
    granted_scopes = tokens.get("scope", "").split()

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google token response did not contain an access token"
        )

    # Retrieve real authenticated user identity from Google userinfo
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            userinfo_resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
    except httpx.RequestError as e:
        logger.error(f"Network error fetching user identity: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve Google user profile information."
        )

    if userinfo_resp.status_code != 200:
        logger.error(f"Google userinfo failed ({userinfo_resp.status_code}): {userinfo_resp.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to retrieve authenticated email address from Google."
        )

    userinfo = userinfo_resp.json()
    real_email = userinfo.get("email")
    google_sub = userinfo.get("id")

    if not real_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authenticated Google account does not have a verified email address."
        )

    # Encrypt credentials before database persistence
    encrypted_access = encrypt_credential(access_token)
    encrypted_refresh = encrypt_credential(refresh_token) if refresh_token else None
    token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    # Upsert default connected Google account
    account = db.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()
    if not account:
        account = GoogleAccountModel(
            id="default",
            email=real_email,
            google_sub=google_sub,
            encrypted_access_token=encrypted_access,
            encrypted_refresh_token=encrypted_refresh,
            token_uri=GOOGLE_TOKEN_URL,
            scopes=json.dumps(granted_scopes),
            expires_at=token_expiry,
            is_connected=True,
            connected_at=datetime.now(timezone.utc),
            last_verified_at=datetime.now(timezone.utc)
        )
        db.add(account)
    else:
        account.email = real_email
        account.google_sub = google_sub
        account.encrypted_access_token = encrypted_access
        if encrypted_refresh:
            account.encrypted_refresh_token = encrypted_refresh
        account.scopes = json.dumps(granted_scopes)
        account.expires_at = token_expiry
        account.is_connected = True
        account.connected_at = datetime.now(timezone.utc)
        account.last_verified_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(account)

    logger.info(f"Successfully connected genuine Google account: {real_email}")
    return {
        "success": True,
        "email": real_email,
        "scopes": granted_scopes
    }

async def get_valid_access_token(db: Session) -> str:
    """
    Retrieves and decrypts the active Google OAuth access token.
    If expired, uses stored refresh token to transparently refresh with Google.
    """
    account = db.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()
    if not account or not account.is_connected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Google account is currently connected. Connect a Google account in Integrations."
        )

    now_utc = datetime.now(timezone.utc)
    is_expired = True
    if account.expires_at:
        exp = account.expires_at if account.expires_at.tzinfo else account.expires_at.replace(tzinfo=timezone.utc)
        # Refresh if within 60 seconds of expiration
        if exp > (now_utc + timedelta(seconds=60)):
            is_expired = False

    if not is_expired and account.encrypted_access_token:
        try:
            return decrypt_credential(account.encrypted_access_token)
        except Exception:
            logger.warning("Decryption error on cached access token; attempting refresh.")

    # Access token expired or unreadable; refresh using refresh token
    if not account.encrypted_refresh_token:
        account.is_connected = False
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authorization expired and no refresh token is stored. Please reconnect your account."
        )

    try:
        refresh_token = decrypt_credential(account.encrypted_refresh_token)
    except Exception as e:
        logger.error(f"Corrupted refresh token: {e}")
        account.is_connected = False
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Stored refresh token is corrupted. Please reconnect your account."
        )

    refresh_payload = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            refresh_resp = await client.post(GOOGLE_TOKEN_URL, data=refresh_payload)
    except httpx.RequestError as e:
        logger.error(f"Network error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to connect to Google OAuth to refresh credentials."
        )

    if refresh_resp.status_code != 200:
        logger.error(f"Token refresh failed ({refresh_resp.status_code}): {refresh_resp.text}")
        account.is_connected = False
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authorization was revoked or expired. Please reconnect your Google account."
        )

    new_tokens = refresh_resp.json()
    new_access_token = new_tokens.get("access_token")
    new_expires_in = new_tokens.get("expires_in", 3600)

    account.encrypted_access_token = encrypt_credential(new_access_token)
    account.expires_at = datetime.now(timezone.utc) + timedelta(seconds=new_expires_in)
    account.last_verified_at = datetime.now(timezone.utc)
    db.commit()

    return new_access_token

async def test_google_connection(db: Session) -> Dict[str, Any]:
    """
    Performs a genuine, low-impact Gmail API request (users.getProfile)
    to verify account access, validate scopes, and report live mailbox metadata.
    """
    token = await get_valid_access_token(db)
    account = db.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()

    start_time = datetime.now(timezone.utc)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                GMAIL_PROFILE_URL,
                headers={"Authorization": f"Bearer {token}"}
            )
    except httpx.RequestError as e:
        logger.error(f"Network error testing Gmail API: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Gmail API. Check your internet connection."
        )

    latency_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

    if resp.status_code == 403:
        # Note: Google's users/me/profile requires gmail.readonly or mail.google.com.
        # Send-only apps with gmail.send cannot read mailbox profiles.
        # Check token validity and granted scopes via Google's tokeninfo service.
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                tokeninfo_resp = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?access_token={token}"
                )
        except Exception as e:
            tokeninfo_resp = None

        if tokeninfo_resp and tokeninfo_resp.status_code == 200:
            tokeninfo = tokeninfo_resp.json()
            granted_scopes_str = tokeninfo.get("scope", "")
            has_send_scope = "gmail.send" in granted_scopes_str or "mail.google.com" in granted_scopes_str
            if has_send_scope:
                if account:
                    account.last_verified_at = datetime.now(timezone.utc)
                    db.commit()
                return {
                    "success": True,
                    "email": account.email if account else "",
                    "messages_total": None,
                    "threads_total": None,
                    "history_id": None,
                    "latency_ms": latency_ms,
                    "verified_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                    "note": "Verified active Gmail send-only credentials."
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Gmail Send scope ('gmail.send') was not granted. Please enable the Gmail API in Google Cloud Console, reconnect your account, and check 'Send email on your behalf'."
                )

        logger.error(f"Gmail API 403 Forbidden: {resp.text}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Gmail API access denied. Ensure the Gmail API is enabled in your Google Cloud project and required scopes were granted."
        )

    if resp.status_code != 200:
        logger.error(f"Gmail API test failed ({resp.status_code}): {resp.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gmail API returned error {resp.status_code} during connection test."
        )

    profile = resp.json()
    profile_email = profile.get("emailAddress", account.email if account else "")

    # Update verification timestamp
    if account:
        account.last_verified_at = datetime.now(timezone.utc)
        db.commit()

    return {
        "success": True,
        "email": profile_email,
        "messages_total": profile.get("messagesTotal"),
        "threads_total": profile.get("threadsTotal"),
        "history_id": profile.get("historyId"),
        "latency_ms": latency_ms,
        "verified_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    }

async def disconnect_google_account(db: Session) -> Dict[str, Any]:
    """
    Safely disconnects Google Account:
    1. Attempts to revoke token at Google (best effort).
    2. Removes stored credentials and updates connection status.
    """
    account = db.query(GoogleAccountModel).filter(GoogleAccountModel.id == "default").first()
    if not account:
        return {"success": True, "message": "No Google account was connected."}

    revocation_attempted = False
    revocation_success = False

    # Try revocation if access token or refresh token is available
    token_to_revoke = None
    if account.encrypted_refresh_token:
        try:
            token_to_revoke = decrypt_credential(account.encrypted_refresh_token)
        except Exception:
            pass
    if not token_to_revoke and account.encrypted_access_token:
        try:
            token_to_revoke = decrypt_credential(account.encrypted_access_token)
        except Exception:
            pass

    if token_to_revoke:
        revocation_attempted = True
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                revoke_resp = await client.post(
                    GOOGLE_REVOKE_URL,
                    params={"token": token_to_revoke},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                revocation_success = (revoke_resp.status_code == 200)
        except Exception as e:
            logger.warning(f"Google token revocation request error: {e}")

    # Remove account record from SQLite
    db.delete(account)
    db.commit()

    logger.info("Google account disconnected and credentials permanently removed from local database.")
    return {
        "success": True,
        "revocation_attempted": revocation_attempted,
        "revocation_success": revocation_success,
        "message": "Google account disconnected successfully."
    }
