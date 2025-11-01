from google.adk import Agent
from google.genai.types import GenerateContentConfig
import types
from . import prompt


from tools.amadeus_hotels import (
    search_hotels_tool,
    get_hotel_details_tool
)

hotel_booking_agent = Agent(
    model="gemini-2.5-flash",
    name="hotel_booking_agent",
    description="Comprehensive agent for complete hotel booking workflow: search hotels and get detailed information",
    instruction=prompt.HOTEL_BOOKING_INSTR,
    output_key="hotel_search_results",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    tools=[
        search_hotels_tool,
        get_hotel_details_tool
    ],
    generate_content_config=GenerateContentConfig(
        temperature=0.1,
        top_p=0.8,
        response_mime_type="text/plain"
    )
)
