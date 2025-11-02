import asyncio
import socket
from google.adk.runners import InMemoryRunner
from google.genai import types
from agents.agent import root_agent

# Force IPv4 to avoid connectivity issues
original_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4_only

# Global runner instance
runner = InMemoryRunner(
    agent=root_agent,
    app_name='agents',
)

# Track session mappings: client_session_id -> (runner_session_id, user_id)
_session_mappings = {}


async def initialize_session_with_runner(user_id: str, client_session_id: str, app_name: str = 'agents'):
    """
    Initialize a session with the runner.
    The runner creates its own session_id, we map it to the client's session_id.
    """
    # Create session - let runner generate its own ID
    session = await runner.session_service.create_session(
        app_name=app_name,
        user_id=user_id
    )
    runner_session_id = session.id
    
    print(f"Created runner session: {runner_session_id} for client session: {client_session_id}")
    
    # Initialize by running a dummy message
    content = types.Content(
        role='user',
        parts=[types.Part.from_text(text="initialize")]
    )
    
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=runner_session_id,
            new_message=content,
        ):
            # Consume all initialization events
            pass
    except Exception as e:
        print(f"Session initialization warning: {e}")
    
    # Store the mapping
    _session_mappings[client_session_id] = {
        'runner_session_id': runner_session_id,
        'user_id': user_id
    }
    
    return runner_session_id


async def get_runner_session_id(user_id: str, client_session_id: str, app_name: str = 'agents'):
    """
    Get the runner's session_id for a client's session_id.
    Initialize if not found.
    """
    # Check if we have a mapping
    if client_session_id in _session_mappings:
        mapping = _session_mappings[client_session_id]
        if mapping['user_id'] == user_id:
            runner_session_id = mapping['runner_session_id']
            print(f"Using existing session: {runner_session_id} for client session: {client_session_id}")
            return runner_session_id
    
    # No mapping found, initialize new session
    print(f"Initializing new session for client session: {client_session_id}")
    return await initialize_session_with_runner(user_id, client_session_id, app_name)


def run_agent(query: str, user_id: str, runner_session_id: str):
    """
    Runs the agent with a query and returns the response (synchronous).
    Uses the runner's actual session_id.
    """
    content = types.Content(
        role='user',
        parts=[types.Part.from_text(text=query)]
    )
    
    response_text = ""
    
    # Run agent synchronously
    for event in runner.run(
        user_id=user_id,
        session_id=runner_session_id,
        new_message=content,
    ):
        # Collect text from events
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
    
    return response_text


def run_agent_stream(query: str, user_id: str, runner_session_id: str):
    """
    Runs the agent with a query and yields response chunks (generator for streaming).
    Uses the runner's actual session_id.
    """
    content = types.Content(
        role='user',
        parts=[types.Part.from_text(text=query)]
    )
    
    # Run agent synchronously and yield text chunks
    for event in runner.run(
        user_id=user_id,
        session_id=runner_session_id,
        new_message=content,
    ):
        # Yield text from events as they arrive
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    yield part.text


def call_agent_sync(query: str, user_id: str, session_id: str, agent_instance=None, app_name: str = 'agents'):
    """
    Calls the agent with a query and returns the response (synchronous).
    Uses client's session_id, maps to runner's session_id internally.
    Initializes session on first call, reuses on subsequent calls.
    """
    # Get or initialize the runner's session_id
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        runner_session_id = loop.run_until_complete(
            get_runner_session_id(user_id, session_id, app_name)
        )
    finally:
        loop.close()
    
    # Run agent with runner's session_id
    return run_agent(query, user_id, runner_session_id)


def call_agent_stream(query: str, user_id: str, session_id: str, agent_instance=None, app_name: str = 'agents'):
    """
    Calls the agent with a query and yields response chunks (generator for streaming).
    Uses client's session_id, maps to runner's session_id internally.
    Initializes session on first call, reuses on subsequent calls.
    """
    # Get or initialize the runner's session_id
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        runner_session_id = loop.run_until_complete(
            get_runner_session_id(user_id, session_id, app_name)
        )
    finally:
        loop.close()
    
    # Run agent and yield chunks
    yield from run_agent_stream(query, user_id, runner_session_id)


async def call_agent_async(query: str, user_id: str, session_id: str, agent_instance=None, app_name: str = 'agents'):
    """
    Calls the agent with a query and returns the response (asynchronous).
    Uses client's session_id, maps to runner's session_id internally.
    """
    # Get or initialize the runner's session_id
    runner_session_id = await get_runner_session_id(user_id, session_id, app_name)
    
    # Prepare message
    content = types.Content(
        role='user',
        parts=[types.Part.from_text(text=query)]
    )
    
    response_text = ""
    
    # Run agent asynchronously
    async for event in runner.run_async(
        user_id=user_id,
        session_id=runner_session_id,
        new_message=content,
    ):
        # Collect text from events
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
    
    return {
        "response": response_text,
        "session_id": session_id,  # Return client's session_id
        "user_id": user_id
    }