from fastapi import APIRouter
from typing import List

router = APIRouter()

@router.get("/")
async def list_tournaments():
    """List tournaments - placeholder for Phase 4"""
    return {"message": "Tournament endpoints - coming in Phase 4"}

@router.post("/")
async def create_tournament():
    """Create tournament - placeholder for Phase 4"""
    return {"message": "Tournament creation - coming in Phase 4"}