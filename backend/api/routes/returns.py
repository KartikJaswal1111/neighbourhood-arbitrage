"""Return lifecycle endpoints."""
import threading
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import (
    get_db, SessionLocal, Return, Order, Product, Customer,
    SmartLocker, LockerAllocation, HumanReviewQueue
)
from agent.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/api/v1/returns", tags=["returns"])


# ── Request / Response schemas ────────────────────────────────────

class InitiateRequest(BaseModel):
    customer_id: str
    order_id: str
    reason_text: str
    media_urls: list[str]
    returner_lat: float
    returner_lng: float


class SimulateLockerRequest(BaseModel):
    locker_ai_score: int = 82
    weight_match: bool = True
    camera_match: bool = True


# ── Background analysis runner ────────────────────────────────────

def _run_agent(return_id: str, context: dict):
    """Runs agent in a background thread with its own event loop + DB session."""
    db = SessionLocal()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        orchestrator = AgentOrchestrator(db=db)
        result = loop.run_until_complete(orchestrator.run(context))
        trace = result["trace"]

        # ── Extract results from trace ─────────────────────────
        def find(tool_name):
            return next((t["output"] for t in trace if t["tool"] == tool_name), {})

        condition   = find("analyze_item_condition")
        fraud       = find("calculate_fraud_risk")
        matching    = find("search_nearby_buyers")
        hub_result  = find("find_nearest_hub")
        refund_risk = find("calculate_refund_risk")
        routing     = find("generate_routing_instruction")
        refund_issued = find("issue_instant_refund")
        escalation  = find("escalate_to_human")
        locker_alloc = find("allocate_locker")

        # ── Determine final status ─────────────────────────────
        if escalation.get("escalated"):
            status = "escalated"
        elif refund_issued.get("success"):
            status = "awaiting_locker_dropoff"
        elif routing.get("routing_type") == "warehouse":
            status = "warehouse_routed"
        else:
            status = "no_match_routed"

        # ── Update return record ───────────────────────────────
        ret = db.query(Return).filter(Return.id == return_id).first()
        if ret:
            ret.status              = status
            ret.condition_score     = condition.get("overall_score")
            ret.condition_grade     = condition.get("grade")
            ret.detected_issues     = condition.get("issues", [])
            ret.authenticity_result = condition.get("authenticity", {})
            ret.fraud_probability   = fraud.get("fraud_probability")
            ret.fraud_signals       = fraud.get("signals", [])
            ret.fraud_reasoning     = fraud.get("reasoning")
            ret.refund_decision     = refund_risk.get("decision")
            ret.refund_reasoning    = refund_risk.get("reasoning")
            ret.expected_loss       = refund_risk.get("total_risk")
            ret.routing_decision    = routing.get("routing_type")
            ret.routing_instructions= routing.get("instruction", {})
            ret.agent_trace         = trace
            ret.updated_at          = datetime.now(timezone.utc)

            if refund_issued.get("success"):
                ret.refund_amount    = refund_issued.get("amount")
                ret.transaction_id   = refund_issued.get("transaction_id")

            if matching.get("best_match"):
                ret.p2p_match_order_id = matching["best_match"].get("order_id")
                ret.match_distance_km  = matching["best_match"].get("distance_km")

            if hub_result.get("hub_found"):
                hub = hub_result["nearest_hub"]
                ret.hub_id = hub.get("hub_id")

            if locker_alloc.get("success"):
                ret.locker_id = locker_alloc.get("locker_id")

            db.commit()

    except Exception as e:
        db.query(Return).filter(Return.id == return_id).update({
            "status": "error",
            "updated_at": datetime.now(timezone.utc)
        })
        db.commit()
        print(f"Agent error for {return_id}: {e}")
    finally:
        db.close()


# ── Endpoints ─────────────────────────────────────────────────────

