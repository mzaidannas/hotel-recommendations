## Hotel Recommendations API

A FastAPI service that generates hotel recommendations using LangChain + Gemini, then verifies and ranks using Google Maps.

### Prerequisites
- Python 3.10+
- Google Gemini API key
- Google Maps API key (Places, Geocoding enabled)

### Setup
1. Create and fill `.env` from `.env.example`.
2. Install deps:
```bash
pip install -r requirements.txt
```
3. Run server:
```bash
python3 app/main.py
```


MCP Server config
```json
{
  "mcp-servers": {
    "hotel-recommendations-mcp": {
      "command": "npx",
      "args": ["mcp-remote", "http://localhost:8000/sse"]
    }
  }
}
```

Response:
- Top 10 verified hotels including distance from provided location.

### Notes
- Uses LCEL with `ChatGoogleGenerativeAI` for structured JSON generation.
- Maps verification uses Places + Geocoding and a haversine distance check.
