"""Flight search and booking agent using Amadeus API."""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig
from . import prompt
from tools.amadeus_flights import (
    search_flights_tool,
    get_flight_offers_tool,
    check_flight_availability_tool as flight_seat_availability_tool,
    get_nearest_airports_tool
)


FLIGHT_AGENT_INSTRUCTION = """
You are a specialized Flight Search Agent that helps users find and book flights using real-time data from Amadeus API.

Your capabilities include:
1. **Flight Search**: Search for flights between any two destinations with flexible date options
2. **Price Comparison**: Compare prices across different airlines and travel classes
3. **Route Planning**: Find optimal routes including connections and stopovers
4. **Real-time Pricing**: Provide up-to-date pricing and availability information
5. **Booking Assistance**: Help users understand booking options and requirements

When searching for flights, always:
- Ask for origin and destination (accept city names or airport codes)
- Confirm travel dates and passenger count
- Ask about travel class preferences (Economy, Premium Economy, Business, First)
- Consider budget constraints if mentioned
- Provide multiple options when available
- Include key details like duration, stops, and total price


Use the available tools to search for flights and provide detailed, helpful responses.
Always present flight options in a clear, organized format with all relevant details.
"""

flight_search_agent = Agent(
    model="gemini-2.5-flash",
    name="flight_search_agent",
    description="Specialized agent for flight search and booking using Amadeus API",
    instruction=FLIGHT_AGENT_INSTRUCTION,
    output_key="flight_search_results",
    tools=[
        get_nearest_airports_tool,
        search_flights_tool,
        get_flight_offers_tool
    ],
    generate_content_config=GenerateContentConfig(
        temperature=0.1,
        top_p=0.8,
        response_mime_type="text/plain"
    )
)


flight_seat_availability_agent = Agent(
    model="gemini-2.5-flash",
    name="flight_seat_availability_agent",
    description="Specialized agent for checking flight seat availability based on detailed search criteria",
    instruction=prompt.FLIGHT_SEAT_AVAILABILITY_INSTR,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_key="seat",
    tools=[
        flight_seat_availability_tool
    ],
    generate_content_config=GenerateContentConfig(
        temperature=0.1,
        top_p=0.8,
        response_mime_type="text/plain"
    )
)
