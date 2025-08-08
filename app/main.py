#!/usr/bin/env python3
"""
MCP Tools Server: Automatically discovers and registers all Tool classes in the tools/ directory
Supports both stdio (DEV) and SSE (PROD) transports based on ENV variable.
"""

from fastmcp import FastMCP
from dotenv import load_dotenv
from tools.recommendations import GetHotelRecommendationsTool
from datetime import datetime

# Load environment variables first
load_dotenv()

app = FastMCP(name="Hotel Recommendations", port=8000, host="0.0.0.0")

@app.tool
def get_hotel_recommendations(address: str, date: str, guests: int, room_type: str, additional_comments: str) -> str:
    """
    Generates hotel recommendations near the provided location.
    """

    tool = GetHotelRecommendationsTool(
        address=address,
        date=date,
        guests=guests,
        room_type=room_type,
        additional_comments=additional_comments,
    )
    return tool.run()

@app.tool
def get_current_date() -> str:
    """
    Returns the current date in the format YYYY-MM-DD.
    """
    return datetime.now().strftime("%Y-%m-%d")


@app.tool
def get_instructions_on_tool_calling() -> str:
    """
    Instructions on how to call the tools
    """
    return """
    You are a helpful assistant that can help with hotel recommendations.
    You can use the following tools to get hotel recommendations:
    - get_hotel_recommendations
    - get_current_date

    The get_hotel_recommendations tool takes in the following parameters:
    - address: str (Required)
    - date: str (Required)
    - guests: int (Required) > 0
    - room_type: str (Optional)
    - additional_comments: str (Optional)

    # IMPORTANT: REQUIRED FIELDS MUST BE PROVIDED BY THE USER. DO NOT MAKE UP ANYTHING.

    The get_current_date tool returns the current date in the format YYYY-MM-DD.

    Example:
    - address: "1 Market St, San Francisco, CA"
    - date: "2025-08-20"
    - guests: 2

    Output Format: You will be given top N hotels in a list format. Return the response back to the user in a readable format,
    and summarize the reviews of a hotel instead of showing all reviews.
    """


@app.resource("instructions://app", description="Instructions on how to call the tools")
def instructions() -> str:
    """
    Instructions on how to call the tools
    """
    return """
    You are a helpful assistant that can help with hotel recommendations.
    You can use the following tools to get hotel recommendations:
    - get_hotel_recommendations
    - get_current_date

    The get_hotel_recommendations tool takes in the following parameters:
    - address: str (Required)
    - date: str (Required)
    - guests: int (Required) > 0
    - room_type: str (Optional)
    - additional_comments: str (Optional)

    # IMPORTANT: REQUIRED FIELDS MUST BE PROVIDED BY THE USER. DO NOT MAKE UP ANYTHING.

    The get_current_date tool returns the current date in the format YYYY-MM-DD.

    Example:
    - address: "1 Market St, San Francisco, CA"
    - date: "2025-08-20"
    - guests: 2

    Output Format: You will be given top N hotels in a list format. Return the response back to the user in a readable format,
    and summarize the reviews of a hotel instead of showing all reviews.
    """


if __name__ == "__main__":
    app.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")
