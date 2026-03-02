from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = "mock-key-not-needed"
    DATABASE_URL: str = "sqlite:///./arbitrage.db"
    CLAUDE_MODEL: str = "claude-sonnet-4-6"
    USE_MOCK_VISION: bool = False
    USE_MOCK_AGENT: bool = False   # True = zero API cost, deterministic demo
    AGENT_MAX_TURNS: int = 12

    # Comma-separated list of allowed CORS origins.
    # In production set this to your Vercel frontend URL, e.g.:
    #   CORS_ORIGINS=https://your-app.vercel.app
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Refund thresholds — set by business, not AI
    REFUND_AUTO_APPROVE_MAX_LOSS: float = 15.00
    REFUND_HARD_DENY_FRAUD_PROB: float = 0.75
    REFUND_HARD_DENY_ITEM_VALUE: float = 500.00
    REFUND_MIN_CONDITION_SCORE: int = 30

    # Geo matching
    GEO_INITIAL_RADIUS_KM: float = 50.0
    GEO_EXPANDED_RADIUS_KM: float = 200.0
    HUB_SEARCH_RADIUS_KM: float = 5.0

    # Category-specific P2P condition thresholds
    P2P_MIN_SCORE_FOOTWEAR: int = 75
    P2P_MIN_SCORE_APPAREL: int = 65
    P2P_MIN_SCORE_ELECTRONICS: int = 88

    # Locker model reduces risk multiplier (physical confirmation = less risk)
    LOCKER_RISK_MULTIPLIER: float = 0.4

    # Liquidation recovery rates by category
    LIQUIDATION_RATE_FOOTWEAR: float = 0.20
    LIQUIDATION_RATE_APPAREL: float = 0.15
    LIQUIDATION_RATE_ELECTRONICS: float = 0.35

    class Config:
        env_file = ".env"


settings = Settings()
