import logging
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.services.google_oauth import (
    get_oauth_status,
    create_authorization_url,
    handle_oauth_callback,
    test_google_connection,
    disconnect_google_account
)

logger = logging.getLogger("leddro.api.google")
router = APIRouter(prefix="/google", tags=["Google OAuth & Gmail"])

@router.get("/status")
def google_status(db: Session = Depends(get_db)):
    """
    Returns public Google integration status. Never exposes client secrets,
    access tokens, or refresh tokens.
    """
    return get_oauth_status(db)

@router.get("/connect")
def google_connect(db: Session = Depends(get_db)):
    """
    Generates a secure Google OAuth authorization URL with CSRF state and PKCE challenge.
    """
    return create_authorization_url(db)

@router.get("/callback")
async def google_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Handles Google OAuth redirect callback.
    Validates CSRF state, exchanges authorization code for tokens,
    retrieves authenticated email address, and redirects user back to Frontend Integrations page.
    """
    frontend_base = settings.FRONTEND_URL.rstrip("/")
    integrations_url = f"{frontend_base}/integrations"

    # User denied consent or Google returned error
    if error:
        logger.warning(f"Google OAuth callback returned error: {error} ({error_description})")
        err_msg = error_description or error
        return RedirectResponse(
            url=f"{integrations_url}?google_error={quote(err_msg)}",
            status_code=status.HTTP_302_FOUND
        )

    if not code or not state:
        logger.warning("Google OAuth callback missing required code or state parameter")
        return RedirectResponse(
            url=f"{integrations_url}?google_error={quote('Missing authorization code or state from Google')}",
            status_code=status.HTTP_302_FOUND
        )

    try:
        result = await handle_oauth_callback(code=code, state=state, db=db)
        email_str = result.get("email", "")
        return RedirectResponse(
            url=f"{integrations_url}?google_connected=true&email={quote(email_str)}",
            status_code=status.HTTP_302_FOUND
        )
    except HTTPException as exc:
        logger.error(f"OAuth callback HTTP error: {exc.detail}")
        return RedirectResponse(
            url=f"{integrations_url}?google_error={quote(str(exc.detail))}",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as exc:
        logger.error(f"Unexpected error in OAuth callback: {exc}", exc_info=True)
        return RedirectResponse(
            url=f"{integrations_url}?google_error={quote('An unexpected error occurred during Google authentication.')}",
            status_code=status.HTTP_302_FOUND
        )

@router.post("/test-connection")
async def google_test_connection(db: Session = Depends(get_db)):
    """
    Performs a live, low-impact test of the Gmail API using stored credentials.
    """
    return await test_google_connection(db)

@router.post("/disconnect")
async def google_disconnect(db: Session = Depends(get_db)):
    """
    Disconnects the Google account, revokes OAuth access at Google,
    and removes credentials from local database.
    """
    return await disconnect_google_account(db)
