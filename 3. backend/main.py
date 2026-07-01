import os
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

user_database = {}

# 🚀 Upgraded schema to support full frontend state logs
class ChatRequest(BaseModel):
    messages: list
    user_id: str
    lang: str | None = None
    name: str | None = None
    age: str | None = None
    day_title: str | None = None

class VerifyPaymentRequest(BaseModel):
    payment_id: str
    order_id: str

@app.get("/api/check_user_status")
async def check_status(user_id: str):
    if user_id not in user_database:
        user_database[user_id] = {"payment_verified": True, "tier": "ai"}
    return user_database[user_id]

@app.post("/api/verify_payment")
async def verify_payment_and_get_user(payload: VerifyPaymentRequest):
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=500, detail="Razorpay keys are missing on the server configuration.")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.razorpay.com/v1/payments/{payload.payment_id}",
                auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
            )
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch data from Razorpay.")
            payment_data = response.json()
            return {"status": "success", "email": payment_data.get("email")}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def secure_chat_proxy(payload: ChatRequest):
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=500, detail="DeepSeek API Key missing on server config.")

    async with httpx.AsyncClient() as client:
        try:
            # Forward the exact contextual history array straight to DeepSeek
            response = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": payload.messages,
                    "temperature": 0.7
                },
                timeout=40.0
            )
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"DeepSeek Error: {response.text}")
            ai_data = response.json()
            return {"reply": ai_data["choices"][0]["message"]["content"]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)