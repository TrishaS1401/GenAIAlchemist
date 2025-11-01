# Imports for the clarifying agent
from google.adk.agents import LlmAgent
from .prompt import clarify_agent_prompt


# # --- Define required trip details as a constant ---
# REQUIRED_TRIP_DETAILS = [
#     "destination", 
#     "start_date", 
#     "end_date", 
#     "number_of_travelers",
#     "trip_type",
#     "budget",
#     "stay_type",
#     "travel_preference"
# ]

# # Format the list for use in prompts
# REQUIRED_FIELDS_LIST = "\n".join([f"- {field}" for field in REQUIRED_TRIP_DETAILS])


# # --- Single Clarifying Agent (no loop needed) ---
# clarifying_agent = LlmAgent(
#     model='gemini-2.5-flash',
#     name='clarifying_agent',
#     description='Gathers essential details for a travel itinerary by asking the user questions in a conversational manner.',
#     instruction=f"""{clarify_agent_prompt}

# **Required Information to Collect:**
# {REQUIRED_FIELDS_LIST}

# **Current State:**
# - destination: {{destination}}
# - start_date: {{start_date}}
# - end_date: {{end_date}}
# - number_of_travelers: {{number_of_travelers}}
# - trip_type: {{trip_type}}
# - budget: {{budget}}
# - stay_type: {{stay_type}}
# - travel_preference: {{travel_preference}}

# **Your Task:**
# 1. Review the current state above to identify which fields are missing or empty
# 2. If any required fields are missing:
#    - Ask the user for that information in a friendly, conversational way
#    - Ask for 1-2 pieces of information at a time (don't overwhelm the user)
#    - Store the user's responses in the session state using the exact field names listed above
#    - Continue the conversation until you have all required details

# 3. If ALL required fields have valid, non-empty values:
#    - Thank the user and indicate you have all the information needed
#    - Summarize the trip details briefly
#    - Signal that you're ready to proceed with itinerary planning

# **Important Guidelines:**
# - Be natural and conversational - this is a dialogue, not a form
# - If a user provides multiple pieces of information at once, capture all of them
# - If information is unclear, ask for clarification
# - Store each piece of information in session state immediately upon receiving it
# - Always check the current state before asking questions to avoid asking for information you already have

# Output your conversational response to the user.
# """,
#     output_key="clarification_response"
# )

# Imports for the clarifying agent and loop agent
from google.adk.agents.llm_agent import Agent
from google.adk.agents.loop_agent import LoopAgent

# Define the single-use clarifying agent
clarifing_agent = Agent(
    model='gemini-2.5-flash',
    name='clarifing_agent',
    description='Gathers essential details for a travel itinerary.',
    instruction=clarify_agent_prompt,
)
