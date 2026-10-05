import asyncio
import base64
import json

import httpx
import pytest

from property_cutouts.infrai_images import InfraiError, InfraiImageClient


@pytest.mark.asyncio
async def test_background_remove_sends_json_image() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["content-type"] == "application/json"
        assert json.loads(request.content) == {
            "image": {"base64": base64.b64encode(b"photo").decode("ascii")},
            "format": "png",
        }
        return httpx.Response(200, json={"ok": True, "data": {}, "metadata": {}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = InfraiImageClient("test-key", client=http_client)
        await client.remove_background(
            image=b"photo", filename="kitchen.jpeg", output_format="png", idempotency_key="test"
        )


@pytest.mark.asyncio
async def test_business_rejection_is_decoded_before_http_status() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "ok": False,
                "data": None,
                "error": {"code": "BAD_PHOTO", "message": "Choose another photo"},
                "metadata": None,
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = InfraiImageClient("test-key", client=http_client)
        with pytest.raises(InfraiError) as caught:
            await client.remove_background(
                image=b"photo",
                filename="kitchen.jpg",
                output_format="png",
                idempotency_key="listing-cutout:maple-12:kitchen:png",
            )
    assert caught.value.status_code == 400
    assert caught.value.code == "BAD_PHOTO"


@pytest.mark.asyncio
async def test_rate_limit_honors_retry_after() -> None:
    calls = 0
    delays: list[float] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "2"},
                json={"ok": False, "data": None, "error": {}, "metadata": None},
            )
        return httpx.Response(
            200,
            json={"ok": True, "data": {"id": "cutout-7"}, "error": None, "metadata": {}},
        )

    async def record_sleep(delay: float) -> None:
        delays.append(delay)
        await asyncio.sleep(0)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = InfraiImageClient(client=http_client, api_key="test-key", sleep=record_sleep)
        result = await client.remove_background(
            image=b"photo",
            filename="kitchen.jpg",
            output_format="png",
            idempotency_key="listing-cutout:maple-12:kitchen:png",
        )
    assert calls == 2
    assert delays == [2.0]
    assert result["data"] == {"id": "cutout-7"}
