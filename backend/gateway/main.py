import os
from typing import Any
from uuid import UUID

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="E-commerce API Gateway")

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://localhost:8002")
CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", "http://localhost:8003")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8004")


class Credentials(BaseModel):
    username: str
    password: str


class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=99)


async def call_service(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.request(
                method, f"{base_url}{path}", json=payload, headers=headers
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502, detail=f"Service unavailable: {base_url}"
        ) from exc

    if response.is_error:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise HTTPException(status_code=response.status_code, detail=detail)
    if response.status_code == 204:
        return None
    return response.json()


def get_cart_id(value: str | None) -> str:
    if value is None:
        raise HTTPException(status_code=400, detail="X-Cart-Id header required")
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid cart ID") from exc


async def require_user(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    result = await call_service(
        AUTH_SERVICE_URL,
        "/verify",
        method="POST",
        headers={"Authorization": authorization},
    )
    return result["username"]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "gateway"}


@app.post("/api/auth/register")
async def register(credentials: Credentials) -> Any:
    return await call_service(
        AUTH_SERVICE_URL,
        "/register",
        method="POST",
        payload=credentials.model_dump(),
    )


@app.post("/api/auth/login")
async def login(credentials: Credentials) -> Any:
    return await call_service(
        AUTH_SERVICE_URL,
        "/login",
        method="POST",
        payload=credentials.model_dump(),
    )


@app.get("/api/products")
async def products() -> Any:
    return await call_service(CATALOG_SERVICE_URL, "/products")


@app.get("/api/cart")
async def get_cart(x_cart_id: str | None = Header(default=None)) -> Any:
    cart_id = get_cart_id(x_cart_id)
    return await call_service(CART_SERVICE_URL, f"/carts/{cart_id}")


@app.post("/api/cart/items")
async def add_cart_item(
    item: CartItem,
    x_cart_id: str | None = Header(default=None),
) -> Any:
    cart_id = get_cart_id(x_cart_id)
    return await call_service(
        CART_SERVICE_URL,
        f"/carts/{cart_id}/items",
        method="POST",
        payload=item.model_dump(),
    )


@app.put("/api/cart/items/{product_id}")
async def update_cart_item(
    product_id: int,
    item: CartItem,
    x_cart_id: str | None = Header(default=None),
) -> Any:
    if item.product_id != product_id:
        raise HTTPException(status_code=400, detail="Product ID does not match")
    cart_id = get_cart_id(x_cart_id)
    return await call_service(
        CART_SERVICE_URL,
        f"/carts/{cart_id}/items/{product_id}",
        method="PUT",
        payload={"quantity": item.quantity},
    )


@app.delete("/api/cart/items/{product_id}", status_code=204)
async def remove_cart_item(
    product_id: int,
    x_cart_id: str | None = Header(default=None),
) -> None:
    cart_id = get_cart_id(x_cart_id)
    await call_service(
        CART_SERVICE_URL,
        f"/carts/{cart_id}/items/{product_id}",
        method="DELETE",
    )


@app.post("/api/checkout")
async def checkout(
    authorization: str | None = Header(default=None),
    x_cart_id: str | None = Header(default=None),
) -> Any:
    username = await require_user(authorization)
    cart_id = get_cart_id(x_cart_id)
    cart = await call_service(CART_SERVICE_URL, f"/carts/{cart_id}")
    if not cart["items"]:
        raise HTTPException(status_code=400, detail="Your cart is empty")

    catalog = await call_service(CATALOG_SERVICE_URL, "/products")
    products_by_id = {product["id"]: product for product in catalog}
    order_items = []
    for item in cart["items"]:
        product = products_by_id.get(item["product_id"])
        if product is None:
            raise HTTPException(
                status_code=400,
                detail=f"Product {item['product_id']} is no longer available",
            )
        order_items.append(
            {
                "product_id": product["id"],
                "name": product["name"],
                "quantity": item["quantity"],
                "unit_price_cents": product["price_cents"],
            }
        )

    order = await call_service(
        ORDER_SERVICE_URL,
        "/orders",
        method="POST",
        payload={"username": username, "items": order_items},
    )
    await call_service(CART_SERVICE_URL, f"/carts/{cart_id}", method="DELETE")
    return order
