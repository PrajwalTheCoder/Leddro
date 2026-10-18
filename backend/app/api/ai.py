import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from backend.app.ai.service import ai_service
from backend.app.ai.models import (
    AIProviderInfo,
    AISettingsResponse,
    AISettingsUpdate,
    TestConnectionRequest,
    TestConnectionResponse
)
from backend.app.ai.base import (
    AIError,
    AIConfigurationError,
    AIProviderError,
    AIRateLimitError,
    AITimeoutError
)

logger = logging.getLogger("leddro.api.ai")
router = APIRouter(prefix="/ai", tags=["AI Provider & Settings"])

@router.get("/providers", response_model=List[AIProviderInfo])
def get_providers():
    """
    Returns available AI provider names, configuration status, supported models,
    active state, and clear privacy/data transmission notices.
    """
    return ai_service.list_providers()

@router.get("/settings", response_model=AISettingsResponse)
def get_ai_settings():
    """
    Returns non-secret AI provider configuration settings and developer profile info.
    Secret API keys are strictly masked and never returned to the frontend.
    """
    return ai_service.get_settings()

@router.put("/settings", response_model=AISettingsResponse)
def update_ai_settings(payload: AISettingsUpdate):
    """
    Updates non-secret AI settings such as active provider, selected models,
    safety timeouts, token limits, and developer profile fields.
    """
    try:
        updated = ai_service.update_settings(payload)
        return updated
    except AIConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update AI settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}"
        )

@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_ai_connection(payload: TestConnectionRequest = TestConnectionRequest()):
    """
    Tests the connection to an explicitly selected AI provider (or active provider).
    Validates API key and connectivity without generating an email or transmitting prospect data.
    """
    try:
        provider = ai_service.get_provider(payload.provider_id)
        result = await provider.test_connection()
        return TestConnectionResponse(**result)
    except AIConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AIRateLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except AITimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(e)
        )
    except AIProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error testing AI connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection test failed: {str(e)}"
        )
