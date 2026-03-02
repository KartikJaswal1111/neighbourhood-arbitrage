"""
Tool implementations — each function maps 1:1 to a tool in tool_registry.py.
These are plain async Python functions; the agent calls them by name.
"""
import math
import json
import uuid
import random
import re
from datetime import datetime, timezone, timedelta

import anthropic
from sqlalchemy.orm import Session

from config import settings
from database import (
    Order, Product, CustomerTrustProfile,
    CommunityHub, SmartLocker, LockerAllocation, HumanReviewQueue
)
from agent.prompts import get_inspection_prompt, get_mock_response

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


# ─────────────────────────────────────────────────────────────────
# Geo helper
# ─────────────────────────────────────────────────────────────────

def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─────────────────────────────────────────────────────────────────
# Tool 1 — analyze_item_condition
# ─────────────────────────────────────────────────────────────────

async def tool_analyze_item_condition(
    media_urls: list[str],
    product_category: str,
    product_metadata: dict
) -> dict:
    """
    Calls Claude Vision to inspect item condition.
    Falls back to mock response if vision call fails or USE_MOCK_VISION=true.
    """
    if settings.USE_MOCK_VISION or not media_urls:
        return get_mock_response(product_category)

    prompt = get_inspection_prompt(product_category, product_metadata)
    content = []

    for url in media_urls[:4]:
        try:
            content.append({
                "type": "image",
                "source": {"type": "url", "url": url}
            })
        except Exception:
            pass

    if not content:
        return get_mock_response(product_category)

    content.append({"type": "text", "text": prompt})

    try:
        response = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": content}]
        )
        raw = response.content[0].text
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return get_mock_response(product_category)
    except Exception:
        return get_mock_response(product_category)


# ─────────────────────────────────────────────────────────────────
# Tool 2 — get_customer_trust_score
# ─────────────────────────────────────────────────────────────────

async def tool_get_customer_trust_score(customer_id: str, db: Session) -> dict:
    profile = db.query(CustomerTrustProfile).filter(
        CustomerTrustProfile.customer_id == customer_id
    ).first()

    if not profile:
        return {
            "customer_id": customer_id,
            "trust_score": 50,
            "lifetime_orders": 0,
            "lifetime_returns": 0,
            "return_rate": 0.0,
            "fraud_flags": 0,
            "p2p_accepted_count": 0,
            "profile_status": "new_customer"
        }

    return {
        "customer_id": customer_id,
        "trust_score": profile.trust_score,
        "lifetime_orders": profile.lifetime_orders,
        "lifetime_returns": profile.lifetime_returns,
        "return_rate": profile.return_rate,
        "fraud_flags": profile.fraud_flags,
        "p2p_accepted_count": profile.p2p_accepted_count,
        "profile_status": "established"
    }


# ─────────────────────────────────────────────────────────────────
# Tool 3 — calculate_fraud_risk
# ─────────────────────────────────────────────────────────────────

async def tool_calculate_fraud_risk(
    customer_id: str,
    order_id: str,
    item_value: float,
    product_category: str,
    trust_profile: dict,
    condition_score: int
) -> dict:
    signals = []

    # Signal: return rate
    rr = trust_profile.get("return_rate", 0)
    if rr > 0.35:
        signals.append({"signal": "high_return_rate", "value": round(rr, 2), "weight": "high_risk"})
    elif rr > 0.15:
        signals.append({"signal": "elevated_return_rate", "value": round(rr, 2), "weight": "medium_risk"})
    else:
        signals.append({"signal": "normal_return_rate", "value": round(rr, 2), "weight": "low_risk"})

    # Signal: fraud flags
    ff = trust_profile.get("fraud_flags", 0)
    if ff > 0:
        signals.append({"signal": "prior_fraud_flags", "value": ff, "weight": "critical"})

    # Signal: item value band
    if item_value > 500:
        signals.append({"signal": "very_high_value_item", "value": item_value, "weight": "high_risk"})
    elif item_value > 200:
        signals.append({"signal": "high_value_item", "value": item_value, "weight": "medium_risk"})

    # Signal: suspicious condition gap (claims good, AI says bad)
    if condition_score < 40 and item_value > 100:
        signals.append({"signal": "low_condition_high_value", "value": condition_score, "weight": "high_risk"})

    # Base rates by category
    base_rates = {"footwear": 0.08, "apparel": 0.06, "electronics": 0.14}
    base = base_rates.get(product_category, 0.10)

    trust = trust_profile.get("trust_score", 75)
    trust_modifier = (100 - trust) / 100

    high_risk = sum(1 for s in signals if s["weight"] in ["high_risk", "critical"])
    medium_risk = sum(1 for s in signals if s["weight"] == "medium_risk")

    prob = base + (high_risk * 0.15) + (medium_risk * 0.07) + (trust_modifier * 0.20)
    prob = min(round(prob, 3), 0.95)

    # LLM reasoning for top risk factors (skipped in mock mode)
    if settings.USE_MOCK_AGENT:
        top_signals = [s["signal"].replace("_", " ") for s in signals if s["weight"] in ["critical", "high_risk"]]
        reasoning = (
            f"Fraud probability {prob:.1%} — "
            + (f"key risk factors: {', '.join(top_signals)}." if top_signals else "no major risk factors detected.")
        )
    else:
        try:
            r = client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Fraud signals for a ${item_value:.0f} {product_category} return:\n"
                        f"{json.dumps(signals, indent=2)}\n"
                        f"Fraud probability: {prob:.1%}\n"
                        f"In 2 concise sentences, identify the key risk factors."
                    )
                }]
            )
            reasoning = r.content[0].text.strip()
        except Exception:
            reasoning = f"Fraud probability {prob:.1%} based on {len(signals)} behavioral signals."

    return {
        "fraud_probability": prob,
        "risk_level": "high" if prob > 0.4 else "medium" if prob > 0.15 else "low",
        "signals": signals,
        "reasoning": reasoning,
        "base_rate": base
    }


