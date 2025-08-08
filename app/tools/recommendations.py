from __future__ import annotations

from agency_swarm.tools import BaseTool
from pydantic import Field
from dotenv import load_dotenv

from models.schemas import ReservationRequest
from services.recommender import recommend_hotels

load_dotenv()


class GetHotelRecommendationsTool(BaseTool):
    """
    Generates hotel recommendations near the provided location.
    Results are enriched with Google Maps (distance, rating, total reviews, price level, up to 5 reviews).

    - address: str (Required)
    - date: str (Required)
    - guests: int (Required) > 0
    - room_type: str (Optional)
    - additional_comments: str (Optional)

    # IMPORTANT: REQUIRED FIELDS MUST BE PROVIDED BY THE USER. DO NOT MAKE UP ANYTHING.
    """

    address: str | None = Field(
        ..., description="Specific address for proximity filtering"
    )
    date: str = Field(
        ..., description="Target date in ISO format (YYYY-MM-DD)"
    )
    guests: int = Field(
        ..., description="Number of guests"
    )
    room_type: str | None = Field(
        None, description="Preferred room type"
    )
    additional_comments: str | None = Field(
        None, description="Any additional comments or special considerations"
    )

    def run(self):
        """
        Generates hotel recommendations and returns a readable summary.
        """
        try:
            # Build domain request (Pydantic will coerce ISO date string)
            reservation = ReservationRequest(
                address=self.address,
                date=self.date,
                guests=self.guests,
                room_type=self.room_type,
                additional_comments=self.additional_comments,
            )

            hotels = recommend_hotels(reservation)
            # Return the raw hotel data as a string (e.g., JSON string)
            import json
            return json.dumps([h.model_dump() if hasattr(h, "model_dump") else h.dict() for h in hotels], default=str, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(e)
            return "Unable to get recommendations. Error: " + str(e)


if __name__ == "__main__":
    tool = GetHotelRecommendationsTool(
        address="1 Market St, San Francisco, CA",
        date="2025-08-20",
        guests=2,
        room_type="double",
        additional_comments="High floor preferred",
    )
    print(tool.run())