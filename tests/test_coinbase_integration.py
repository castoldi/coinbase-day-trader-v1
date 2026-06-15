import httpx
import pytest

from trader_app.integrations.coinbase import CoinbaseClient


def test_coinbase_client_uses_sandbox_header():
    client = CoinbaseClient(base_url="https://api.coinbase.com", sandbox=True)
    assert client.headers["X-Sandbox"] == "true"


@pytest.mark.asyncio
async def test_coinbase_smoke_check_parses_status():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"products": [{"product_id": "BTC-USD"}]})

    transport = httpx.MockTransport(handler)
    client = CoinbaseClient(base_url="https://api.coinbase.com", sandbox=True, transport=transport)
    result = await client.smoke_check()
    assert result["ok"] is True
    assert result["product_count"] == 1