# ─────────────────────────────────────────────────────────────────
# Tool 4 — search_nearby_buyers
# ─────────────────────────────────────────────────────────────────

async def tool_search_nearby_buyers(
    product_id: str,
    size_variant: str,
    returner_lat: float,
    returner_lng: float,
    condition_score: int,
    radius_km: float,
    db: Session
) -> dict:
    product = db.query(Product).filter(Product.id == product_id).first()
    min_score = product.min_p2p_condition_score if product else 75
    item_value = product.unit_price if product else 140.0

    pending = db.query(Order).filter(
        Order.product_id == product_id,
        Order.status == "pending",
        Order.size_variant == size_variant
    ).all()

    candidates = []
    for o in pending:
        dist = haversine_km(returner_lat, returner_lng, o.geo_lat, o.geo_lng)
        if dist > radius_km:
            continue

        score = 0
        if dist < 10:   score += 40
        elif dist < 25: score += 30
        elif dist < 50: score += 20
        else:           score += 10

        if condition_score >= min_score:       score += 30
        elif condition_score >= min_score - 10: score += 15

        candidates.append({
            "order_id": o.id,
            "customer_id": o.customer_id,
            "distance_km": round(dist, 1),
            "match_score": score,
            "p2p_eligible": condition_score >= min_score
        })

    candidates.sort(key=lambda x: x["match_score"], reverse=True)
    top = candidates[0] if candidates else None

    recovery = {
        "community_hub_p2p": {"pct": 82, "amount": round(item_value * 0.82, 2)},
        "carrier_p2p":       {"pct": 75, "amount": round(item_value * 0.75, 2)},
        "warehouse":         {"pct": 60, "amount": round(item_value * 0.60, 2)},
        "resale_partner":    {"pct": 45, "amount": round(item_value * 0.45, 2)},
        "liquidation":       {"pct": 20, "amount": round(item_value * 0.20, 2)},
    }

    return {
        "match_found": bool(top and top["p2p_eligible"]),
        "candidates_found": len(candidates),
        "best_match": top,
        "all_candidates": candidates[:3],
        "search_radius_km": radius_km,
        "min_condition_required": min_score,
        "recovery_options": recovery
    }


# ─────────────────────────────────────────────────────────────────
# Tool 5 — find_nearest_hub
# ─────────────────────────────────────────────────────────────────

async def tool_find_nearest_hub(
    returner_lat: float,
    returner_lng: float,
    item_category: str,
    search_radius_km: float,
    db: Session
) -> dict:
    hubs = db.query(CommunityHub).filter(CommunityHub.is_active == True).all()

    results = []
    for hub in hubs:
        dist = haversine_km(returner_lat, returner_lng, hub.geo_lat, hub.geo_lng)
        if dist > search_radius_km:
            continue

        # Check available lockers
        available = db.query(SmartLocker).filter(
            SmartLocker.hub_id == hub.id,
            SmartLocker.status == "available"
        ).first()

        if available:
            walk_min = int(dist * 12)  # ~12 min per km walking
            results.append({
                "hub_id": hub.id,
                "hub_name": hub.name,
                "partner": hub.partner_name,
                "address": hub.address,
                "distance_km": round(dist, 2),
                "walking_minutes": walk_min,
                "available_locker_id": available.id,
                "available_locker_unit": available.unit_number,
                "operating_hours": hub.operating_hours
            })

    results.sort(key=lambda x: x["distance_km"])

    if results:
        return {
            "hub_found": True,
            "nearest_hub": results[0],
            "all_hubs": results[:3]
        }

    return {
        "hub_found": False,
        "nearest_hub": None,
        "all_hubs": [],
        "message": "No hubs with available lockers within search radius"
    }


