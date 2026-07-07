import os
from fastapi import FastAPI, Request, HTTPException
from transformers import pipeline
from huggingface_hub import login
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("MY_API_KEY")
login(token=os.getenv("HUGGINGFACE_TOKEN"))

chatbot = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.3")

app = FastAPI()


def build_prompt(user_message, system_prompt=None, history=None):
    parts = []
    if history:
        for msg in history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                parts.append(f"[INST] {content} [/INST]")
            elif role == "assistant":
                parts.append(f"{content}</s>")
            else:
                parts.append(f"{content}")

    if system_prompt:
        full_message = f"{system_prompt}\n\n{user_message}"
    else:
        full_message = user_message

    parts.append(f"[INST] {full_message} [/INST]")
    return "".join(parts)


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message")
    if not user_message:
        raise HTTPException(status_code=400, detail="Message required")

    system_prompt = data.get("system_prompt")
    history = data.get("history", [])

    prompt = build_prompt(user_message, system_prompt, history)
    response = chatbot(prompt, max_new_tokens=600, do_sample=True, temperature=0.7)
    generated = response[0]["generated_text"]
    reply = generated[len(prompt):].strip()
    return {"response": reply}
