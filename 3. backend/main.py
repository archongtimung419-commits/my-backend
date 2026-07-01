import os
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, status
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

# Key will be loaded securely from cloud environment dashboard
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
user_database = {}

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.get("/api/check_user_status")
async def check_status(user_id: str):
    if user_id not in user_database:
        user_database[user_id] = {"payment_verified": True, "tier": "ai"}
    return user_database[user_id]

@app.post("/api/chat")
async def secure_chat_proxy(payload: ChatRequest):
    uid = payload.user_id
    user_msg = payload.message
    
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=500, detail="DeepSeek API Key missing on server config.")

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
                    "messages": [{"role": "user", "content": user_msg}],
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
    print("🚀 Server starting automatically on port 8000...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)