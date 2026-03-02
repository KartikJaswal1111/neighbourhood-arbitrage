"""Tool schemas for Claude's tool-use API."""

TOOLS = [
    {
        "name": "analyze_item_condition",
        "description": (
            "Analyzes customer-submitted photos/video of the returned item. "
            "Uses computer vision to assess condition, detect defects, and verify authenticity. "
            "Returns a structured condition report with score 0-100."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "media_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Public URLs of uploaded item photos or video frames"
                },
                "product_category": {
                    "type": "string",
                    "enum": ["footwear", "apparel", "electronics"],
                    "description": "Product category — determines which inspection protocol to apply"
                },
                "product_metadata": {
                    "type": "object",
                    "description": "SKU, brand, name, and known weight for context"
                }
            },
            "required": ["media_urls", "product_category", "product_metadata"]
        }
    },
    {
        "name": "get_customer_trust_score",
        "description": (
            "Retrieves the customer's historical trust profile from our database. "
            "Includes return rate, fraud flags, trust score (0-100), and P2P history."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"}
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "calculate_fraud_risk",
        "description": (
            "Aggregates behavioral signals and item data to compute a fraud probability score. "
            "Uses rule-based signals plus LLM reasoning for the final assessment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id":      {"type": "string"},
                "order_id":         {"type": "string"},
                "item_value":       {"type": "number"},
                "product_category": {"type": "string"},
                "trust_profile":    {"type": "object"},
                "condition_score":  {"type": "integer"}
            },
            "required": ["customer_id", "order_id", "item_value", "product_category",
                         "trust_profile", "condition_score"]
        }
    },
    {
        "name": "search_nearby_buyers",
        "description": (
            "Searches pending orders for the same SKU within a geographic radius of the returner. "
            "Returns ranked P2P match candidates with projected margin recovery."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id":    {"type": "string"},
                "size_variant":  {"type": "string"},
                "returner_lat":  {"type": "number"},
                "returner_lng":  {"type": "number"},
                "condition_score": {"type": "integer"},
                "radius_km":     {"type": "number", "default": 50}
            },
            "required": ["product_id", "size_variant", "returner_lat",
                         "returner_lng", "condition_score"]
        }
    },
    {
        "name": "find_nearest_hub",
        "description": (
            "Finds the nearest active Community Hub with an available Smart Locker "
            "suitable for the item category and size."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "returner_lat":   {"type": "number"},
                "returner_lng":   {"type": "number"},
                "item_category":  {"type": "string"},
                "search_radius_km": {"type": "number", "default": 5}
            },
            "required": ["returner_lat", "returner_lng", "item_category"]
        }
    },
    {
        "name": "calculate_refund_risk",
        "description": (
            "Calculates the expected financial loss of issuing an instant refund. "
            "Applies business-configured thresholds to decide: auto_approved or escalate. "
            "When a locker is available, applies reduced risk multiplier (physical confirmation)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_value":        {"type": "number"},
                "fraud_probability": {"type": "number"},
                "condition_score":   {"type": "integer"},
                "liquidation_rate":  {"type": "number"},
                "locker_available":  {"type": "boolean", "default": False}
            },
            "required": ["item_value", "fraud_probability", "condition_score"]
        }
    },
    {
        "name": "allocate_locker",
        "description": (
            "Reserves a Smart Locker unit at the nearest Community Hub. "
            "Generates the Returner's Drop-off QR code. "
            "The Buyer QR is generated only AFTER IoT confirms physical drop-off."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "hub_id":       {"type": "string"},
                "return_id":    {"type": "string"},
                "item_weight_g": {"type": "number"},
                "return_window_hrs": {"type": "integer", "default": 48}
            },
            "required": ["hub_id", "return_id", "item_weight_g"]
        }
    },
    {
        "name": "issue_instant_refund",
        "description": (
            "Issues an instant refund to the customer's payment method. "
            "HARD RULE: Only callable when expected_loss is below threshold "
            "AND fraud_probability < 0.75 AND item_value < 500.00."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "return_id":   {"type": "string"},
                "amount":      {"type": "number"},
                "reasoning":   {"type": "string"}
            },
            "required": ["customer_id", "return_id", "amount", "reasoning"]
        }
    },
    {
        "name": "generate_routing_instruction",
        "description": (
            "Generates the physical routing instruction for the item. "
            "Routing types: community_hub_p2p | carrier_p2p | warehouse | resale_partner | liquidation"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "return_id":          {"type": "string"},
                "routing_type":       {
                    "type": "string",
                    "enum": ["community_hub_p2p", "carrier_p2p", "warehouse",
                             "resale_partner", "liquidation"]
                },
                "hub_id":             {"type": "string"},
                "locker_unit":        {"type": "string"},
                "p2p_match_order_id": {"type": "string"},
                "reasoning":          {"type": "string"}
            },
            "required": ["return_id", "routing_type", "reasoning"]
        }
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Escalates the return to a human reviewer queue. "
            "Called when AI cannot safely make an autonomous decision. "
            "AI processing stops after this call."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "return_id":         {"type": "string"},
                "escalation_reason": {"type": "string"},
                "risk_summary":      {"type": "object"},
                "ai_recommendation": {"type": "string"},
                "priority":          {
                    "type": "string",
                    "enum": ["low", "normal", "high", "urgent"]
                }
            },
            "required": ["return_id", "escalation_reason", "risk_summary",
                         "ai_recommendation", "priority"]
        }
    }
]
