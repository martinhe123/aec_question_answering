import os
import time
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI, OpenAIError

from chat_service import ChatService
from conversation_store import ConversationNotFoundError, ConversationStore
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
conversation_store = ConversationStore()
chat_service = ChatService(client, conversation_store, MODEL_NAME)


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
        return chat_service.respond(message, chat_request.conversation_id)
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found. Start a new conversation.",
        )
    except OpenAIError:
        raise HTTPException(
            status_code=502, detail="Error communicating with OpenAI API."
        )
    except ValueError as error:
        raise HTTPException(status_code=502, detail=str(error))


@app.get("/")
def root():
    return {"status": "ok"}
