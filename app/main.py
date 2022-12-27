from typing import Dict, List

from fastapi import APIRouter, Depends, FastAPI

from .security import authenticate_api_key

app = FastAPI()

api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(authenticate_api_key)])


@api_router.get("/")
def api_root() -> Dict:
    return {}


@api_router.post("/transcripts")
def create_transcript() -> None:
    return None


@api_router.get("/transcripts")
def get_transcripts() -> List:
    return []


@api_router.get("/transcripts/{id}")
def get_transcript() -> None:
    return None


@api_router.delete("/transcripts/{id}")
def delete_transcript() -> None:
    return None


app.include_router(api_router)
