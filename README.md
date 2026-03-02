# Neighbourhood Arbitrage Engine — MVP

AI-native reverse logistics: e-commerce returns rerouted P2P via Smart Lockers.
Built for Wealthsimple AI Builder application.

## Setup & Run (5 minutes)

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Add your Anthropic API key to .env

# Seed the database with demo scenarios
python seed_data.py

# Start the API server
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:3000
```

### 3. Demo Flow

1. Open http://localhost:3000
2. Click "Run This Scenario" on any of the 3 cards
3. Watch the AI agent trace build in real-time (~30s)
4. For Scenario A (happy path): click "Simulate Locker Drop-off"
5. Visit /admin to see the human review queue (Scenario B)

## Demo Scenarios

| Scenario | Item | Expected Outcome |
|---|---|---|
| A — Happy Path | Nike Air Max 270, $140 | Instant $140 refund + Smart Locker P2P |
| B — Escalation | Sony WH-1000XM5, $380 | AI stops — human review queue |
| C — No Match | Patagonia Jacket Size XS | Warehouse route — refund on delivery |

## Architecture

- **Backend**: Python FastAPI + SQLite + Anthropic SDK
- **AI**: Claude claude-sonnet-4-6 (vision + tool-calling agent)
- **Frontend**: Next.js 14 + Tailwind CSS
- **AI Pattern**: Tool-calling agent with 10 specialized tools

## The Human Boundary

AI is explicitly stopped (never calls `issue_instant_refund`) when:
- Expected financial loss > $15.00
- Fraud probability > 75%
- Item value > $500.00
- Condition score < 30

These thresholds are business-configured parameters in `config.py`, not AI decisions.
