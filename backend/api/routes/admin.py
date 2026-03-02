"""Human review dashboard endpoints."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, HumanReviewQueue, Return

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class ReviewDecision(BaseModel):
    reviewer_id: str
    decision: str      # approve | deny | request_inspection
    notes: str


@router.get("/queue")
def get_review_queue(db: Session = Depends(get_db)):
    """Get all pending human review items."""
    items = db.query(HumanReviewQueue).filter(
        HumanReviewQueue.status.in_(["pending", "in_review"])
    ).order_by(HumanReviewQueue.created_at.desc()).all()

    return {
        "total": len(items),
        "high_priority": sum(1 for i in items if i.priority in ["high", "urgent"]),
        "queue": [
            {
                "review_id":         i.id,
                "return_id":         i.return_id,
                "priority":          i.priority,
                "status":            i.status,
                "escalation_reason": i.escalation_reason,
                "risk_summary":      i.risk_summary,
                "ai_recommendation": i.ai_recommendation,
                "created_at":        i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ]
    }


@router.get("/queue/{review_id}")
def get_review_item(review_id: str, db: Session = Depends(get_db)):
    """Get a single review item with full return context."""
    item = db.query(HumanReviewQueue).filter(HumanReviewQueue.id == review_id).first()
    if not item:
        raise HTTPException(404, "Review item not found")

    ret = db.query(Return).filter(Return.id == item.return_id).first()

    return {
        "review": {
            "review_id":         item.id,
            "return_id":         item.return_id,
            "priority":          item.priority,
            "status":            item.status,
            "escalation_reason": item.escalation_reason,
            "risk_summary":      item.risk_summary,
            "ai_recommendation": item.ai_recommendation,
            "created_at":        item.created_at.isoformat() if item.created_at else None,
        },
        "return_context": {
            "condition_score":   ret.condition_score if ret else None,
            "condition_grade":   ret.condition_grade if ret else None,
            "fraud_probability": ret.fraud_probability if ret else None,
            "fraud_signals":     ret.fraud_signals if ret else [],
            "fraud_reasoning":   ret.fraud_reasoning if ret else None,
            "expected_loss":     ret.expected_loss if ret else None,
            "agent_trace":       ret.agent_trace if ret else [],
        } if ret else {}
    }


@router.post("/queue/{review_id}/decide")
def submit_decision(review_id: str, req: ReviewDecision, db: Session = Depends(get_db)):
    """Submit human reviewer decision."""
    item = db.query(HumanReviewQueue).filter(HumanReviewQueue.id == review_id).first()
    if not item:
        raise HTTPException(404, "Review item not found")

    item.status            = "resolved"
    item.reviewer_decision = req.decision
    item.reviewer_notes    = req.notes
    item.resolved_at       = datetime.now(timezone.utc)

    # Update return status based on decision
    ret = db.query(Return).filter(Return.id == item.return_id).first()
    if ret:
        if req.decision == "approve":
            ret.status = "refund_issued"
        elif req.decision == "deny":
            ret.status = "warehouse_routed"
        else:
            ret.status = "warehouse_routed"
        ret.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "review_id": review_id,
        "decision":  req.decision,
        "resolved":  True,
        "message":   f"Decision '{req.decision}' applied to return {item.return_id}"
    }


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Dashboard summary statistics."""
    total_returns    = db.query(Return).count()
    refund_issued    = db.query(Return).filter(Return.status == "refund_issued").count()
    escalated        = db.query(Return).filter(Return.status == "escalated").count()
    warehouse_routed = db.query(Return).filter(Return.status == "warehouse_routed").count()
    p2p_matched      = db.query(Return).filter(Return.p2p_match_order_id.isnot(None)).count()
    pending_review   = db.query(HumanReviewQueue).filter(HumanReviewQueue.status == "pending").count()

    return {
        "total_returns":     total_returns,
        "instant_refunds":   refund_issued,
        "escalated":         escalated,
        "warehouse_routed":  warehouse_routed,
        "p2p_matched":       p2p_matched,
        "pending_review":    pending_review,
        "automation_rate":   round(refund_issued / total_returns * 100, 1) if total_returns else 0,
    }
