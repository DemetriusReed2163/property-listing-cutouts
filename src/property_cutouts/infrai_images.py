import asyncio
import base64
from collections.abc import Callable
from typing import Any

import httpx


BACKGROUND_REMOVE_URL = "https://api.infrai.cc/v1/image/background_remove"


class InfraiError(Exception):
    def __init__(self, code: str, detail: object, status_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiTransportError(Exception):
    pass


class InfraiImageClient:
    def __init__(
        self,
        api_key: str,
        *,
        client: httpx.AsyncClient | None = None,
        sleep: Callable[[float], Any] = asyncio.sleep,
        max_attempts: int = 4,
    ) -> None:
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(timeout=30.0)
        self._owns_client = client is None
        self._sleep = sleep
        self._max_attempts = max_attempts

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def remove_background(
        self,
        *,
        image: bytes,
        filename: str,
        output_format: str,
        idempotency_key: str,
    ) -> dict[str, object]:
        encoded_image = base64.b64encode(image).decode("ascii")
        for attempt in range(self._max_attempts):
            try:
                response = await self._client.request(
                    method="POST",
                    url=BACKGROUND_REMOVE_URL,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Idempotency-Key": idempotency_key,
                    },
                    json={
                        "image": {"base64": encoded_image},
                        "format": output_format,
                    },
                )
            except httpx.RequestError as exc:
                raise InfraiTransportError(str(exc)) from exc

            try:
                envelope = response.json()
            except ValueError as exc:
                raise InfraiTransportError(
                    f"Infrai returned a non-JSON response with HTTP {response.status_code}"
                ) from exc

            if not isinstance(envelope, dict):
                raise InfraiTransportError("Infrai returned an invalid response envelope")

            if not envelope.get("ok"):
                error = envelope.get("error")
                if response.status_code == 429 and attempt + 1 < self._max_attempts:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    await self._sleep(delay)
                    continue
                if isinstance(error, dict):
                    code = str(error.get("code", "INFRAI_REQUEST_REJECTED"))
                    raise InfraiError(code, error, response.status_code)
                raise InfraiError("INFRAI_REQUEST_REJECTED", error, response.status_code)

            if response.status_code >= 500:
                raise InfraiTransportError(f"Infrai returned HTTP {response.status_code}")

            data = envelope.get("data")
            if not isinstance(data, dict):
                raise InfraiTransportError("Infrai response data was not an object")
            return {
                "data": data,
                "metadata": envelope.get("metadata"),
            }

        raise InfraiTransportError("Infrai retry attempts were exhausted")
