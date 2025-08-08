from __future__ import annotations
from typing import Optional, Dict, Any, Tuple, List
import math
from tenacity import retry, stop_after_attempt, wait_exponential
import googlemaps

from core.config import get_settings

settings = get_settings()
_gmaps = googlemaps.Client(key=settings.google_maps_api_key)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=6))
def geocode(query: str) -> Optional[Tuple[float, float]]:
    if not query:
        return None
    res = _gmaps.geocode(query)
    if not res:
        return None
    loc = res[0]["geometry"]["location"]
    return (loc["lat"], loc["lng"])  # type: ignore[index]

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=6))
def find_hotel_by_name_near(name: str, near_lat: float, near_lng: float) -> Optional[Dict[str, Any]]:
    if not name:
        return None
    query = f"{name} hotel"
    res = _gmaps.places(query=query, location=(near_lat, near_lng), radius=settings.maps_radius_meters, type="lodging")
    candidates = res.get("results", []) if isinstance(res, dict) else []
    if not candidates:
        return None
    best = max(candidates, key=lambda c: c.get("rating", 0))
    place_id = best.get("place_id")
    try:
        details = _gmaps.place(place_id=place_id, fields=[
            "name",
            "formatted_address",
            "geometry",
            "formatted_phone_number",
            "rating",
            "user_ratings_total",
            "price_level",
            "website",
            "reviews",
        ])
    except Exception as e:
        print(str(e))
        return None
    result = details.get("result", {})
    loc = result.get("geometry", {}).get("location", {})
    result_reviews = result.get("reviews", []) if isinstance(result, dict) else []
    reviews = []
    for rv in result_reviews[:5]:
        reviews.append({
            "author": rv.get("author_name"),
            "rating": rv.get("rating"),
            "text": rv.get("text"),
            "relative_time": rv.get("relative_time_description"),
        })
    return {
        "name": result.get("name") or best.get("name"),
        "address": result.get("formatted_address"),
        "phone": result.get("formatted_phone_number"),
        "rating": result.get("rating"),
        "total_reviews": result.get("user_ratings_total"),
        "lat": loc.get("lat"),
        "lng": loc.get("lng"),
        "price_level": result.get("price_level"),
        "website": result.get("website"),
        "reviews": reviews,
    }


def distance_km_between(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    return _haversine_km(lat1, lng1, lat2, lng2)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=6))
def find_hotel_by_name_and_address_near(name: str, address: Optional[str], near_lat: float, near_lng: float) -> Optional[Dict[str, Any]]:
    if not name:
        return None
    query = f"{name} {address}" if address else f"{name} hotel"
    res = _gmaps.places(query=query, location=(near_lat, near_lng), radius=settings.maps_radius_meters, type="lodging")
    candidates = res.get("results", []) if isinstance(res, dict) else []
    if not candidates:
        return None
    # Prefer the first candidate as Google sorts by relevance
    best = candidates[0]
    place_id = best.get("place_id")
    details = _gmaps.place(place_id=place_id, fields=[
        "name",
        "formatted_address",
        "geometry",
        "formatted_phone_number",
        "rating",
        "user_ratings_total",
        "price_level",
        "website",
        "reviews",
    ])
    result = details.get("result", {})
    loc = result.get("geometry", {}).get("location", {})
    result_reviews = result.get("reviews", []) if isinstance(result, dict) else []
    reviews = []
    for rv in result_reviews[:5]:
        reviews.append({
            "author": rv.get("author_name"),
            "rating": rv.get("rating"),
            "text": rv.get("text"),
            "relative_time": rv.get("relative_time_description"),
        })
    return {
        "name": result.get("name") or best.get("name"),
        "address": result.get("formatted_address"),
        "phone": result.get("formatted_phone_number"),
        "rating": result.get("rating"),
        "total_reviews": result.get("user_ratings_total"),
        "lat": loc.get("lat"),
        "lng": loc.get("lng"),
        "price_level": result.get("price_level"),
        "website": result.get("website"),
        "reviews": reviews,
    }

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=6))
def find_hotels_text_search(near_lat: float, near_lng: float, max_results: int) -> List[Dict[str, Any]]:
    res = _gmaps.places(query="hotel", location=(near_lat, near_lng), radius=settings.maps_radius_meters, type="lodging")
    candidates = res.get("results", []) if isinstance(res, dict) else []
    hotels: List[Dict[str, Any]] = []
    for c in candidates:
        place_id = c.get("place_id")
        if not place_id:
            continue
        details = _gmaps.place(place_id=place_id, fields=["name","formatted_address","geometry","formatted_phone_number","rating","user_ratings_total","price_level","website","reviews"]) \
            .get("result", {})
        loc = details.get("geometry", {}).get("location", {})
        result_reviews = details.get("reviews", []) if isinstance(details, dict) else []
        reviews = []
        for rv in result_reviews[:5]:
            reviews.append({
                "author": rv.get("author_name"),
                "rating": rv.get("rating"),
                "text": rv.get("text"),
                "relative_time": rv.get("relative_time_description"),
            })
        hotels.append({
            "name": details.get("name") or c.get("name"),
            "address": details.get("formatted_address"),
            "phone": details.get("formatted_phone_number"),
            "rating": details.get("rating"),
            "total_reviews": details.get("user_ratings_total"),
            "lat": loc.get("lat"),
            "lng": loc.get("lng"),
            "price_level": details.get("price_level"),
            "website": details.get("website"),
            "reviews": reviews,
        })
        if len(hotels) >= max_results:
            break
    return hotels
