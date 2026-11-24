from fastapi import FastAPI

app = FastAPI(title="Product Catalog Service")

products = [
    {"id": 1, "name": "Everyday Runner", "category": "Footwear", "description": "Lightweight comfort for your daily miles.", "price_cents": 8900, "icon": "👟", "color": "#e6eee5", "badge": "BEST SELLER"},
    {"id": 2, "name": "Trail Shell Jacket", "category": "Clothing", "description": "A packable layer for unpredictable weather.", "price_cents": 12400, "icon": "🧥", "color": "#e8e8f0", "badge": "NEW"},
    {"id": 3, "name": "Daybreak Backpack", "category": "Accessories", "description": "Room for the essentials, wherever the day goes.", "price_cents": 6800, "icon": "🎒", "color": "#f1e9db", "badge": ""},
    {"id": 4, "name": "Summit Bottle", "category": "Accessories", "description": "Keep your water cold on the move.", "price_cents": 2800, "icon": "🧴", "color": "#e0edf0", "badge": ""},
    {"id": 5, "name": "Field Watch", "category": "Accessories", "description": "A simple, durable companion for every route.", "price_cents": 15600, "icon": "⌚", "color": "#eee5dc", "badge": "POPULAR"},
    {"id": 6, "name": "Studio Headphones", "category": "Gear", "description": "Focus mode for commutes and quiet mornings.", "price_cents": 9900, "icon": "🎧", "color": "#e9e7f0", "badge": ""},
]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "catalog"}


@app.get("/products")
async def get_products() -> list[dict[str, str | int]]:
    return products
