from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class OrderRequest(BaseModel):
    product_id: int
    quantity: int

def calculate_total(quantity: int) -> float:
    if quantity < 0:
        raise ValueError("Invalid quantity: quantity cannot be negative")
    return quantity * 19.99

@app.post("/orders")
def create_order(payload: OrderRequest):
    total = calculate_total(payload.quantity)
    return {"status": "success", "total": total}
