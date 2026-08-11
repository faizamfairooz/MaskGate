from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict

from app.services.masking_service import MaskingService
from app.schemas.masking import MaskingPolicy, MaskingRequest, MaskingResult, MaskingRecommendation

router = APIRouter()
masking_service = MaskingService()


class CreatePolicyRequest(BaseModel):
    name: str
    description: str
    table_name: str
    column_name: str
    strategy: str
    parameters: Optional[dict] = None


class RejectRecommendationRequest(BaseModel):
    reason: Optional[str] = None


@router.get("/strategies")
async def list_strategies() -> Dict[str, str]:
    return masking_service.get_available_strategies()


@router.post("/policies", response_model=MaskingPolicy)
async def create_policy(request: CreatePolicyRequest):
    try:
        return masking_service.create_policy(
            name=request.name,
            description=request.description,
            table_name=request.table_name,
            column_name=request.column_name,
            strategy=request.strategy,
            parameters=request.parameters,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")


@router.get("/policies", response_model=List[MaskingPolicy])
async def get_policies():
    try:
        return masking_service.get_all_policies()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve policies: {str(e)}")


@router.get("/policies/{policy_id}", response_model=MaskingPolicy)
async def get_policy(policy_id: int):
    policy = masking_service.get_policy(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.delete("/policies/{policy_id}")
async def delete_policy(policy_id: int):
    try:
        masking_service.delete_policy(policy_id)
        return {"message": "Policy deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete policy: {str(e)}")


@router.get("/recommendations", response_model=List[MaskingRecommendation])
async def list_recommendations(status: Optional[str] = None, table_name: Optional[str] = None):
    try:
        return masking_service.list_recommendations(status=status, table_name=table_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list recommendations: {str(e)}")


@router.post("/recommendations/{rec_id}/approve", response_model=MaskingPolicy)
async def approve_recommendation(rec_id: int):
    try:
        return masking_service.approve_recommendation(rec_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve recommendation: {str(e)}")


@router.post("/recommendations/{rec_id}/reject", response_model=MaskingRecommendation)
async def reject_recommendation(rec_id: int, body: Optional[RejectRecommendationRequest] = None):
    try:
        return masking_service.reject_recommendation(rec_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject recommendation: {str(e)}")


@router.post("/apply", response_model=MaskingResult)
async def apply_masking(request: MaskingRequest):
    try:
        return masking_service.apply_masking(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply masking: {str(e)}")
