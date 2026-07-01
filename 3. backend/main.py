import os
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

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

class ChatRequest(BaseModel):
    messages: List[dict]
    user_id: str
    lang: Optional[str] = None
    name: Optional[str] = None
    age: Optional[str] = None
    day_title: Optional[str] = None

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

    # 🧠 Strict & Exclusive Earning + Ebook Knowledge Base
    system_instruction = (
        "You are Dr. Zen, an AI assistant dedicated strictly and exclusively to promoting Arsong's digital products and ecosystem.\n"
        "Strict Instructions:\n"
        "1. Absolute Core Focus: You only answer queries regarding two things: the 'Student Pocket Money Program' and Arsong's official 'Brain Rewire Protocol Ebook'. Do NOT give generic self-help advice, general psychology definitions, or recommend external books.\n"
        "2. Ebook Product Details: If the user asks about an 'ebook', 'book', 'reading material', or 'digital product', you must tell them: 'Aapko kisi aur book ki zarurat nahi hai! Arsong ki official Brain Rewire Protocol Ebook hi ultimate guide hai. Isme 7-Day protocols ka practical aur step-by-step masterclass framework diya gaya hai jo aapke focus ko lock kar dega.'\n"
        "3. Earning Program Details: We are launching a micro-tasks website very soon! Students can do simple daily focus-based tasks on the site and easily earn up to ₹2500 a month as pocket money.\n"
        "4. Off-Topic Refusal: If a user asks about anything else, politely say: 'Main yahan sirf Student Pocket Money Program aur hamari official Ebook ke baare me guide karne ke liye hoon.'\n"
        "5. Style: Keep your answers very short, direct, and clear. Use a friendly mix of Hindi/Hinglish or English."
    )

    compiled_messages = [{"role": "system", "content": system_instruction}] + payload.messages

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": compiled_messages,
                    "temperature": 0.4
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