# ─────────────────────────────────────────────────────────────────
# Tool 6 — calculate_refund_risk
# ─────────────────────────────────────────────────────────────────

async def tool_calculate_refund_risk(
    item_value: float,
    fraud_probability: float,
    condition_score: int,
    liquidation_rate: float = 0.20,
    locker_available: bool = False
) -> dict:
    # Locker model reduces risk: physical confirmation lowers fraud effectiveness
    effective_fraud_prob = (
        fraud_probability * settings.LOCKER_RISK_MULTIPLIER
        if locker_available else fraud_probability
    )

    unrecoverable = item_value * (1 - liquidation_rate)
    expected_loss = effective_fraud_prob * unrecoverable

    # Condition value haircut
    haircut = 0.0
    if condition_score < 45:
        haircut = item_value * 0.25
    elif condition_score < 60:
        haircut = item_value * 0.10

    total_risk = expected_loss + haircut

    # Hard rules
    hard_deny = []
    if fraud_probability > settings.REFUND_HARD_DENY_FRAUD_PROB:
        hard_deny.append(f"Fraud probability {fraud_probability:.1%} exceeds hard limit")
    if item_value > settings.REFUND_HARD_DENY_ITEM_VALUE:
        hard_deny.append(f"Item value ${item_value} exceeds auto-approve limit ${settings.REFUND_HARD_DENY_ITEM_VALUE}")
    if condition_score < settings.REFUND_MIN_CONDITION_SCORE:
        hard_deny.append(f"Condition score {condition_score} below minimum {settings.REFUND_MIN_CONDITION_SCORE}")

    if hard_deny:
        decision = "escalate"
        reasoning = "Hard rule triggered: " + "; ".join(hard_deny)
    elif total_risk <= settings.REFUND_AUTO_APPROVE_MAX_LOSS:
        decision = "auto_approved"
        reasoning = (
            f"Expected loss ${total_risk:.2f} is below ${settings.REFUND_AUTO_APPROVE_MAX_LOSS:.2f} threshold."
            + (" Locker model applied — risk reduced by physical confirmation." if locker_available else "")
            + " Refund auto-approved."
        )
    else:
        decision = "escalate"
        reasoning = (
            f"Expected loss ${total_risk:.2f} exceeds ${settings.REFUND_AUTO_APPROVE_MAX_LOSS:.2f} threshold."
            " Human review required."
        )

    return {
        "decision": decision,
        "expected_loss": round(expected_loss, 2),
        "condition_haircut": round(haircut, 2),
        "total_risk": round(total_risk, 2),
        "unrecoverable_value": round(unrecoverable, 2),
        "auto_approve_threshold": settings.REFUND_AUTO_APPROVE_MAX_LOSS,
        "locker_risk_reduction_applied": locker_available,
        "effective_fraud_prob": round(effective_fraud_prob, 3),
        "reasoning": reasoning,
        "hard_deny_triggered": bool(hard_deny),
        "hard_deny_reasons": hard_deny
    }


# ─────────────────────────────────────────────────────────────────
# Tool 7 — allocate_locker
# ─────────────────────────────────────────────────────────────────

async def tool_allocate_locker(
    hub_id: str,
    return_id: str,
    item_weight_g: float,
    return_window_hrs: int,
    db: Session
) -> dict:
    locker = db.query(SmartLocker).filter(
        SmartLocker.hub_id == hub_id,
        SmartLocker.status == "available"
    ).first()

    if not locker:
        return {"success": False, "error": "No available lockers at this hub"}

    hub = db.query(CommunityHub).filter(CommunityHub.id == hub_id).first()

    # Reserve the locker
    locker.status = "reserved"
    db.commit()

    qr_hash = str(uuid.uuid4())
    expires = datetime.now(timezone.utc) + timedelta(hours=return_window_hrs)

    allocation = LockerAllocation(
        return_id=return_id,
        locker_id=locker.id,
        hub_id=hub_id,
        dropoff_qr_hash=qr_hash,
        expected_weight_g=item_weight_g,
        dropoff_window_hrs=return_window_hrs,
        pickup_window_hrs=24,
        allocated_at=datetime.now(timezone.utc)
    )
    db.add(allocation)
    db.commit()

    return {
        "success": True,
        "allocation_id": allocation.id,
        "locker_id": locker.id,
        "locker_unit": f"Locker {locker.unit_number}",
        "hub_name": hub.name if hub else "Community Hub",
        "hub_address": hub.address if hub else "",
        "dropoff_qr_hash": qr_hash,
        "dropoff_window_hours": return_window_hrs,
        "expires_at": expires.isoformat(),
        "instructions": (
            f"Go to {hub.name if hub else 'Community Hub'} — "
            f"scan your QR code at Locker {locker.unit_number}. "
            f"Place item inside and close the door. "
            f"Your refund fires the moment the locker confirms receipt."
        )
    }


