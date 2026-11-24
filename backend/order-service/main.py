import os
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Order Service")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8005")
orders: list[dict[str, object]] = []


class OrderItem(BaseModel):
    product_id: int
    name: str
    quantity: int = Field(gt=0, le=99)
    unit_price_cents: int = Field(gt=0)


class OrderRequest(BaseModel):
    username: str
    items: list[OrderItem] = Field(min_length=1)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "orders"}


@app.post("/orders")
async def create_order(order: OrderRequest) -> dict[str, object]:
    order_id = str(uuid4())
    items = [item.model_dump() for item in order.items]
    total_cents = sum(
        item["quantity"] * item["unit_price_cents"] for item in items
    )

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{PAYMENT_SERVICE_URL}/payments",
                json={
                    "amount_cents": total_cents,
                    "currency": "USD",
                    "reference": order_id,
                },
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Payment service unavailable") from exc

    if response.is_error:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise HTTPException(status_code=response.status_code, detail=detail)

    result: dict[str, object] = {
        "order_id": order_id,
        "username": order.username,
        "items": items,
        "total_cents": total_cents,
        "status": "paid",
        "payment": response.json(),
    }
    orders.append(result)
    return result
