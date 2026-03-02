from sqlalchemy import (
    create_engine, Column, String, Float,
    Integer, JSON, DateTime, Text, Boolean, BigInteger
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime, timezone
import uuid

from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def new_id():
    return str(uuid.uuid4())


def now():
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────
# Core entities
# ─────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"
    id         = Column(String, primary_key=True, default=new_id)
    name       = Column(String, nullable=False)
    email      = Column(String, unique=True, nullable=False)
    geo_lat    = Column(Float, nullable=False)
    geo_lng    = Column(Float, nullable=False)
    created_at = Column(DateTime, default=now)


class Product(Base):
    __tablename__ = "products"
    id                       = Column(String, primary_key=True, default=new_id)
    sku                      = Column(String, unique=True, nullable=False)
    name                     = Column(String, nullable=False)
    brand                    = Column(String)
    category                 = Column(String, nullable=False)   # footwear|apparel|electronics
    unit_price               = Column(Float, nullable=False)
    weight_grams             = Column(Float, default=500.0)
    liquidation_rate         = Column(Float, default=0.20)
    min_p2p_condition_score  = Column(Integer, default=75)
    created_at               = Column(DateTime, default=now)


class Order(Base):
    __tablename__ = "orders"
    id           = Column(String, primary_key=True, default=new_id)
    customer_id  = Column(String, nullable=False)
    product_id   = Column(String, nullable=False)
    unit_price   = Column(Float, nullable=False)
    status       = Column(String, default="pending")   # pending|fulfilled|matched_p2p|cancelled
    geo_lat      = Column(Float, nullable=False)
    geo_lng      = Column(Float, nullable=False)
    size_variant = Column(String)
    color_variant= Column(String)
    created_at   = Column(DateTime, default=now)


class CustomerTrustProfile(Base):
    __tablename__ = "customer_trust_profiles"
    customer_id       = Column(String, primary_key=True)
    lifetime_orders   = Column(Integer, default=0)
    lifetime_returns  = Column(Integer, default=0)
    return_rate       = Column(Float, default=0.0)
    fraud_flags       = Column(Integer, default=0)
    trust_score       = Column(Integer, default=75)    # 0-100
    p2p_accepted_count= Column(Integer, default=0)
    last_updated      = Column(DateTime, default=now)


# ─────────────────────────────────────────
# Smart Locker network
# ─────────────────────────────────────────

class CommunityHub(Base):
    __tablename__ = "community_hubs"
    id             = Column(String, primary_key=True, default=new_id)
    name           = Column(String, nullable=False)
    hub_type       = Column(String)          # convenience_store|transit|dedicated
    partner_name   = Column(String)
    address        = Column(Text, nullable=False)
    geo_lat        = Column(Float, nullable=False)
    geo_lng        = Column(Float, nullable=False)
    total_lockers  = Column(Integer, default=10)
    active_lockers = Column(Integer, default=10)
    is_active      = Column(Boolean, default=True)
    operating_hours= Column(JSON)
    created_at     = Column(DateTime, default=now)


class SmartLocker(Base):
    __tablename__ = "smart_lockers"
    id               = Column(String, primary_key=True, default=new_id)
    hub_id           = Column(String, nullable=False)
    unit_number      = Column(String, nullable=False)   # "Locker #3"
    status           = Column(String, default="available")
    # available|reserved|occupied|maintenance
    size_category    = Column(String, default="medium")
    has_camera       = Column(Boolean, default=True)
    has_weight_sensor= Column(Boolean, default=True)
    last_heartbeat   = Column(DateTime, default=now)


class LockerAllocation(Base):
    __tablename__ = "locker_allocations"
    id                   = Column(String, primary_key=True, default=new_id)
    return_id            = Column(String, nullable=False)
    locker_id            = Column(String, nullable=False)
    hub_id               = Column(String, nullable=False)
    dropoff_qr_hash      = Column(String, unique=True, nullable=False)
    pickup_qr_hash       = Column(String)                # generated after dropoff
    status               = Column(String, default="awaiting_dropoff")
    # awaiting_dropoff|dropoff_confirmed|awaiting_pickup|pickup_confirmed|expired
    verified_weight_g    = Column(Float)
    expected_weight_g    = Column(Float)
    weight_match         = Column(Boolean)
    camera_sku_match     = Column(Boolean)
    camera_confidence    = Column(Float)
    locker_ai_score      = Column(Integer)
    dropoff_window_hrs   = Column(Integer, default=48)
    pickup_window_hrs    = Column(Integer, default=24)
    allocated_at         = Column(DateTime, default=now)
    dropoff_confirmed_at = Column(DateTime)
    pickup_confirmed_at  = Column(DateTime)


# ─────────────────────────────────────────
# Return lifecycle
# ─────────────────────────────────────────

class Return(Base):
    __tablename__ = "returns"
    id                   = Column(String, primary_key=True, default=new_id)
    customer_id          = Column(String, nullable=False)
    order_id             = Column(String, nullable=False)
    product_id           = Column(String, nullable=False)
    status               = Column(String, default="initiated")
    # initiated|analyzing|awaiting_locker_dropoff|refund_issued|
    # escalated|warehouse_routed|no_match_routed|error
    reason_raw           = Column(Text)
    reason_category      = Column(String)
    condition_score      = Column(Integer)
    condition_grade      = Column(String)
    detected_issues      = Column(JSON)
    authenticity_result  = Column(JSON)
    fraud_probability    = Column(Float)
    fraud_signals        = Column(JSON)
    fraud_reasoning      = Column(Text)
    hub_id               = Column(String)
    locker_id            = Column(String)
    p2p_match_order_id   = Column(String)
    match_distance_km    = Column(Float)
    refund_decision      = Column(String)
    refund_reasoning     = Column(Text)
    expected_loss        = Column(Float)
    refund_amount        = Column(Float)
    transaction_id       = Column(String)
    routing_decision     = Column(String)
    routing_instructions = Column(JSON)
    agent_trace          = Column(JSON)
    created_at           = Column(DateTime, default=now)
    updated_at           = Column(DateTime, default=now)


class HumanReviewQueue(Base):
    __tablename__ = "human_review_queue"
    id                = Column(String, primary_key=True, default=new_id)
    return_id         = Column(String, nullable=False)
    escalation_reason = Column(Text, nullable=False)
    risk_summary      = Column(JSON)
    ai_recommendation = Column(Text)
    priority          = Column(String, default="normal")  # low|normal|high|urgent
    status            = Column(String, default="pending")  # pending|in_review|resolved
    reviewer_decision = Column(String)
    reviewer_notes    = Column(Text)
    resolved_at       = Column(DateTime)
    created_at        = Column(DateTime, default=now)


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