# ─────────────────────────────────────────────────────────────────
# Tool 8 — issue_instant_refund
# ─────────────────────────────────────────────────────────────────

async def tool_issue_instant_refund(
    customer_id: str,
    return_id: str,
    amount: float,
    reasoning: str
) -> dict:
    txn_id = f"TXN-{random.randint(100000, 999999)}"
    return {
        "success": True,
        "transaction_id": txn_id,
        "amount": amount,
        "currency": "CAD",
        "customer_id": customer_id,
        "return_id": return_id,
        "credited_to": "Payment method on file",
        "status": "Instant — funds available now",
        "reasoning": reasoning
    }


# ─────────────────────────────────────────────────────────────────
# Tool 9 — generate_routing_instruction
# ─────────────────────────────────────────────────────────────────

async def tool_generate_routing_instruction(
    return_id: str,
    routing_type: str,
    reasoning: str,
    hub_id: str = None,
    locker_unit: str = None,
    p2p_match_order_id: str = None
) -> dict:
    instructions_map = {
        "community_hub_p2p": {
            "title": "Drop at Smart Locker — Nearby Buyer Found",
            "description": (
                "A verified buyer is located near you. "
                "Drop your item at the Community Hub Smart Locker. "
                "Your refund fires the moment the locker confirms receipt."
            ),
            "carrier": "Smart Locker Network",
            "estimated_days": 1,
            "co2_saved_kg": 3.1,
            "cost_to_company": 0.0
        },
        "carrier_p2p": {
            "title": "Ship to Nearby Buyer (Carrier)",
            "description": "A buyer is within range. Ship using the prepaid label below.",
            "carrier": "Canada Post Expedited",
            "estimated_days": 2,
            "co2_saved_kg": 1.8,
            "cost_to_company": 11.0
        },
        "warehouse": {
            "title": "Return to Warehouse",
            "description": "No nearby buyer found. Please return to our processing centre.",
            "carrier": "Canada Post",
            "estimated_days": 5,
            "co2_saved_kg": 0.0,
            "cost_to_company": 27.0
        },
        "resale_partner": {
            "title": "Ship to Resale Partner",
            "description": "Item routed to our regional refurbishment partner.",
            "carrier": "UPS Ground",
            "estimated_days": 3,
            "co2_saved_kg": 1.2,
            "cost_to_company": 18.0
        },
        "liquidation": {
            "title": "Liquidation Route",
            "description": "Item will be liquidated. Partial refund credited.",
            "carrier": "Canada Post",
            "estimated_days": 7,
            "co2_saved_kg": 0.0,
            "cost_to_company": 35.0
        }
    }

    info = instructions_map.get(routing_type, instructions_map["warehouse"])

    return {
        "routing_type": routing_type,
        "hub_id": hub_id,
        "locker_unit": locker_unit,
        "p2p_match_order_id": p2p_match_order_id,
        "instruction": info,
        "label_url": f"https://mock-carrier.example.com/label/{return_id}",
        "reasoning": reasoning
    }


# ─────────────────────────────────────────────────────────────────
# Tool 10 — escalate_to_human
# ─────────────────────────────────────────────────────────────────

async def tool_escalate_to_human(
    return_id: str,
    escalation_reason: str,
    risk_summary: dict,
    ai_recommendation: str,
    priority: str,
    db: Session
) -> dict:
    item = HumanReviewQueue(
        return_id=return_id,
        escalation_reason=escalation_reason,
        risk_summary=risk_summary,
        ai_recommendation=ai_recommendation,
        priority=priority,
        status="pending"
    )
    db.add(item)
    db.commit()

    return {
        "escalated": True,
        "review_id": item.id,
        "priority": priority,
        "message": (
            "AI processing has stopped. This return requires human judgment. "
            "A reviewer will assess within 2 hours."
        ),
        "ai_recommendation": ai_recommendation
    }
