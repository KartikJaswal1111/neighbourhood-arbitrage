"""Community Hub and Smart Locker endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db, CommunityHub, SmartLocker
from agent.tools import haversine_km

router = APIRouter(prefix="/api/v1/hubs", tags=["hubs"])


@router.get("/nearby")
def get_nearby_hubs(lat: float, lng: float, radius_km: float = 5.0,
                    db: Session = Depends(get_db)):
    """Find active community hubs near a location."""
    hubs = db.query(CommunityHub).filter(CommunityHub.is_active == True).all()

    results = []
    for hub in hubs:
        dist = haversine_km(lat, lng, hub.geo_lat, hub.geo_lng)
        if dist > radius_km:
            continue
        available = db.query(SmartLocker).filter(
            SmartLocker.hub_id == hub.id,
            SmartLocker.status == "available"
        ).count()
        results.append({
            "hub_id":           hub.id,
            "name":             hub.name,
            "partner":          hub.partner_name,
            "address":          hub.address,
            "distance_km":      round(dist, 2),
            "walking_min":      int(dist * 12),
            "available_lockers":available,
            "operating_hours":  hub.operating_hours,
            "geo": {"lat": hub.geo_lat, "lng": hub.geo_lng}
        })

    results.sort(key=lambda x: x["distance_km"])
    return {"hubs": results, "count": len(results)}


@router.get("/{hub_id}/lockers")
def get_hub_lockers(hub_id: str, db: Session = Depends(get_db)):
    """Get all lockers for a specific hub."""
    lockers = db.query(SmartLocker).filter(SmartLocker.hub_id == hub_id).all()
    return {
        "hub_id": hub_id,
        "lockers": [
            {
                "locker_id":    l.id,
                "unit":         l.unit_number,
                "status":       l.status,
                "size":         l.size_category,
                "has_camera":   l.has_camera,
                "has_weight":   l.has_weight_sensor,
            }
            for l in lockers
        ]
    }
