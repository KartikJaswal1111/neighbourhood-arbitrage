"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from api.routes import returns, admin, hubs
from config import settings

app = FastAPI(
    title="Neighbourhood Arbitrage Engine",
    description="AI-native reverse logistics — P2P rerouting via Smart Locker network",
    version="1.0.0-mvp"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(returns.router)
app.include_router(admin.router)
app.include_router(hubs.router)


@app.on_event("startup")
def startup():
    init_db()
    print("✓ Database initialized")
    print("✓ Neighbourhood Arbitrage Engine running")


@app.get("/health")
def health():
    return {"status": "ok", "service": "Neighbourhood Arbitrage Engine"}


@app.get("/api/v1/demo/scenarios")
def get_demo_scenarios():
    """Pre-configured demo scenarios for the presentation."""
    return {
        "scenarios": [
            {
                "id": "happy_path",
                "title": "Scenario A — Happy Path",
                "subtitle": "Smart Locker P2P Match + Instant Refund",
                "description": "Sarah returns Nike Air Max 270. AI finds James 7.8km away. Smart Locker confirms. Instant refund.",
                "badge": "P2P Match",
                "badge_color": "green",
                "customer_id": "cust-sarah-001",
                "order_id": "order-return-nike-001",
                "reason_text": "The shoe runs a half size small and the right heel has a minor scuff from trying them on indoors.",
                "media_urls": [
                    "https://static.nike.com/a/images/t_PDP_1728_v1/f_auto,q_auto:eco/99486859-0ff3-46b4-949b-2d16af2ad421/AIR+MAX+270.png"
                ],
                "returner_lat": 43.6512,
                "returner_lng": -79.3832,
                "expected_outcome": "Instant $140 refund + Smart Locker drop-off instruction"
            },
            {
                "id": "escalation",
                "title": "Scenario B — Human Escalation",
                "subtitle": "AI Stops — Hard Rule Triggered",
                "description": "Mike returns Sony headphones. Fraud flags detected. Expected loss $142. AI escalates.",
                "badge": "Escalated",
                "badge_color": "red",
                "customer_id": "cust-mike-003",
                "order_id": "order-return-sony-002",
                "reason_text": "These headphones stopped working after 2 days. They seem defective.",
                "media_urls": [
                    "https://www.sony.com/image/5d02da5df552836db894cead731a2f78?fmt=png-alpha&wid=440"
                ],
                "returner_lat": 43.7731,
                "returner_lng": -79.2580,
                "expected_outcome": "AI stops — human review queue created with full evidence"
            },
            {
                "id": "no_match",
                "title": "Scenario C — No P2P Match",
                "subtitle": "Graceful Warehouse Fallback",
                "description": "Sarah returns Patagonia jacket Size XS. No nearby buyers. Routed to warehouse.",
                "badge": "Warehouse Route",
                "badge_color": "yellow",
                "customer_id": "cust-sarah-001",
                "order_id": "order-return-pata-003",
                "reason_text": "The jacket is great quality but Size XS is slightly too large for me. I need a XXS.",
                "media_urls": [
                    "https://www.patagonia.com/dw/image/v2/BDJB_PRD/on/demandware.static/-/Sites-patagonia-master/default/dw5f1f04d5/images/hi-res/25551_NKGR.jpg"
                ],
                "returner_lat": 43.6512,
                "returner_lng": -79.3832,
                "expected_outcome": "Warehouse route — refund on confirmed delivery"
            }
        ]
    }
