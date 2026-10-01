import os
import json
import asyncio
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import google.generativeai as genai
from openai import AsyncOpenAI

app = FastAPI()

# Clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-1.5-pro")

class VoiceQuery(BaseModel):
    query: str

def execute_background_job(job_type: str, details: str):
    """Placeholder for long-running scripts (Escapia, Playwright scrapers, code runs)."""
    print(f"[BACKGROUND WORKER] Executing {job_type} with details: {details}")

async def parse_intent_and_device_actions(prompt: str) -> dict:
    """Uses fast GPT model to classify requests and extract phone controls."""
    system_prompt = (
        "You are Morty, a hyper-competent AI assistant for an executive. "
        "Analyze the user's spoken command and return a valid JSON object with three keys:\n"
        "1. 'action': One of ['none', 'low_power_mode', 'timer', 'dnd', 'reminder', 'automation_task']\n"
        "2. 'value': Extra data needed for the action (e.g., number of minutes for timer, reminder text, or task name). Return empty string if none.\n"
        "3. 'is_complex_query': boolean (true if the user is asking for analysis, strategy, coding, or long-form reasoning; false if it is a simple phone command or quick question).\n"
        "4. 'fast_response': A short 1-sentence spoken voice response addressing the user as 'sir'."
    )
    
    try:
        completion = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        return {
            "action": "none",
            "value": "",
            "is_complex_query": True,
            "fast_response": f"Encountered a gateway issue, sir: {str(e)}"
        }

async def generate_gemini_response(prompt: str) -> str:
    """Uses Gemini Pro for deep reasoning, coding, and strategic analysis."""
    try:
        response = await asyncio.to_thread(
            gemini_model.generate_content,
            f"You are Morty, a sharp executive AI assistant. Address the user as 'sir'. "
            f"Respond concisely in 1 to 2 spoken sentences suitable for voice readout: {prompt}"
        )
        return response.text.strip()
    except Exception as e:
        return f"Gemini calculation error, sir: {str(e)}"

@app.get("/")
def health_check():
    return {"status": "Morty Dual-Brain Engine Online"}

@app.post("/webhook")
async def handle_siri(payload: VoiceQuery, background_tasks: BackgroundTasks):
    user_prompt = payload.query.strip()
    
    # Step 1: Run intent detection and action extraction
    intent = await parse_intent_and_device_actions(user_prompt)
    action = intent.get("action", "none")
    value = str(intent.get("value", ""))
    
    # Step 2: Handle long-running automation tasks in background
    if action == "automation_task" or any(kw in user_prompt.lower() for kw in ["batch", "escapia", "sync sheets", "run report"]):
        background_tasks.add_task(execute_background_job, "batch_runner", user_prompt)
        return {
            "response": "Starting the automation job in the background now, sir. I'll update your sheets.",
            "action": "none",
            "value": ""
        }

    # Step 3: Handle complex questions via Gemini Pro
    if intent.get("is_complex_query") and action == "none":
        gemini_reply = await generate_gemini_response(user_prompt)
        return {
            "response": gemini_reply,
            "action": "none",
            "value": ""
        }

    # Step 4: Return direct device actions with voice response
    return {
        "response": intent.get("fast_response", "Right away, sir."),
        "action": action,
        "value": value
    }
