import os
import time
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI, OpenAIError

from prompts import CLARIFICATION_RESPONSE, OFF_TOPIC_RESPONSE, SYSTEM_PROMPT
from resources import RESOURCE_MAP
from schemas import AECCategory, ChatRequest, ChatResponse, ModelResult


# OpenAI API key: Render environment variable first, local file as fallback.
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    try:
        with open("secrets.txt", "r") as file:
            api_key = file.read().strip()
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


# Simple in-memory rate limiting for this small, single-instance app.
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60
request_log: dict[str, list[float]] = defaultdict(list)


def is_rate_limited(client_ip: str) -> bool:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS

    timestamps = request_log[client_ip]
    timestamps[:] = [timestamp for timestamp in timestamps if timestamp > window_start]

    if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        return True

    timestamps.append(now)
    return False


app = FastAPI()

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


@app.post("/chat", response_model=ChatResponse)
def chat(chat_request: ChatRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(client_ip):
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Limit is {RATE_LIMIT_MAX_REQUESTS} per minute.",
        )

    message = chat_request.message.strip() if chat_request.message else ""
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    word_count = len(message.split())
    if word_count > MAX_WORDS:
        raise HTTPException(
            status_code=400,
            detail=f"Message is too long ({word_count} words). Limit is {MAX_WORDS} words.",
        )

    try:
        completion = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            response_format=ModelResult,
        )
    except OpenAIError:
        raise HTTPException(
            status_code=502, detail="Error communicating with OpenAI API."
        )

    result = completion.choices[0].message.parsed
    if result is None:
        raise HTTPException(
            status_code=502, detail="OpenAI returned an unusable response."
        )

    if result.category == AECCategory.NOT_AEC:
        return ChatResponse(
            response=OFF_TOPIC_RESPONSE,
            category=AECCategory.NOT_AEC,
            resources=[],
        )

    if result.category == AECCategory.NEEDS_CLARIFICATION:
        return ChatResponse(
            response=CLARIFICATION_RESPONSE,
            category=AECCategory.NEEDS_CLARIFICATION,
            resources=[],
        )

    answer = result.answer.strip()
    if not answer:
        raise HTTPException(
            status_code=502, detail="OpenAI returned an empty response."
        )

    return ChatResponse(
        response=answer,
        category=result.category,
        resources=list(RESOURCE_MAP[result.category]),
    )


@app.get("/")
def root():
    return {"status": "ok"}
