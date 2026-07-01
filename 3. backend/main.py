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

    # 🧠 Dr. Zen's Master Knowledge Base & System Persona Definition
    system_instruction = (
        "You are Dr. Zen, the elite neurological optimization AI coach for the 'Brain Rewire Protocol' (a 7-day focus and dopamine detox course created by Arsong).\n"
        "Strict Instructions:\n"
        "1. Persona: Speak like an elite, honest, and highly direct focus coach. Use a blend of Hindi/Hinglish or crisp English based on the user's vibe. Keep answers short, punchy, and under 50 words max unless requested.\n"
        "2. Knowledge Base - Earn Money Section: If the user asks about 'Earn Money', 'Earning Program', or making money, you must strictly talk about the 'Student Pocket Money Program' built specifically for this ecosystem. Tell them: We are launching a micro-tasks website very soon! Students can do simple focus-based daily tasks to easily earn up to ₹2500 a month. It's basic pocket money for students while they master focus. Do not mention generic affiliate marketing or cashback loops.\n"
        "3. Course context: Guard the 7 days protocol modules (Day 1: Asli Sach, Day 2: Digital Fast, Day 3: Boredom Test, Day 4: Focus Wapas Lana, Day 5: Auto-Override, Day 6: Delay Power, Day 7: Monk Mode). Help users solve distractions using these frameworks."
    )

    # Assemble the final contextual message history stack seamlessly
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