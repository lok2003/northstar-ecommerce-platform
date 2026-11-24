from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Mock Payment Service")


class PaymentRequest(BaseModel):
    amount_cents: int = Field(gt=0)
    currency: str = "USD"
    reference: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "payment"}


@app.post("/payments")
async def create_payment(payment: PaymentRequest) -> dict[str, str | int]:
    return {
        "payment_id": f"demo-{payment.reference}",
        "status": "succeeded",
        "amount_cents": payment.amount_cents,
        "currency": payment.currency,
        "message": "Simulated payment only; no money was charged.",
    }
