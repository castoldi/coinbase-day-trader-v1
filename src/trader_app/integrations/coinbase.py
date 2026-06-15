from typing import Any

import httpx


class CoinbaseClient:
    def __init__(
        self,
        base_url: str,
        sandbox: bool,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"Accept": "application/json"}
        if sandbox:
            self.headers["X-Sandbox"] = "true"
        self.transport = transport

    async def smoke_check(self) -> dict[str, Any]:
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            transport=self.transport,
            timeout=10,
        ) as client:
            response = await client.get("/api/v3/brokerage/products")
            response.raise_for_status()
            payload = response.json()
            products = payload.get("products", [])
            return {"ok": True, "product_count": len(products)}
