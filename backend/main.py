import os
import time
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI, OpenAIError

# ---------------------------------------------------------------------------
# OpenAI API key
# Primary: Render environment variable OPENAI_API_KEY
# Fallback: local secrets.txt (for local development only, never committed)
# ---------------------------------------------------------------------------
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    try:
        with open("secrets.txt", "r") as f:
            api_key = f.read().strip()
    except FileNotFoundError:
        api_key = None

if not api_key:
    raise RuntimeError(
        "No OpenAI API key found. Set the OPENAI_API_KEY environment variable "
        "or create a local secrets.txt file."
    )

client = OpenAI(api_key=api_key)

MODEL_NAME = "gpt-4o-mini"
MAX_WORDS = 200

# ---------------------------------------------------------------------------
# Simple in-memory rate limiting
# Keyed by client IP. Not persisted across restarts and not shared across
# multiple server instances, which is fine for this small, single-instance app.
# ---------------------------------------------------------------------------
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60
request_log: dict[str, list[float]] = defaultdict(list)


def is_rate_limited(client_ip: str) -> bool:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS

    timestamps = request_log[client_ip]
    # Drop timestamps outside the current window
    timestamps[:] = [t for t in timestamps if t > window_start]

    if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        return True

    timestamps.append(now)
    return False

SYSTEM_PROMPT = (
    "You are a chatbot that answers questions about AEC "
    "(architecture, engineering, and construction) topics. "
    "If the user's question is not related to AEC, briefly tell them "
    "this chatbot is for work-related AEC questions only, and do not "
    "answer the off-topic question. If the question is AEC-related, "
    "answer professionally and clearly."
)

app = FastAPI()

# ---------------------------------------------------------------------------
# CORS configuration
# Allows the deployed GitHub Pages frontend, plus localhost for local testing.
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "https://martinhe123.github.io",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
def chat(chat_request: ChatRequest, request: Request):
    # 1. Rate limit
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(client_ip):
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Limit is {RATE_LIMIT_MAX_REQUESTS} per minute.",
        )

    message = chat_request.message.strip() if chat_request.message else ""

    # 2. Empty input
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # 3. Message longer than 200 words
    word_count = len(message.split())
    if word_count > MAX_WORDS:
        raise HTTPException(
            status_code=400,
            detail=f"Message is too long ({word_count} words). Limit is {MAX_WORDS} words.",
        )

    # 4. Call OpenAI, handle API errors
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
        )
    except OpenAIError:
        raise HTTPException(
            status_code=502, detail="Error communicating with OpenAI API."
        )

    answer = completion.choices[0].message.content
    return ChatResponse(response=answer)


@app.get("/")
def root():
    return {"status": "ok"}
