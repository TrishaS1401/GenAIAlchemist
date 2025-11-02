# Part of agent.py --> Follow https://google.github.io/adk-docs/get-started/quickstart/ to learn the setup

from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.tools.tool_context import ToolContext
from agents.orchestrators.inspiration_agent.agent import inspiration_agent
from agents.orchestrators.planning_agent.agent import planning_agent
# from itinery_generation_app.sub_agents.booking.agent import booking_agent
# from itinery_generation_app.sub_agents.in_trip.agent import in_trip_agent
# from itinery_generation_app.sub_agents.post_trip.agent import post_trip_agent
# from itinery_generation_app.sub_agents.pre_trip.agent import pre_trip_agent
from tools.memory import _load_precreated_itinerary
import os

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
COMPLETION_PHRASE = "Response is adequate and ready for user."

# --- Exit Loop Tool ---
def exit_refinement_loop(tool_context: ToolContext):
    """Call this function when the response meets quality standards and no further refinement is needed."""
    print(f"  [Tool Call] exit_refinement_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    return {}

# --- Step 1: Main Travel Orchestrator Agent ---
# This agent routes to specialized sub-agents and generates the initial response
travel_orchestrator_agent = LlmAgent(
    model=GEMINI_MODEL,
    name="TravelOrchestratorAgent",
    description="Routes user requests to specialized travel sub-agents and generates comprehensive responses",
    instruction="""You are a highly capable and friendly Travel Concierge. Your primary goal is to manage and orchestrate the entire travel lifecycle for a user, from initial inspiration to post-trip feedback.

Your responsibilities include:
1.  **Understanding the User's Needs**: Analyze the user's requests to determine the correct phase of their travel journey (e.g., just dreaming, actively planning, already on their trip).
2.  **Delegating to Sub-Agents**: Based on the user's intent, activate the appropriate sub-agent(s) to handle specific tasks. You must route the request to the correct specialized agent.
3.  **Synthesizing Information**: Receive information back from your sub-agents and present a coherent, helpful, and comprehensive response to the user.
4.  **Maintaining Context**: Use the provided memory to recall previous interactions and itinerary details to provide a seamless experience.

Use your available tools and sub-agents to fulfill the user's request. Always be helpful, informative, and proactive in assisting with travel-related inquiries.

Output your complete response to the user's query.""",
    sub_agents=[
        inspiration_agent,
        planning_agent
    ],
    before_agent_callback=_load_precreated_itinerary,
    output_key="generated_response"  # Store initial response in state
)

# --- Step 2a: Critic Agent (Inside Refinement Loop) ---
# Reviews the generated response and provides feedback
critic_agent = LlmAgent(
    model=GEMINI_MODEL,
    name="ResponseCriticAgent",
    description="Reviews travel responses for quality, completeness, and accuracy",
    instruction=f"""You are an Expert Travel Response Reviewer. Your task is to critically evaluate the travel concierge response for quality and completeness.

**User's Original Query:**
Review the conversation history to identify the user's original query that this response is addressing.

**Generated Response:**
{{generated_response}}

**Review Criteria:**
1.  **Relevance**: Does the response directly address the user's query?
2.  **Completeness**: Are all aspects of the query adequately covered?
3.  **Accuracy**: Is the information accurate and up-to-date (based on what's provided)?
4.  **Clarity**: Is the response clear, well-organized, and easy to understand?
5.  **Helpfulness**: Does the response provide actionable information or next steps?
6.  **Tone**: Is the tone friendly, professional, and appropriate for a travel concierge?

**Task:**
IF you identify 1-3 *clear and actionable* improvements that would significantly enhance the response quality:
    Provide specific, concise suggestions for improvement. Focus on the most impactful changes.
    Output *only* your critique and suggestions.

ELSE IF the response adequately addresses all criteria and is ready for the user:
    Respond *exactly* with: "{COMPLETION_PHRASE}"
    Do not add any additional text.

Output only your critique OR the exact completion phrase.""",
    output_key="critique_feedback"
)

# --- Step 2b: Refiner Agent (Inside Refinement Loop) ---
# Either refines the response based on critique or exits the loop
refiner_agent = LlmAgent(
    model=GEMINI_MODEL,
    name="ResponseRefinerAgent",
    description="Refines the travel response based on critic feedback or exits if complete",
    instruction=f"""You are a Travel Response Refinement Specialist. Your task is to improve the response or exit the refinement process.

**User's Original Query:**
Review the conversation history to identify the user's original query that this response is addressing.

**Current Response:**
{{generated_response}}

**Critic's Feedback:**
{{critique_feedback}}

**Task:**
Analyze the 'Critic's Feedback' carefully.

IF the feedback is *exactly* "{COMPLETION_PHRASE}":
    You MUST call the 'exit_refinement_loop' function immediately. Do NOT output any text.

ELSE (the feedback contains actionable suggestions):
    Carefully apply ALL the critic's suggestions to improve the response. Maintain the helpful and friendly tone.
    Address each point raised in the critique.
    Output *only* the complete, refined response text.

Do not add explanations about changes made. Either call the exit_refinement_loop function OR output the refined response.""",
    tools=[exit_refinement_loop],
    output_key="generated_response"  # Overwrites the response with refined version
)

# --- Step 2: Create Refinement Loop ---
# This loop runs critic → refiner repeatedly until response is adequate
refinement_loop = LoopAgent(
    name="ResponseRefinementLoop",
    sub_agents=[
        critic_agent,
        refiner_agent
    ],
    max_iterations=3  # Run max 3 times as specified
)

itinery_agent = SequentialAgent(
    name="ItineraryAgentPipeline",
    sub_agents=[
        travel_orchestrator_agent,  # Generate initial response
        refinement_loop             # Refine iteratively with critic
    ],
    description="Travel concierge that generates and iteratively refines responses using critic feedback",
    before_agent_callback=_load_precreated_itinerary
)