@router.post("/initiate")
def initiate_return(req: InitiateRequest, background_tasks: BackgroundTasks,
                    db: Session = Depends(get_db)):
    """
    Create a return record and kick off background AI analysis.
    Returns immediately with return_id — frontend polls /status.
    """
    order = db.query(Order).filter(Order.id == req.order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    product = db.query(Product).filter(Product.id == order.product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")

    ret = Return(
        customer_id=req.customer_id,
        order_id=req.order_id,
        product_id=order.product_id,
        status="analyzing",
        reason_raw=req.reason_text
    )
    db.add(ret)
    db.commit()
    db.refresh(ret)

    context = {
        "return_id":        ret.id,
        "customer_id":      req.customer_id,
        "order_id":         req.order_id,
        "product_id":       order.product_id,
        "product_name":     product.name,
        "product_category": product.category,
        "item_value":       product.unit_price,
        "size_variant":     order.size_variant or "N/A",
        "weight_grams":     product.weight_grams,
        "liquidation_rate": product.liquidation_rate,
        "reason_text":      req.reason_text,
        "media_urls":       req.media_urls,
        "returner_lat":     req.returner_lat,
        "returner_lng":     req.returner_lng,
    }

    # Run agent in background thread (avoids blocking the HTTP response)
    t = threading.Thread(target=_run_agent, args=(ret.id, context), daemon=True)
    t.start()

    return {
        "return_id": ret.id,
        "status": "analyzing",
        "message": "AI assessment started. Poll /api/v1/returns/{return_id} for results.",
        "product": product.name,
        "value": product.unit_price
    }


@router.get("/{return_id}")
def get_return(return_id: str, db: Session = Depends(get_db)):
    """Poll for return status and full decision."""
    ret = db.query(Return).filter(Return.id == return_id).first()
    if not ret:
        raise HTTPException(404, "Return not found")

    # Build locker info if available
    locker_info = None
    if ret.locker_id:
        alloc = db.query(LockerAllocation).filter(
            LockerAllocation.return_id == return_id
        ).first()
        if alloc:
            locker_info = {
                "allocation_id":    alloc.id,
                "locker_id":        alloc.locker_id,
                "locker_unit":      f"Locker {db.query(SmartLocker).filter(SmartLocker.id == alloc.locker_id).first().unit_number if alloc.locker_id else ''}",
                "dropoff_qr_hash":  alloc.dropoff_qr_hash,
                "pickup_qr_hash":   alloc.pickup_qr_hash,
                "allocation_status":alloc.status,
                "expires_at":       alloc.allocated_at.isoformat() if alloc.allocated_at else None,
            }

    # Build escalation info if queued
    escalation_info = None
    if ret.status == "escalated":
        review = db.query(HumanReviewQueue).filter(
            HumanReviewQueue.return_id == return_id
        ).first()
        if review:
            escalation_info = {
                "review_id":         review.id,
                "priority":          review.priority,
                "escalation_reason": review.escalation_reason,
                "risk_summary":      review.risk_summary,
                "ai_recommendation": review.ai_recommendation,
                "queue_status":      review.status,
            }

    return {
        "return_id":    ret.id,
        "status":       ret.status,
        "customer_id":  ret.customer_id,
        "product_id":   ret.product_id,
        "reason":       ret.reason_raw,
        "condition": {
            "score":         ret.condition_score,
            "grade":         ret.condition_grade,
            "issues":        ret.detected_issues or [],
            "authenticity":  ret.authenticity_result or {},
        },
        "fraud": {
            "probability":   ret.fraud_probability,
            "signals":       ret.fraud_signals or [],
            "reasoning":     ret.fraud_reasoning,
        },
        "refund": {
            "decision":      ret.refund_decision,
            "reasoning":     ret.refund_reasoning,
            "expected_loss": ret.expected_loss,
            "amount":        ret.refund_amount,
            "transaction_id":ret.transaction_id,
        },
        "matching": {
            "p2p_match_order_id": ret.p2p_match_order_id,
            "match_distance_km":  ret.match_distance_km,
        },
        "routing": {
            "decision":      ret.routing_decision,
            "instructions":  ret.routing_instructions or {},
        },
        "locker":       locker_info,
        "escalation":   escalation_info,
        "agent_trace":  ret.agent_trace or [],
        "created_at":   ret.created_at.isoformat() if ret.created_at else None,
        "updated_at":   ret.updated_at.isoformat() if ret.updated_at else None,
    }


@router.post("/{return_id}/simulate-locker-dropoff")
def simulate_locker_dropoff(
    return_id: str,
    req: SimulateLockerRequest,
    db: Session = Depends(get_db)
):
    """
    DEMO ONLY — simulates IoT locker confirmation event.
    In production this is a webhook from the locker hardware.
    """
    alloc = db.query(LockerAllocation).filter(
        LockerAllocation.return_id == return_id
    ).first()
    if not alloc:
        raise HTTPException(404, "No locker allocation for this return")

    if alloc.status != "awaiting_dropoff":
        raise HTTPException(400, f"Allocation already in status: {alloc.status}")

    # Simulate locker IoT verification
    alloc.status              = "dropoff_confirmed"
    alloc.camera_sku_match    = req.camera_match
    alloc.camera_confidence   = 0.92 if req.camera_match else 0.41
    alloc.locker_ai_score     = req.locker_ai_score
    alloc.weight_match        = req.weight_match
    alloc.dropoff_confirmed_at= datetime.now(timezone.utc)
    alloc.pickup_qr_hash      = f"PICKUP-{alloc.dropoff_qr_hash[:8]}"

    # Update locker status
    if alloc.locker_id:
        locker = db.query(SmartLocker).filter(SmartLocker.id == alloc.locker_id).first()
        if locker:
            locker.status = "occupied"

    # Update return status
    ret = db.query(Return).filter(Return.id == return_id).first()
    if ret and req.weight_match and req.camera_match:
        ret.status = "refund_issued"
        ret.updated_at = datetime.now(timezone.utc)

    db.commit()

    if not (req.weight_match and req.camera_match):
        return {
            "confirmed": False,
            "issue": "Locker verification failed — weight or camera mismatch.",
            "action": "Human review triggered. Locker remains locked."
        }

    return {
        "confirmed": True,
        "locker_ai_score":     req.locker_ai_score,
        "weight_verified":     req.weight_match,
        "camera_verified":     req.camera_match,
        "pickup_qr_hash":      alloc.pickup_qr_hash,
        "buyer_notified":      True,
        "message": (
            "Locker confirmed item receipt. "
            "Refund is live. Buyer QR code dispatched."
        )
    }
