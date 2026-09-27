from enum import Enum

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class AECCategory(str, Enum):
    NOT_AEC = "not_aec"
    NEEDS_CLARIFICATION = "needs_clarification"
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
