# Neighbourhood Arbitrage Engine — MVP

AI-native reverse logistics: e-commerce returns rerouted P2P via Smart Lockers.

---

## Quickstart — Docker Compose (Recommended)

> No Python or Node.js setup needed. Just Docker Desktop.

### Demo Mode — zero cost, no API key required

```bash
git clone https://github.com/KartikJaswal1111/neighborhood-arbitrage.git
cd neighborhood-arbitrage
docker compose up --build
```

Opens at **http://localhost:3000**

The backend seeds demo data automatically on first start.

---

### Real AI Mode — live Claude claude-sonnet-4-6 agent

```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here \
USE_MOCK_AGENT=false \
USE_MOCK_VISION=false \
docker compose up --build
```

> **Windows (PowerShell):**
> ```powershell
> $env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
> $env:USE_MOCK_AGENT="false"
> $env:USE_MOCK_VISION="false"
> docker compose up --build
> ```

---

## Demo Scenarios

| Scenario | Item | Expected Outcome |
|---|---|---|
| A — Happy Path | Nike Air Max 270, $140 | Instant $140 refund + Smart Locker P2P |
| B — Escalation | Sony WH-1000XM5, $380 | AI stops — human review queue |
| C — No Match | Patagonia Jacket Size XS | Warehouse route — refund on delivery |

### Demo Flow

1. Open **http://localhost:3000**
2. Click **"Run This Scenario"** on any of the 3 cards
3. Watch the AI agent trace build in real-time
4. For Scenario A (happy path): click **"Simulate Locker Drop-off"**
5. Visit **/admin** to see the human review queue (Scenario B)

---

## Manual Setup (Alternative to Docker)

<details>
<summary>Click to expand</summary>

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — add your Anthropic API key if using real AI mode

python seed_data.py
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

</details>

---

## Architecture

```
User Browser
    │
    ▼
Next.js 14 + Tailwind (Vercel / localhost:3000)
    │  REST API calls
    ▼
FastAPI (Railway / localhost:8000)
    │
    ▼
Agent Orchestrator  ──►  Claude claude-sonnet-4-6 (Anthropic SDK)
    │                         tool-calling loop (up to 12 turns)
    ▼
10 Specialised Tools
  ├── Vision: analyze_item_condition
  ├── Trust:  get_customer_trust_score
  ├── Risk:   calculate_fraud_risk · calculate_refund_risk
  ├── Geo:    search_nearby_buyers · find_nearest_hub
  ├── Action: allocate_locker · issue_instant_refund
  │           generate_routing_instruction
  └── HITL:   escalate_to_human  ◄── AI hard-stops here
    │
    ▼
SQLite + SQLAlchemy ORM (arbitrage.db)
```

**Tech Stack**

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, Tailwind CSS |
| Backend | Python 3.11, FastAPI |
| AI Agent | Claude claude-sonnet-4-6 via Anthropic SDK |
| Database | SQLite (SQLAlchemy ORM) |
| Containers | Docker + Docker Compose |

---

## The Human Boundary

The AI is explicitly stopped — `issue_instant_refund` is never called — when any threshold is breached:

| Rule | Threshold |
|---|---|
| Expected financial loss | > $15.00 |
| Fraud probability | > 75% |
| Item value | > $500.00 |
| Item condition score | < 30 / 100 |

These thresholds are business-configured parameters in `config.py`, **not AI decisions**.
