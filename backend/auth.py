"""Unkey API key verification dependency."""
import os

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer()


async def require_api_key(
    credentials: HTTPAuthorizationCredentials = Security(bearer),
) -> str:
    # TODO: replace stub with real Unkey verification
    # from unkey import Unkey
    # result = await Unkey(os.environ["UNKEY_ROOT_KEY"]).keys.verify(
    #     key=credentials.credentials, api_id=os.environ["UNKEY_API_ID"]
    # )
    # if not result.valid:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if credentials.credentials != os.environ.get("DEV_API_KEY", "dev"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return credentials.credentials
