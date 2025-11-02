import os

"""Inspiration agent. A pre-booking agent covering the ideation part of the trip."""

from shared_libraries.types import DestinationIdeas, POISuggestions, json_response_config
from agents.tool_agents.monitoring.weather_agent.agent import weather_forecast_agent
from google.adk.agents import Agent, LlmAgent, ParallelAgent, SequentialAgent
from google.adk.tools.agent_tool import AgentTool
from . import prompt
from tools.places import map_tool

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

"""Inspiration agent with parallel execution of place, POI, and weather sub-agents."""

# --- Sub-Agent 1: Place Agent ---
place_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="place_agent",
    instruction=prompt.PLACE_AGENT_INSTR,
    description="Suggests destinations based on user preferences",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_schema=DestinationIdeas,
    output_key="place_suggestions",
    generate_content_config=json_response_config,
)

# --- Sub-Agent 2: POI Agent ---
poi_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="poi_agent",
    description="Suggests activities and points of interest for destinations",
    instruction=prompt.POI_AGENT_INSTR,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    output_schema=POISuggestions,
    output_key="poi_suggestions",
    generate_content_config=json_response_config,
)

from agents.tool_agents.monitoring.weather_agent.agent import weather_forecast_agent

parallel_inspiration_agents = ParallelAgent(
    name="ParallelInspirationAgents",
    sub_agents=[
        place_agent,
        poi_agent,
        weather_forecast_agent  
    ],
    description="Runs place, POI, and weather agents concurrently for faster inspiration gathering"
)

synthesis_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="inspiration_synthesis_agent",
    description="Synthesizes place, POI, and weather information into inspiring travel recommendations",
    instruction="""You are a Creative Travel Inspiration Specialist. Your task is to synthesize information from multiple sources into an engaging, inspiring travel recommendation.

**Available Information:**

**Place Suggestions:**
{place_suggestions}

**Points of Interest & Activities:**
{poi_suggestions}

**Weather Forecast:**
{weather_data}

**Task:**
Create an inspiring, cohesive travel recommendation that:
1. Highlights the most compelling destinations from the place suggestions
2. Weaves in the activities and POIs to paint a vivid picture of the experience
3. Incorporates weather information naturally (e.g., "perfect beach weather in May")
4. Uses engaging, evocative language that inspires wanderlust
5. Provides practical next steps or suggestions for the user

Structure your response to be conversational and inspiring, not just a data dump. 
Make the user excited about their potential trip!

**CRITICAL: Base your response EXCLUSIVELY on the information provided above. Do not add external knowledge or details not present in the input summaries.**

Output only the inspiring travel recommendation.""",
    tools=[map_tool],  # Include map_tool for synthesis agent if needed
)

inspiration_agent = SequentialAgent(
    name="inspiration_agent",
    sub_agents=[
        parallel_inspiration_agents,  # Run place, POI, weather concurrently
        synthesis_agent               # Synthesize results into inspiring response
    ],
    description="A travel inspiration agent that discovers destinations, activities, and weather in parallel, then synthesizes an inspiring recommendation"
)

