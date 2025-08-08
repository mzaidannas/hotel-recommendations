from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

class UserPreferences(BaseModel):
    preferred_location: Optional[str] = None
    star_rating: Optional[int] = Field(default=None, ge=1, le=5)
    language: Optional[str] = None
    room_view: Optional[str] = None
    price_range: Optional[str] = None

class ReservationRequest(BaseModel):
    address: Optional[str] = Field(default=None, description="Specific address for proximity filtering")
    date: date
    guests: int
    room_type: Optional[str] = None
    additional_comments: Optional[str] = None

class Coordinates(BaseModel):
    lat: float
    lng: float

class Hotel(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    price_per_night: Optional[str] = None
    amenities: Optional[List[str]] = None
    room_features: Optional[List[str]] = None
    location: Optional[Coordinates] = None
    distance_km: Optional[float] = None
    verified: bool = False

class Review(BaseModel):
    author: Optional[str] = None
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    text: Optional[str] = None
    relative_time: Optional[str] = None

class Hotel(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    price_per_night: Optional[str] = None
    amenities: Optional[List[str]] = None
    room_features: Optional[List[str]] = None
    location: Optional[Coordinates] = None
    distance_km: Optional[float] = None
    verified: bool = False
    reviews: Optional[List[Review]] = None
    total_reviews: Optional[int] = None

class RecommendationsResponse(BaseModel):
    results: List[Hotel]
    total_candidates: int
    total_verified: int
    source: str = "gemini+maps"
