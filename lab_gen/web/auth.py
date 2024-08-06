from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from lab_gen.settings import settings


api_key = APIKeyHeader(name="Authorization", auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key)) -> bool:
    """
        A function that retrieves an API key from the API key header.

    Parameters:
        api_key_header (str): The API key header value.

    Returns:
        bool: True if the API key is valid, False otherwise.

    Raises:
        HTTPException: If the API key cannot be validated.
    """
    if api_key_header == settings.api_key:
        return True
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail="Could not validate API KEY",
    )
