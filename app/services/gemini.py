import json
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from core.config import get_settings
from models.schemas import ReservationRequest

settings = get_settings()

_system = (
    "You are a helpful travel assistant. Given reservation details, generate a list of 20-25 hotel candidates near the user's provided location.\n"
    "Return ONLY valid JSON. The top-level object MUST have key 'hotels' which maps to a list of hotel objects.\n"
    "Each hotel object MUST include keys: 'name', 'address', 'phone', 'email', 'rating', 'price_per_night', 'amenities', 'room_features'.\n"
    "If unsure for a field, use null (or an empty list for list fields). Output nothing else besides the JSON."
)

_user_tmpl = (
    "Reservation Inputs:\n"
    "- Address: {address}\n"
    "- Date: {date}\n"
    "- Guests: {guests}\n"
    "- Room type: {room_type}\n"
    "- Additional comments: {additional_comments}\n\n"
    "Constraints:\n"
    f"- Provide between 20 and {settings.max_candidates} hotels.\n"
    "- Prefer hotels matching star rating, price range, and location preferences when possible.\n"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", _system),
    ("user", _user_tmpl),
])

llm = ChatGoogleGenerativeAI(
    model=settings.gemini_model,
    temperature=settings.temperature,
    google_api_key=settings.gemini_api_key,
    max_retries=1,
)

chain = prompt | llm | StrOutputParser()


def _strip_markdown_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.lstrip("`")
        first_brace = t.find("{")
        if first_brace != -1:
            t = t[first_brace:]
    if t.endswith("```"):
        last_brace = t.rfind("}")
        if last_brace != -1:
            t = t[: last_brace + 1]
    return t.strip()


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
def generate_hotel_candidates(reservation: ReservationRequest) -> List[Dict[str, Any]]:
    payload = reservation.model_dump()
    try:
        raw = chain.invoke(payload)
    except Exception as e:  # Short-circuit on quota/rate limit to trigger maps fallback
        msg = str(e)
        if "ResourceExhausted" in msg or "429" in msg or "rate" in msg.lower():
            return []
        raise
    text = _strip_markdown_fence(raw)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            data = json.loads(text[start:end+1])
        else:
            return []
    hotels = data.get("hotels", []) if isinstance(data, dict) else []
    if not isinstance(hotels, list):
        return []
    return hotels[: settings.max_candidates]
