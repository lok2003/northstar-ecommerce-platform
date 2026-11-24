from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

app = FastAPI(title="Shopping Cart Service")
carts: dict[str, dict[int, int]] = {}


class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=99)


class QuantityUpdate(BaseModel):
    quantity: int = Field(gt=0, le=99)


def cart_response(cart_id: str) -> dict[str, list[dict[str, int]]]:
    items = carts.get(cart_id, {})
    return {
        "items": [
            {"product_id": product_id, "quantity": quantity}
            for product_id, quantity in sorted(items.items())
        ]
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "cart"}


@app.get("/carts/{cart_id}")
async def get_cart(cart_id: str) -> dict[str, list[dict[str, int]]]:
    return cart_response(cart_id)


@app.post("/carts/{cart_id}/items")
async def add_item(cart_id: str, item: CartItem) -> dict[str, list[dict[str, int]]]:
    cart = carts.setdefault(cart_id, {})
    quantity = cart.get(item.product_id, 0) + item.quantity
    if quantity > 99:
        raise HTTPException(status_code=422, detail="Maximum quantity is 99")
    cart[item.product_id] = quantity
    return cart_response(cart_id)


@app.put("/carts/{cart_id}/items/{product_id}")
async def update_item(
    cart_id: str,
    product_id: int,
    update: QuantityUpdate,
) -> dict[str, list[dict[str, int]]]:
    cart = carts.get(cart_id)
    if cart is None or product_id not in cart:
        raise HTTPException(status_code=404, detail="Cart item not found")
    cart[product_id] = update.quantity
    return cart_response(cart_id)


@app.delete("/carts/{cart_id}/items/{product_id}", status_code=204)
async def remove_item(cart_id: str, product_id: int) -> Response:
    cart = carts.get(cart_id)
    if cart is not None:
        cart.pop(product_id, None)
    return Response(status_code=204)


@app.delete("/carts/{cart_id}", status_code=204)
async def clear_cart(cart_id: str) -> Response:
    carts.pop(cart_id, None)
    return Response(status_code=204)
