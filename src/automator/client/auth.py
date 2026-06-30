import logging
import time
from dataclasses import dataclass

import httpx

from automator.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    access_token: str
    expires_at: float


class AllureAuth:
    def __init__(self, settings: Settings) -> None:
        self._endpoint = settings.allure_endpoint.rstrip("/")
        self._api_token = settings.allure_api_token
        self._token: TokenInfo | None = None

    def get_token(self, client: httpx.Client) -> str:
        if self._token is None or time.time() >= self._token.expires_at:
            self._refresh(client)
        assert self._token is not None
        return self._token.access_token

    def _refresh(self, client: httpx.Client) -> None:
        response = client.post(
            f"{self._endpoint}/api/uaa/oauth/token",
            data={
                "grant_type": "apitoken",
                "scope": "openid",
                "token": self._api_token,
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        payload = response.json()
        expires_in = int(payload.get("expires_in", 3600))
        # Refresh 5 minutes before expiry.
        self._token = TokenInfo(
            access_token=payload["access_token"],
            expires_at=time.time() + max(expires_in - 300, 60),
        )
        logger.info("Allure JWT refreshed, valid for ~%s seconds", expires_in)
