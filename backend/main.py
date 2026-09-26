import os
import time
from collections import defaultdict
from enum import Enum

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

SYSTEM_PROMPT = """
You classify and answer questions about architecture, engineering, construction,
infrastructure, planning, and the built environment.

Choose exactly one category based on the user's primary intent:
- not_aec: unrelated to AEC or the built environment.
- codes: codes, accessibility, zoning, fire codes, occupancy, egress, permits,
  or regulatory compliance.
- safety: construction hazards, PPE, fall protection, excavation safety, or
  safe work practices.
- architecture: spatial design, programming, architectural history, layouts,
  aesthetics, or architectural practice.
- structures: loads, foundations, beams, columns, structural systems, wind,
  earthquakes, or structural analysis.
- energy: building energy use, HVAC efficiency, envelope performance,
  insulation, energy modeling, or operational energy.
- building_systems: mechanical, electrical, plumbing, fire protection,
  lighting, controls, or vertical transportation.
- construction: cost, scheduling, estimating, procurement, contracts, project
  delivery, sequencing, or construction management.
- materials: concrete, steel, wood, masonry, assemblies, durability, material
  selection, or construction methods.
- sustainability: embodied carbon, green building, resilience, adaptive reuse,
  water conservation, or environmental performance.
- general_aec: a valid AEC question that does not clearly fit another category.

Precedence rules:
1. If the main question is what is legally required, choose codes.
2. If the main question concerns an immediate worker hazard, choose safety.
3. For a mixed question, choose only the category that best matches its main
   intent.
4. If the question is not AEC-related, choose not_aec and return an empty
   answer.
5. Otherwise, answer professionally and clearly. Do not include website links
   in the answer; the application supplies related resources separately.
""".strip()

OFF_TOPIC_RESPONSE = (
    "This chatbot is limited to architecture, engineering, and construction "
    "questions."
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


class AECCategory(str, Enum):
    NOT_AEC = "not_aec"
    CODES = "codes"
    SAFETY = "safety"
    ARCHITECTURE = "architecture"
    STRUCTURES = "structures"
    ENERGY = "energy"
    BUILDING_SYSTEMS = "building_systems"
    CONSTRUCTION = "construction"
    MATERIALS = "materials"
    SUSTAINABILITY = "sustainability"
    GENERAL_AEC = "general_aec"


class ModelResult(BaseModel):
    category: AECCategory
    answer: str


class ResourceLink(BaseModel):
    title: str
    url: str


class ChatResponse(BaseModel):
    response: str
    category: AECCategory
    resources: list[ResourceLink]


RESOURCE_MAP: dict[AECCategory, tuple[ResourceLink, ...]] = {
    AECCategory.CODES: (
        ResourceLink(title="ICC Digital Codes", url="https://codes.iccsafe.org/"),
        ResourceLink(
            title="NFPA Codes and Standards",
            url="https://www.nfpa.org/codes-and-standards",
        ),
        ResourceLink(
            title="ADA Accessibility Standards",
            url="https://www.access-board.gov/ada/",
        ),
    ),
    AECCategory.SAFETY: (
        ResourceLink(
            title="OSHA Construction",
            url="https://www.osha.gov/construction",
        ),
        ResourceLink(
            title="NIOSH Construction",
            url="https://www.cdc.gov/niosh/construction/",
        ),
        ResourceLink(title="CPWR", url="https://www.cpwr.com/"),
    ),
    AECCategory.ARCHITECTURE: (
        ResourceLink(
            title="AIA Resource Center",
            url="https://www.aia.org/resource-center",
        ),
        ResourceLink(
            title="Whole Building Design Guide",
            url="https://www.wbdg.org/",
        ),
        ResourceLink(
            title="GSA Design and Construction",
            url="https://www.gsa.gov/real-estate/design-and-construction",
        ),
    ),
    AECCategory.STRUCTURES: (
        ResourceLink(
            title="ASCE Codes and Standards",
            url="https://www.asce.org/publications-and-news/codes-and-standards",
        ),
        ResourceLink(
            title="NIST Buildings and Construction",
            url="https://www.nist.gov/buildings-and-construction",
        ),
        ResourceLink(
            title="FEMA Building Science",
            url="https://www.fema.gov/emergency-managers/risk-management/building-science",
        ),
    ),
    AECCategory.ENERGY: (
        ResourceLink(
            title="DOE Buildings Energy Efficiency",
            url="https://www.energy.gov/topics/buildings-energy-efficiency",
        ),
        ResourceLink(
            title="ENERGY STAR Buildings",
            url="https://www.energystar.gov/buildings",
        ),
        ResourceLink(
            title="NREL Buildings Research",
            url="https://www.nrel.gov/buildings/",
        ),
    ),
    AECCategory.BUILDING_SYSTEMS: (
        ResourceLink(
            title="ASHRAE Technical Resources",
            url="https://www.ashrae.org/technical-resources",
        ),
        ResourceLink(
            title="DOE Buildings Energy Efficiency",
            url="https://www.energy.gov/topics/buildings-energy-efficiency",
        ),
        ResourceLink(
            title="NFPA Codes and Standards",
            url="https://www.nfpa.org/codes-and-standards",
        ),
    ),
    AECCategory.CONSTRUCTION: (
        ResourceLink(
            title="Whole Building Design Guide",
            url="https://www.wbdg.org/",
        ),
        ResourceLink(
            title="Construction Management Association of America",
            url="https://www.cmaanet.org/",
        ),
        ResourceLink(
            title="Construction Specifications Institute",
            url="https://www.csiresources.org/",
        ),
    ),
    AECCategory.MATERIALS: (
        ResourceLink(
            title="NIST Buildings and Construction",
            url="https://www.nist.gov/buildings-and-construction",
        ),
        ResourceLink(
            title="USDA Forest Products Laboratory",
            url="https://www.fpl.fs.usda.gov/",
        ),
        ResourceLink(
            title="American Concrete Institute",
            url="https://www.concrete.org/",
        ),
    ),
    AECCategory.SUSTAINABILITY: (
        ResourceLink(
            title="EPA Green Building",
            url="https://www.epa.gov/smartgrowth/green-building",
        ),
        ResourceLink(
            title="U.S. Green Building Council",
            url="https://www.usgbc.org/",
        ),
        ResourceLink(
            title="DOE Buildings Energy Efficiency",
            url="https://www.energy.gov/topics/buildings-energy-efficiency",
        ),
    ),
    AECCategory.GENERAL_AEC: (
        ResourceLink(
            title="Whole Building Design Guide",
            url="https://www.wbdg.org/",
        ),
        ResourceLink(
            title="AIA Resource Center",
            url="https://www.aia.org/resource-center",
        ),
        ResourceLink(
            title="ASCE Codes and Standards",
            url="https://www.asce.org/publications-and-news/codes-and-standards",
        ),
    ),
}


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

    # 4. Classify and answer in one structured OpenAI call
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
