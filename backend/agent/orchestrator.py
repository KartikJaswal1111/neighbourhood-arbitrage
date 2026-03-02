"""
Agent Orchestrator — runs the Claude tool-calling loop.
Dispatches tool calls, records the trace, returns final decision.
"""
import asyncio
import json
import time

import anthropic
from sqlalchemy.orm import Session

from config import settings
from agent.system_prompt import SYSTEM_PROMPT
from agent.tool_registry import TOOLS
from agent.tools import (
    tool_analyze_item_condition,
    tool_get_customer_trust_score,
    tool_calculate_fraud_risk,
    tool_search_nearby_buyers,
    tool_find_nearest_hub,
    tool_calculate_refund_risk,
    tool_allocate_locker,
    tool_issue_instant_refund,
    tool_generate_routing_instruction,
    tool_escalate_to_human,
)

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


class AgentOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.trace: list[dict] = []

    async def _dispatch(self, name: str, inp: dict) -> dict:
        """Execute a named tool, record timing and result."""
        t0 = time.time()

        tool_map = {
            "analyze_item_condition": lambda: tool_analyze_item_condition(
                inp["media_urls"], inp["product_category"], inp.get("product_metadata", {})
            ),
            "get_customer_trust_score": lambda: tool_get_customer_trust_score(
                inp["customer_id"], self.db
            ),
            "calculate_fraud_risk": lambda: tool_calculate_fraud_risk(
                inp["customer_id"], inp["order_id"], inp["item_value"],
                inp["product_category"], inp["trust_profile"], inp["condition_score"]
            ),
            "search_nearby_buyers": lambda: tool_search_nearby_buyers(
                inp["product_id"], inp.get("size_variant", ""),
                inp["returner_lat"], inp["returner_lng"],
                inp["condition_score"], inp.get("radius_km", 50.0), self.db
            ),
            "find_nearest_hub": lambda: tool_find_nearest_hub(
                inp["returner_lat"], inp["returner_lng"],
                inp["item_category"], inp.get("search_radius_km", 5.0), self.db
            ),
            "calculate_refund_risk": lambda: tool_calculate_refund_risk(
                inp["item_value"], inp["fraud_probability"],
                inp["condition_score"], inp.get("liquidation_rate", 0.20),
                inp.get("locker_available", False)
            ),
            "allocate_locker": lambda: tool_allocate_locker(
                inp["hub_id"], inp["return_id"],
                inp.get("item_weight_g", 500.0), inp.get("return_window_hrs", 48), self.db
            ),
            "issue_instant_refund": lambda: tool_issue_instant_refund(
                inp["customer_id"], inp["return_id"], inp["amount"], inp["reasoning"]
            ),
            "generate_routing_instruction": lambda: tool_generate_routing_instruction(
                inp["return_id"], inp["routing_type"], inp["reasoning"],
                inp.get("hub_id"), inp.get("locker_unit"), inp.get("p2p_match_order_id")
            ),
            "escalate_to_human": lambda: tool_escalate_to_human(
                inp["return_id"], inp["escalation_reason"], inp["risk_summary"],
                inp["ai_recommendation"], inp.get("priority", "normal"), self.db
            ),
        }

        if name not in tool_map:
            result = {"error": f"Unknown tool: {name}"}
        else:
            result = await tool_map[name]()

        duration_ms = int((time.time() - t0) * 1000)

        self.trace.append({
            "tool": name,
            "input": inp,
            "output": result,
            "duration_ms": duration_ms,
            "status": "error" if "error" in result else "completed"
        })

        return result

    async def run_mock(self, context: dict) -> dict:
        """
        Zero-cost mock agent — calls real tools directly, skips Claude API entirely.
        Produces identical trace/output to the real agent, just deterministically.
        """
        return_id   = context["return_id"]
        customer_id = context["customer_id"]
        order_id    = context["order_id"]
        product_id  = context["product_id"]
        category    = context["product_category"]
        value       = context["item_value"]
        lat         = context["returner_lat"]
        lng         = context["returner_lng"]
        size        = context.get("size_variant", "")
        weight      = float(context.get("weight_grams", 500))
        liq_rate    = context.get("liquidation_rate", 0.20)
        media_urls  = context.get("media_urls", [])

        # Step 1 — parallel: condition inspection + trust profile
        condition, trust = await asyncio.gather(
            self._dispatch("analyze_item_condition", {
                "media_urls": media_urls,
                "product_category": category,
                "product_metadata": {}
            }),
            self._dispatch("get_customer_trust_score", {
                "customer_id": customer_id
            })
        )

        cond_score = condition.get("overall_score", 75)

        # Step 2 — fraud risk (rule-based, no LLM in mock mode)
        fraud = await self._dispatch("calculate_fraud_risk", {
            "customer_id": customer_id,
            "order_id": order_id,
            "item_value": value,
            "product_category": category,
            "trust_profile": trust,
            "condition_score": cond_score
        })

        # Step 3 — parallel: nearby buyers + nearest hub
        buyers, hub = await asyncio.gather(
            self._dispatch("search_nearby_buyers", {
                "product_id": product_id,
                "size_variant": size,
                "returner_lat": lat,
                "returner_lng": lng,
                "condition_score": cond_score,
                "radius_km": 50.0
            }),
            self._dispatch("find_nearest_hub", {
                "returner_lat": lat,
                "returner_lng": lng,
                "item_category": category,
                "search_radius_km": 5.0
            })
        )

        hub_available = hub.get("hub_found", False)

        # Step 4 — refund risk calculation (pure math, no LLM)
        risk = await self._dispatch("calculate_refund_risk", {
            "item_value": value,
            "fraud_probability": fraud.get("fraud_probability", 0.10),
            "condition_score": cond_score,
            "liquidation_rate": liq_rate,
            "locker_available": hub_available
        })

        # Step 5 — terminal action based on risk decision
        if risk.get("decision") == "auto_approved":
            hub_id      = hub["nearest_hub"]["hub_id"] if hub_available else None
            locker_unit = hub["nearest_hub"].get("available_locker_unit") if hub_available else None

            if hub_available:
                locker = await self._dispatch("allocate_locker", {
                    "hub_id": hub_id,
                    "return_id": return_id,
                    "item_weight_g": weight,
                    "return_window_hrs": 48
                })
                locker_unit = locker.get("locker_unit", locker_unit)

            await self._dispatch("issue_instant_refund", {
                "customer_id": customer_id,
                "return_id": return_id,
                "amount": value,
                "reasoning": risk.get("reasoning", "Auto-approved by risk engine.")
            })

            routing_type = (
                "community_hub_p2p" if hub_available else
                "carrier_p2p"       if buyers.get("match_found") else
                "warehouse"
            )
            await self._dispatch("generate_routing_instruction", {
                "return_id": return_id,
                "routing_type": routing_type,
                "reasoning": risk.get("reasoning", ""),
                "hub_id": hub_id,
                "locker_unit": locker_unit,
                "p2p_match_order_id": (
                    buyers.get("best_match", {}).get("order_id")
                    if buyers.get("match_found") else None
                )
            })
        else:
            risk_summary = {
                "fraud_probability": fraud.get("fraud_probability"),
                "expected_loss":     risk.get("expected_loss"),
                "condition_score":   cond_score,
                "item_value":        value,
                "hard_deny_triggered": risk.get("hard_deny_triggered"),
            }
            await self._dispatch("escalate_to_human", {
                "return_id": return_id,
                "escalation_reason": risk.get("reasoning", "Risk threshold exceeded."),
                "risk_summary": risk_summary,
                "ai_recommendation": (
                    f"Item value ${value:.2f} CAD, fraud probability "
                    f"{fraud.get('fraud_probability', 0):.1%}. "
                    f"Recommend full physical inspection before processing refund."
                ),
                "priority": "high" if value > 300 else "normal"
            })

        return {"trace": self.trace, "summary": "Mock agent completed all processing steps."}

    async def run(self, context: dict) -> dict:
        """
        Main agent loop — uses real Claude API or zero-cost mock (USE_MOCK_AGENT=true).
        """
        if settings.USE_MOCK_AGENT:
            return await self.run_mock(context)

        messages = [{
            "role": "user",
            "content": (
                f"Process this return request:\n\n"
                f"Return ID:       {context['return_id']}\n"
                f"Customer ID:     {context['customer_id']}\n"
                f"Order ID:        {context['order_id']}\n"
                f"Product ID:      {context['product_id']}\n"
                f"Product:         {context['product_name']}\n"
                f"Category:        {context['product_category']}\n"
                f"Item Value:      ${context['item_value']:.2f} CAD\n"
                f"Size:            {context.get('size_variant', 'N/A')}\n"
                f"Weight:          {context.get('weight_grams', 500)}g\n"
                f"Liquidation Rate:{context.get('liquidation_rate', 0.20)}\n"
                f"Return Reason:   {context['reason_text']}\n"
                f"Media URLs:      {json.dumps(context['media_urls'])}\n"
                f"Returner Location: lat={context['returner_lat']}, lng={context['returner_lng']}\n\n"
                f"Begin assessment. Start with analyze_item_condition and "
                f"get_customer_trust_score in parallel."
            )
        }]

        for _turn in range(settings.AGENT_MAX_TURNS):
            response = client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                break

            if response.stop_reason == "tool_use":
                tool_blocks = [b for b in response.content if b.type == "tool_use"]

                # Run parallel if multiple tools requested simultaneously
                if len(tool_blocks) > 1:
                    tasks = [self._dispatch(b.name, b.input) for b in tool_blocks]
                    results = await asyncio.gather(*tasks)
                else:
                    results = [await self._dispatch(tool_blocks[0].name, tool_blocks[0].input)]

                tool_results = [
                    {
                        "type": "tool_result",
                        "tool_use_id": b.id,
                        "content": json.dumps(r)
                    }
                    for b, r in zip(tool_blocks, results)
                ]
                messages.append({"role": "user", "content": tool_results})

        # Extract summary from final text block
        summary = ""
        for block in reversed(messages[-1]["content"] if isinstance(messages[-1]["content"], list) else []):
            if hasattr(block, "text"):
                summary = block.text
                break

        return {"trace": self.trace, "summary": summary}
