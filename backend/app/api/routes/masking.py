from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

from app.services.masking_service import MaskingService
from app.schemas.masking import (
    MaskingPolicy,
    MaskingPolicyUpdate,
    MaskingRequest,
    MaskingResult,
    MaskingRecommendation,
)

router = APIRouter()
masking_service = MaskingService()


class AnalyzeAndQueueRequest(BaseModel):
    model_config = {"populate_by_name": True}
    schema_name: str = Field(default="public", alias="schema")
    table_name: Optional[str] = None


class RejectRecommendationRequest(BaseModel):
    reason: Optional[str] = None


@router.get("/strategies")
async def list_strategies() -> Dict[str, str]:
    return masking_service.get_available_strategies()


@router.get("/policies", response_model=List[MaskingPolicy])
async def get_policies(status: Optional[str] = Query(default="ACTIVE")):
    """Retrieve all active masking policies."""
    try:
        return masking_service.get_all_policies(status=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve policies: {str(e)}")


@router.post("/policies", response_model=MaskingPolicy, status_code=201)
async def create_policy(policy: MaskingPolicy):
    """Create or update a masking policy with table and column validation."""
    try:
        return masking_service.create_policy(policy)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create policy: {str(e)}")


@router.get("/policies/{policy_id}", response_model=MaskingPolicy)
async def get_policy(policy_id: int):
    policy = masking_service.get_policy(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.put("/policies/{policy_id}", response_model=MaskingPolicy)
async def update_policy(policy_id: int, update_data: MaskingPolicyUpdate):
    """Edit an existing masking policy and update its DB masking function."""
    try:
        return masking_service.update_policy(policy_id, update_data)
    except ValueError as e:
        detail = str(e)
        if "not found" in detail.lower():
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update policy: {str(e)}")


@router.post("/policies/{policy_id}/reactivate", response_model=MaskingPolicy)
async def reactivate_policy(policy_id: int):
    """Reactivate a disabled policy and recreate its DB masking function."""
    try:
        return masking_service.reactivate_policy(policy_id)
    except ValueError as e:
        detail = str(e)
        if "not found" in detail.lower():
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reactivate policy: {str(e)}")


@router.delete("/policies/{policy_id}")
async def delete_policy(policy_id: int):
    try:
        masking_service.delete_policy(policy_id)
        return {"message": "Policy deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete policy: {str(e)}")


@router.get("/recommendations", response_model=List[MaskingRecommendation])
async def list_recommendations(
    status: Optional[str] = None,
    table_name: Optional[str] = None,
    schema: Optional[str] = None,
):
    """List AI recommendations with optional status and table filtering."""
    try:
        return masking_service.list_recommendations(
            status=status, table_name=table_name, schema_name=schema
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list recommendations: {str(e)}")


@router.post("/recommendations/analyze-and-queue", response_model=List[MaskingRecommendation])
async def analyze_and_queue(request: Optional[AnalyzeAndQueueRequest] = None):
    """
    Analyze database schema metadata with GenAI/heuristics and persist
    structured PENDING recommendations in the database for admin review.
    """
    try:
        req = request or AnalyzeAndQueueRequest()
        return masking_service.analyze_and_queue_recommendations(
            schema_name=req.schema_name, table_name=req.table_name
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze and queue recommendations: {str(e)}"
        )


@router.post("/recommendations/{rec_id}/approve", response_model=MaskingPolicy)
async def approve_recommendation(rec_id: int):
    """
    Approve an AI recommendation to create an ACTIVE MaskingPolicy.
    Validates column existence and prevents duplicate active policies.
    """
    try:
        return masking_service.approve_recommendation(rec_id)
    except ValueError as e:
        detail = str(e)
        if "not found" in detail.lower():
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve recommendation: {str(e)}")


@router.post("/recommendations/{rec_id}/reject", response_model=MaskingRecommendation)
async def reject_recommendation(rec_id: int, body: Optional[RejectRecommendationRequest] = None):
    """
    Reject an AI recommendation. Updates status to REJECTED and never creates a policy.
    """
    try:
        return masking_service.reject_recommendation(rec_id)
    except ValueError as e:
        detail = str(e)
        if "not found" in detail.lower():
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject recommendation: {str(e)}")


@router.post("/apply", response_model=MaskingResult)
async def apply_masking(request: MaskingRequest):
    try:
        return masking_service.apply_masking(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply masking: {str(e)}")
