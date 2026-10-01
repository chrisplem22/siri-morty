import os
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

class VoiceQuery(BaseModel):
    query: str

def trigger_background_batch():
    # Placeholder where your Escapia batch runner fires
    print("Background job started!")

@app.get("/")
def health_check():
    return {"status": "Morty webhook is online, sir."}

@app.post("/webhook")
async def handle_siri(payload: VoiceQuery, background_tasks: BackgroundTasks):
    user_prompt = payload.query.strip()
    prompt_lower = user_prompt.lower()

    # Route 1: Batch / Escapia automations
    if any(keyword in prompt_lower for keyword in ["batch", "escapia", "sync", "run report"]):
        background_tasks.add_task(trigger_background_batch)
        return {
            "response": "On it, sir. I started the batch runner in the background and will update your sheets."
        }

    # Route 2: Gemini Brain fallback (if API key is present)
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        ai_resp = model.generate_content(
            f"Answer concisely in one or two sentences suitable for voice output: {user_prompt}"
        )
        return {"response": ai_resp.text.strip()}

    # Default reply for connection verification
    return {"response": f"Received loud and clear, sir. You said: {user_prompt}"}
