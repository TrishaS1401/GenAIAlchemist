"""Planning agent. A pre-booking agent covering the planning part of the trip."""

from google.adk.agents import Agent, ParallelAgent, SequentialAgent, LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig
from shared_libraries import types
from . import prompt
from tools.memory import memorize
from google.adk.tools import google_search, url_context
from agents.tool_agents.transportation.flight_seat_agent.agent import flight_search_agent, flight_seat_availability_agent
from agents.tool_agents.transportation.hotel_search_agent.agent import hotel_booking_agent
from agents.tool_agents.transportation.train_search_agent.agent import train_search_agent

flight_search_wrapper = LlmAgent(
    model="gemini-2.5-flash",
    name="flight_search_wrapper",
    description="Searches for flights and stores results",
    instruction="""You are a flight search assistant.
Based on the user's travel requirements, search for available flights.
Extract the following from the session state or user context:
- origin (departure city/airport)
- destination (arrival city/airport)  
- departure_date
- return_date (if round trip)
- passengers
- travel_class

Use the flight search tools to find flights and return a summary of available options.
""",
    tools=flight_search_agent.tools if hasattr(flight_search_agent, 'tools') else [],
    output_key="flight_search_results",
)

hotel_search_wrapper = LlmAgent(
    model="gemini-2.5-flash",
    name="hotel_search_wrapper",
    description="Searches for hotels and stores results",
    instruction="""You are a hotel search assistant.
Based on the user's travel requirements, search for available hotels.
Extract the following from the session state or user context:
- destination
- check_in_date
- check_out_date
- guests
- room_type preferences

Use the hotel search tools to find hotels and return a summary of available options.
""",
    tools=hotel_booking_agent.tools if hasattr(hotel_booking_agent, 'tools') else [],
    output_key="hotel_search_results",
)

train_search_wrapper = LlmAgent(
    model="gemini-2.5-flash",
    name="train_search_wrapper",
    description="Searches for trains and stores results",
    instruction="""You are a train search assistant.
Based on the user's travel requirements, search for available trains.
Extract the following from the session state or user context:
- origin
- destination
- departure_date
- passengers
- class preferences

Use the train search tools to find trains and return a summary of available options.
""",
    tools=train_search_agent.tools if hasattr(train_search_agent, 'tools') else [],
    output_key="train_search_results",
)

# --- Parallel Search Agent ---
parallel_travel_search = ParallelAgent(
    name="parallel_travel_search",
    sub_agents=[
        flight_search_wrapper,
        hotel_search_wrapper,
        train_search_wrapper
    ],
    description="Executes flight, hotel, and train searches in parallel"
)

# --- Results Synthesis Agent ---
search_synthesis_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="search_synthesis_agent",
    description="Combines and presents parallel search results to the user",
    instruction="""You are a travel search results coordinator.
You have received search results from parallel queries:

**Flight Search Results:**
{flight_search_results}

**Hotel Search Results:**
{hotel_search_results}

**Train Search Results:**
{train_search_results}

Your task is to:
1. Combine these results into a coherent, user-friendly summary
2. Highlight the best options from each category based on price, timing, and convenience
3. Present the information in a clear, organized format
4. Note any issues or missing results

Provide a comprehensive summary that helps the user make informed decisions.
""",
    output_key="combined_search_results"
)

# --- Itinerary Agent (unchanged) ---
itinerary_agent = Agent(
    model="gemini-2.5-flash",
    name="itinerary_agent",
    description="Create and persist a structured JSON representation of the itinerary",
    instruction=prompt.ITINERARY_AGENT_INSTR,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_schema=types.Itinerary,
    output_key="itinerary",
    generate_content_config=types.json_response_config,
    tools=[google_search]
)

# --- Main Planning Agent (Modified) ---
planning_agent = Agent(
    model="gemini-2.5-flash",
    description="""Helps users with travel planning, complete a full itinerary for their vacation, finding best deals for flights and hotels.""",
    name="planning_agent",
    instruction=prompt.PLANNING_AGENT_INSTR,
    tools=[
        AgentTool(agent=parallel_travel_search),  # Use parallel search
        AgentTool(agent=train_search_agent),  # Use parallel search
        AgentTool(agent=search_synthesis_agent),  # Synthesize results
        AgentTool(agent=flight_seat_availability_agent),  # Keep for seat selection
        AgentTool(agent=itinerary_agent),
        memorize,
    ],
    generate_content_config=GenerateContentConfig(
        temperature=0.1, top_p=0.5
    )
)