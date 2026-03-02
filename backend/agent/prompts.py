"""Category-specific vision inspection prompts."""

BASE_SCHEMA = """
Return ONLY valid JSON with this exact structure:
{
  "overall_score": <integer 0-100>,
  "grade": <"A"|"B+"|"B"|"C+"|"C"|"D"|"F">,
  "confidence": <float 0.0-1.0>,
  "issues": [
    {"location": "<string>", "severity": "<none|minor|moderate|severe>",
     "type": "<string>", "description": "<string>"}
  ],
  "authenticity": {
    "logo_check": "<pass|fail|inconclusive>",
    "stitching_check": "<pass|fail|inconclusive>",
    "label_check": "<pass|fail|inconclusive>",
    "overall": "<authentic|suspicious|counterfeit>"
  },
  "resale_eligible": <true|false>,
  "inspector_notes": "<concise summary string>"
}
"""

FOOTWEAR_PROMPT = """You are a certified footwear condition inspector for an AI returns system.
Analyze these images of returned footwear carefully.

Inspect in this order:
1. Upper material — scratches, creases, tears, stains, scuffs
2. Sole — separation, wear pattern, structural integrity, grip remaining
3. Heel — counter collapse, scuffs, breakdown
4. Insole — yellowing, compression marks, odor indicators, cleanliness
5. Laces — present, original, clean condition
6. Authenticity — logo placement, stitching quality, label format, serial number

Scoring guide:
  90-100 (A)  — Essentially unworn, no visible use
  75-89  (B)  — Light use only, minor cosmetic marks acceptable
  60-74  (C)  — Moderate visible wear, functional
  45-59  (D)  — Heavy wear or significant defects
  0-44   (F)  — Damaged, non-functional, or authenticity concern

""" + BASE_SCHEMA

APPAREL_PROMPT = """You are a certified apparel condition inspector for an AI returns system.
Analyze these images of returned clothing carefully.

Inspect in this order:
1. Fabric integrity — pilling, tears, fraying, thinning
2. Stains — location, size, type (oil/food/ink), severity
3. Seams — intact, no separation, stitching quality
4. Zippers/buttons — functional, all present
5. Color — fading, discoloration, bleach marks
6. Odor indicators — visible signs of heavy use (underarm areas, collar)
7. Tags — present, not removed, original

Scoring guide:
  90-100 (A)  — New or like-new condition
  75-89  (B)  — Very light wear, clean
  60-74  (C)  — Moderate wear, minor stains acceptable
  45-59  (D)  — Visible stains, significant wear
  0-44   (F)  — Heavily stained, damaged, or unwearable

""" + BASE_SCHEMA

ELECTRONICS_PROMPT = """You are a certified electronics condition inspector for an AI returns system.
Analyze these images of returned electronics carefully.

Inspect in this order:
1. Screen/display — scratches, cracks, dead pixels, burn-in
2. Body — dents, cracks, scratches, missing pieces
3. Ports — damage, corrosion, obstruction
4. Cables/accessories — all present and undamaged
5. Buttons/controls — all present and appear functional
6. Labels — serial number visible, not tampered
7. Packaging — original box present (note if missing)

Scoring guide:
  90-100 (A)  — Near mint, no visible marks
  80-89  (B+) — Very minor cosmetic marks only
  70-79  (B)  — Light scratches, fully functional
  55-69  (C)  — Moderate cosmetic damage
  40-54  (D)  — Significant damage or missing accessories
  0-39   (F)  — Major damage or suspected parts swap

""" + BASE_SCHEMA

MOCK_RESPONSES = {
    "footwear": {
        "overall_score": 84,
        "grade": "B+",
        "confidence": 0.91,
        "issues": [
            {
                "location": "left heel",
                "severity": "minor",
                "type": "scuff",
                "description": "Surface scuff approximately 2cm, non-structural"
            },
            {
                "location": "right sole",
                "severity": "none",
                "type": "wear_check",
                "description": "Minimal sole wear, grip intact"
            }
        ],
        "authenticity": {
            "logo_check": "pass",
            "stitching_check": "pass",
            "label_check": "pass",
            "overall": "authentic"
        },
        "resale_eligible": True,
        "inspector_notes": "Item in good condition with minor cosmetic wear on left heel. All authenticity checks passed. Suitable for P2P resale."
    },
    "electronics_bad": {
        "overall_score": 41,
        "grade": "D",
        "confidence": 0.87,
        "issues": [
            {
                "location": "headband",
                "severity": "moderate",
                "type": "scratch",
                "description": "Deep scratches on headband, possible drop damage"
            },
            {
                "location": "left ear cup",
                "severity": "severe",
                "type": "crack",
                "description": "Crack visible on left ear cup housing"
            },
            {
                "location": "cable port",
                "severity": "moderate",
                "type": "damage",
                "description": "USB-C port appears damaged/bent"
            }
        ],
        "authenticity": {
            "logo_check": "pass",
            "stitching_check": "inconclusive",
            "label_check": "pass",
            "overall": "suspicious"
        },
        "resale_eligible": False,
        "inspector_notes": "Significant damage detected. Cracked housing and damaged port indicate drop damage. Condition does not support claimed 'like new' description."
    },
    "apparel": {
        "overall_score": 71,
        "grade": "C+",
        "confidence": 0.88,
        "issues": [
            {
                "location": "right sleeve cuff",
                "severity": "minor",
                "type": "pilling",
                "description": "Light pilling on right cuff, normal for fleece"
            }
        ],
        "authenticity": {
            "logo_check": "pass",
            "stitching_check": "pass",
            "label_check": "pass",
            "overall": "authentic"
        },
        "resale_eligible": True,
        "inspector_notes": "Good overall condition. Minor pilling typical of fleece fabric. Clean, no stains. All zippers functional."
    }
}


def get_inspection_prompt(category: str, product_metadata: dict) -> str:
    prompts = {
        "footwear": FOOTWEAR_PROMPT,
        "apparel": APPAREL_PROMPT,
        "electronics": ELECTRONICS_PROMPT,
    }
    base = prompts.get(category, FOOTWEAR_PROMPT)
    product_info = f"\nProduct being inspected: {product_metadata.get('name', 'Unknown')} by {product_metadata.get('brand', 'Unknown')}\n"
    return product_info + base


def get_mock_response(category: str, scenario: str = "normal") -> dict:
    if category == "electronics":
        return MOCK_RESPONSES["electronics_bad"]
    elif category == "apparel":
        return MOCK_RESPONSES["apparel"]
    return MOCK_RESPONSES["footwear"]
