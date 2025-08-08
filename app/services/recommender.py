from __future__ import annotations
from typing import List, Dict, Any

from core.config import get_settings
from models.schemas import ReservationRequest, Hotel, Coordinates, Review
from services.gemini import generate_hotel_candidates
from services.maps import geocode, find_hotel_by_name_near, distance_km_between, find_hotels_text_search, find_hotel_by_name_and_address_near

settings = get_settings()


def _coalesce_location_text(res: ReservationRequest) -> str | None:
    return res.address


def _format_price_level(price_level: int | None) -> str | None:
    if price_level is None:
        return None
    mapping = {0: "$", 1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}
    return mapping.get(price_level, None)


def _normalize_price_per_night(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # Convert numeric price to a displayable string
        return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)
    if isinstance(value, str):
        return value
    return str(value)


def _to_hotel_from_maps(d: Dict[str, Any], ref_lat: float, ref_lng: float) -> Hotel:
    hotel_lat = d.get("lat")
    hotel_lng = d.get("lng")
    dist = None
    coords = None
    if isinstance(hotel_lat, (float, int)) and isinstance(hotel_lng, (float, int)):
        dist = distance_km_between(ref_lat, ref_lng, float(hotel_lat), float(hotel_lng))
        coords = Coordinates(lat=float(hotel_lat), lng=float(hotel_lng))
    reviews = []
    for rv in (d.get("reviews") or [])[:5]:
        reviews.append(Review(
            author=rv.get("author"),
            rating=rv.get("rating"),
            text=rv.get("text"),
            relative_time=rv.get("relative_time"),
        ))
    return Hotel(
        name=d.get("name", "Unknown"),
        address=d.get("address"),
        phone=d.get("phone"),
        email=None,
        rating=d.get("rating"),
        total_reviews=d.get("total_reviews"),
        price_per_night=_format_price_level(d.get("price_level")),
        amenities=None,
        room_features=None,
        location=coords,
        distance_km=round(dist, 2) if isinstance(dist, float) else None,
        verified=coords is not None,
        reviews=reviews or None,
    )


def recommend_hotels(reservation: ReservationRequest) -> List[Hotel]:
    ref_text = _coalesce_location_text(reservation)
    ref_coords = geocode(ref_text) if ref_text else None

    try:
        gemini_hotels: List[Dict[str, Any]] = generate_hotel_candidates(reservation)
    except Exception:
        gemini_hotels = []

    print(gemini_hotels)


    verified: List[Hotel] = []

    if not gemini_hotels and ref_coords:
        ref_lat, ref_lng = ref_coords
        maps_only = find_hotels_text_search(ref_lat, ref_lng, settings.fallback_max_candidates)
        hotels = [_to_hotel_from_maps(m, ref_lat, ref_lng) for m in maps_only]
        hotels.sort(key=lambda h: (h.distance_km if h.distance_km is not None else 1e9, -(h.rating or 0)))
        return hotels[: settings.max_results]
    

    for item in gemini_hotels:
        name = (item.get("name") or "").strip()
        if not name:
            continue

        address = item.get("address")
        # Ignore Gemini values for phone, email, rating; will fetch from Maps for accuracy
        phone = None
        email = None
        rating = None
        price_per_night = item.get("price_per_night")
        amenities = item.get("amenities")
        room_features = item.get("room_features")

        distance_km: float | None = None
        lat_lng = None

        if ref_coords:
            ref_lat, ref_lng = ref_coords
            # Use name+address for better uniqueness and accuracy
            details = find_hotel_by_name_and_address_near(name, address, ref_lat, ref_lng) or find_hotel_by_name_near(name, ref_lat, ref_lng)
            if details and details.get("lat") is not None and details.get("lng") is not None:
                hotel_lat = float(details["lat"])  # type: ignore[index]
                hotel_lng = float(details["lng"])  # type: ignore[index]
                lat_lng = Coordinates(lat=hotel_lat, lng=hotel_lng)
                distance_km = distance_km_between(ref_lat, ref_lng, hotel_lat, hotel_lng)
                address = details.get("address") or address
                phone = details.get("phone")
                rating = details.get("rating")
                if price_per_night is None:
                    price_per_night = _format_price_level(details.get("price_level"))

        reviews = []
        if details and details.get("reviews"):
            for rv in details.get("reviews", [])[:5]:
                reviews.append(Review(
                    author=rv.get("author"),
                    rating=rv.get("rating"),
                    text=rv.get("text"),
                    relative_time=rv.get("relative_time"),
                ))
        hotel = Hotel(
            name=name,
            address=address,
            phone=phone,
            email=email,
            rating=rating,
            total_reviews=(details or {}).get("total_reviews") if 'details' in locals() else None,
            price_per_night=_normalize_price_per_night(price_per_night),
            amenities=amenities,
            room_features=room_features,
            location=lat_lng,
            distance_km=round(distance_km, 2) if isinstance(distance_km, float) else None,
            verified=lat_lng is not None,
            reviews=reviews or None,
        )
        verified.append(hotel)

    def sort_key(h: Hotel):
        return (
            0 if h.verified else 1,
            h.distance_km if h.distance_km is not None else 1e9,
            -(h.rating or 0),
        )

    verified.sort(key=sort_key)
    return verified[: settings.max_results]
