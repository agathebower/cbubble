"""API key authentication dependency."""

import os
import logging
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

log = logging.getLogger("cbubble.auth")

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str = Security(_API_KEY_HEADER)):
    """Dependency: validates X-API-Key header against CBUBBLE_API_KEY env var.

    Raises 403 if key is missing or wrong.
    Raises 500 if the server has not configured an API key at all.
    """
    expected = os.environ.get("CBUBBLE_API_KEY", "")
    if not expected:
        log.error("CBUBBLE_API_KEY is not set — protected endpoints are inaccessible")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: API key not set",
        )
    if not key or key != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
