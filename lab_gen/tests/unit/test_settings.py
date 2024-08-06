import pytest

from lab_gen.settings import settings


@pytest.mark.anyio()
async def test_settings() -> None:
    """
    Test that settings are not empty.

    :return: None
    """
    assert settings.host == "127.0.0.1"
    assert settings.workers_count == 1
