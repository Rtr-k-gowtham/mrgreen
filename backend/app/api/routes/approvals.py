"""
MR.GREEN — Human Approval Routes

Endpoints for reviewing, approving, and rejecting gated or critical tool actions.
"""

from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session, get_tool_executor
from app.database.models import Approval, ApprovalStatus, ToolCall
from app.tools.executor import ToolExecutor

router = APIRouter(prefix="/api/approvals")


class ApprovalItemResponse(BaseModel):
    id: str
    resource_type: str
    resource_id: str
    action: str
    status: str
    reason: str | None = None
    created_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApprovalDecisionRequest(BaseModel):
    reason: str | None = None


@router.get("", response_model=list[ApprovalItemResponse])
async def list_approvals(
    status: str = Query(default="pending"),
    db: AsyncSession = Depends(get_db_session),
) -> list[ApprovalItemResponse]:
    """List approval requests filtered by status (default: pending)."""
    try:
        status_enum = ApprovalStatus(status.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status '{status}'. Use pending, approved, or denied.")

    result = await db.execute(
        select(Approval)
        .where(Approval.status == status_enum)
        .order_by(Approval.created_at.desc())
    )
    approvals = result.scalars().all()

    return [
        ApprovalItemResponse(
            id=a.id,
            resource_type=a.resource_type,
            resource_id=a.resource_id,
            action=a.action,
            status=a.status.value,
            reason=a.reason,
            created_at=a.created_at.isoformat() if a.created_at else None,
            metadata=a.metadata_ or {},
        )
        for a in approvals
    ]


@router.post("/{approval_id}/approve")
async def approve_action(
    approval_id: str,
    payload: ApprovalDecisionRequest | None = None,
    db: AsyncSession = Depends(get_db_session),
    executor: ToolExecutor = Depends(get_tool_executor),
) -> dict[str, Any]:
    """
    Approve an action. If it is a tool_call, immediately execute it.
    """
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail=f"Approval request '{approval_id}' not found")

    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Approval request is already '{approval.status.value}'")

    approval.status = ApprovalStatus.APPROVED
    approval.decided_at = datetime.now(timezone.utc)
    if payload and payload.reason:
        approval.reason = payload.reason

    execution_result = None

    # If this is a pending tool execution, run it now with pre-approval
    if approval.resource_type == "tool_call":
        meta = approval.metadata_ or {}
        tool_name = meta.get("tool_name")
        args = meta.get("arguments", {})

        if tool_name:
            exec_resp = await executor.execute(
                tool_name=tool_name,
                arguments=args,
                db_session=db,
                is_pre_approved=True,
            )
            execution_result = exec_resp.to_dict()

            # Update corresponding pending tool call record if exists
            tc_res = await db.execute(select(ToolCall).where(ToolCall.id == approval_id))
            tc = tc_res.scalar_one_or_none()
            if tc:
                tc.status = exec_resp.status
                tc.success = exec_resp.success
                tc.output_data = exec_resp.result if isinstance(exec_resp.result, dict) else {"result": str(exec_resp.result)}
                tc.error_message = exec_resp.error
                tc.duration_ms = exec_resp.duration_ms

    await db.commit()

    return {
        "id": approval_id,
        "status": "approved",
        "action": approval.action,
        "execution": execution_result,
    }


@router.post("/{approval_id}/reject")
async def reject_action(
    approval_id: str,
    payload: ApprovalDecisionRequest | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """
    Reject an action.
    """
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail=f"Approval request '{approval_id}' not found")

    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Approval request is already '{approval.status.value}'")

    approval.status = ApprovalStatus.DENIED
    approval.decided_at = datetime.now(timezone.utc)
    if payload and payload.reason:
        approval.reason = payload.reason

    # Mark tool call as rejected if exists
    if approval.resource_type == "tool_call":
        tc_res = await db.execute(select(ToolCall).where(ToolCall.id == approval_id))
        tc = tc_res.scalar_one_or_none()
        if tc:
            tc.status = "rejected"
            tc.success = False
            tc.error_message = f"Rejected by human operator: {payload.reason if payload else 'No reason specified'}"

    await db.commit()

    return {
        "id": approval_id,
        "status": "denied",
        "action": approval.action,
    }
