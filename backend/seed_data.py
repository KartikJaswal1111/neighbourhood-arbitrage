"""
Seed the database with realistic demo data.
Run once: python seed_data.py
Creates 3 demo scenarios for the Wealthsimple application.
"""
from database import (
    SessionLocal, init_db,
    Customer, Product, Order, CustomerTrustProfile,
    CommunityHub, SmartLocker
)


def seed():
    init_db()
    db = SessionLocal()

    # ── Clear existing data ──────────────────────────────────────────────
    for table in [SmartLocker, CommunityHub, CustomerTrustProfile,
                  Order, Product, Customer]:
        db.query(table).delete()
    db.commit()

    # ── Customers ────────────────────────────────────────────────────────
    # Sarah: high trust returner (downtown Toronto)
    sarah = Customer(
        id="cust-sarah-001",
        name="Sarah Chen",
        email="sarah.chen@email.com",
        geo_lat=43.6512,
        geo_lng=-79.3832
    )
    # James: nearby buyer (Midtown)
    james = Customer(
        id="cust-james-002",
        name="James Wilson",
        email="james.wilson@email.com",
        geo_lat=43.6590,
        geo_lng=-79.3801
    )
    # Mike: low trust, fraud history (Scarborough)
    mike = Customer(
        id="cust-mike-003",
        name="Mike Torres",
        email="mike.torres@email.com",
        geo_lat=43.7731,
        geo_lng=-79.2580
    )
    # Anna: second buyer (North York)
    anna = Customer(
        id="cust-anna-004",
        name="Anna Patel",
        email="anna.patel@email.com",
        geo_lat=43.7615,
        geo_lng=-79.4111
    )
    db.add_all([sarah, james, mike, anna])

    # ── Trust Profiles ───────────────────────────────────────────────────
    db.add_all([
        CustomerTrustProfile(
            customer_id="cust-sarah-001",
            lifetime_orders=24,
            lifetime_returns=3,
            return_rate=0.125,
            fraud_flags=0,
            trust_score=82,
            p2p_accepted_count=1
        ),
        CustomerTrustProfile(
            customer_id="cust-james-002",
            lifetime_orders=11,
            lifetime_returns=1,
            return_rate=0.09,
            fraud_flags=0,
            trust_score=78,
            p2p_accepted_count=2
        ),
        CustomerTrustProfile(
            customer_id="cust-mike-003",
            lifetime_orders=7,
            lifetime_returns=5,
            return_rate=0.71,
            fraud_flags=2,
            trust_score=31,
            p2p_accepted_count=0
        ),
        CustomerTrustProfile(
            customer_id="cust-anna-004",
            lifetime_orders=18,
            lifetime_returns=2,
            return_rate=0.11,
            fraud_flags=0,
            trust_score=80,
            p2p_accepted_count=0
        ),
    ])

    # ── Products ─────────────────────────────────────────────────────────
    nike = Product(
        id="prod-nike-001",
        sku="NK-AM270-BLK-10",
        name="Nike Air Max 270",
        brand="Nike",
        category="footwear",
        unit_price=140.00,
        weight_grams=412.0,
        liquidation_rate=0.20,
        min_p2p_condition_score=75
    )
    sony = Product(
        id="prod-sony-002",
        sku="SONY-WH1000XM5-BLK",
        name="Sony WH-1000XM5 Headphones",
        brand="Sony",
        category="electronics",
        unit_price=380.00,
        weight_grams=250.0,
        liquidation_rate=0.35,
        min_p2p_condition_score=88
    )
    patagonia = Product(
        id="prod-pata-003",
        sku="PATA-BTSW-GRY-XS",
        name="Patagonia Better Sweater Jacket",
        brand="Patagonia",
        category="apparel",
        unit_price=179.00,
        weight_grams=680.0,
        liquidation_rate=0.15,
        min_p2p_condition_score=65
    )
    db.add_all([nike, sony, patagonia])

    # ── Orders to be returned ────────────────────────────────────────────
    # Scenario A: Sarah returns her Nike shoe
    db.add(Order(
        id="order-return-nike-001",
        customer_id="cust-sarah-001",
        product_id="prod-nike-001",
        unit_price=140.00,
        status="fulfilled",
        geo_lat=43.6512,
        geo_lng=-79.3832,
        size_variant="10",
        color_variant="Black"
    ))
    # Scenario B: Mike returns Sony headphones (fraud case)
    db.add(Order(
        id="order-return-sony-002",
        customer_id="cust-mike-003",
        product_id="prod-sony-002",
        unit_price=380.00,
        status="fulfilled",
        geo_lat=43.7731,
        geo_lng=-79.2580,
        size_variant="N/A",
        color_variant="Black"
    ))
    # Scenario C: Sarah returns Patagonia jacket (no nearby match)
    db.add(Order(
        id="order-return-pata-003",
        customer_id="cust-sarah-001",
        product_id="prod-pata-003",
        unit_price=179.00,
        status="fulfilled",
        geo_lat=43.6512,
        geo_lng=-79.3832,
        size_variant="XS",
        color_variant="Grey"
    ))

    # ── Pending demand pool (buyers waiting for items) ───────────────────
    # James wants Nike Air Max 270, Size 10 — very close to Sarah
    db.add(Order(
        id="order-demand-nike-001",
        customer_id="cust-james-002",
        product_id="prod-nike-001",
        unit_price=140.00,
        status="pending",
        geo_lat=43.6590,   # 7.8km from Sarah
        geo_lng=-79.3801,
        size_variant="10",
        color_variant="Black"
    ))
    # Anna wants Nike Air Max 270, Size 10 — further away
    db.add(Order(
        id="order-demand-nike-002",
        customer_id="cust-anna-004",
        product_id="prod-nike-001",
        unit_price=140.00,
        status="pending",
        geo_lat=43.7615,   # 12km from Sarah
        geo_lng=-79.4111,
        size_variant="10",
        color_variant="Black"
    ))
    # NOTE: No pending orders for Patagonia XS or Sony headphones — tests no-match & escalation paths

    # ── Community Hubs ───────────────────────────────────────────────────
    hub1 = CommunityHub(
        id="hub-001",
        name="7-Eleven King & Spadina",
        hub_type="convenience_store",
        partner_name="7-Eleven",
        address="100 King St W, Toronto, ON M5X 1A9",
        geo_lat=43.6483,
        geo_lng=-79.3845,
        total_lockers=8,
        active_lockers=6,
        is_active=True,
        operating_hours={"mon_fri": "6:00-23:00", "sat_sun": "7:00-22:00"}
    )
    hub2 = CommunityHub(
        id="hub-002",
        name="Shoppers Drug Mart Queen St",
        hub_type="convenience_store",
        partner_name="Shoppers Drug Mart",
        address="301 Queen St W, Toronto, ON M5V 2A4",
        geo_lat=43.6495,
        geo_lng=-79.3950,
        total_lockers=6,
        active_lockers=4,
        is_active=True,
        operating_hours={"mon_fri": "8:00-22:00", "sat_sun": "9:00-21:00"}
    )
    db.add_all([hub1, hub2])

    # ── Smart Lockers ────────────────────────────────────────────────────
    for i in range(1, 7):
        db.add(SmartLocker(
            id=f"locker-hub1-{i:03d}",
            hub_id="hub-001",
            unit_number=f"#{i}",
            status="available",
            size_category="medium" if i <= 4 else "large",
            has_camera=True,
            has_weight_sensor=True
        ))
    for i in range(1, 5):
        db.add(SmartLocker(
            id=f"locker-hub2-{i:03d}",
            hub_id="hub-002",
            unit_number=f"#{i}",
            status="available",
            size_category="medium",
            has_camera=True,
            has_weight_sensor=True
        ))

    db.commit()
    db.close()
    print("✓ Database seeded with 3 demo scenarios")
    print("  Scenario A — Happy Path:    Sarah returns Nike Air Max 270")
    print("  Scenario B — Escalation:    Mike returns Sony WH-1000XM5")
    print("  Scenario C — No Match:      Sarah returns Patagonia jacket")


if __name__ == "__main__":
    seed()
