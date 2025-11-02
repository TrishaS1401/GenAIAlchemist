import os
import uuid
import socket
from dotenv import load_dotenv

# Load environment variables from 'env' file before any other imports
load_dotenv('env')

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from agent_runner import call_agent_sync, call_agent_stream

# Force IPv4 to avoid connectivity issues
original_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4_only

# Configuration
APP_NAME = "agents"

# Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

def generate_session_id():
    """Generate a unique session ID."""
    return str(uuid.uuid4())


@app.route('/getSession', methods=['POST'])
def get_session():
    """
    Generate a new session ID (just a UUID, not initialized yet).
    Session will be initialized on first /chat call.
    Request body: {"user_id": "optional_user_id"}
    """
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', str(uuid.uuid4()))
        
        # Just generate a session ID, don't initialize
        session_id = generate_session_id()
        
        return jsonify({
            "session_id": session_id,
            "user_id": user_id,
            "app_name": APP_NAME,
            "message": "Session ID created. Will be initialized on first chat."
        }), 201
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to create session ID"
        }), 500


@app.route('/chat', methods=['POST'])
def chat():
    """
    Send a message to the agent and get a response.
    Session is initialized on FIRST call, then reused on subsequent calls.
    
    Request body: {
        "query": "your message",
        "session_id": "required_session_id",
        "user_id": "optional_user_id"
    }
    Returns: JSON with response and session_id
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'query' not in data:
            return jsonify({
                "error": "Missing required field 'query'"
            }), 400
        
        if 'session_id' not in data:
            return jsonify({
                "error": "Missing required field 'session_id'. Call /getSession first."
            }), 400
        
        query = data['query']
        session_id = data['session_id']
        user_id = data.get('user_id', 'user')
        
        # Call agent - will initialize session on first call, reuse on subsequent
        response_text = call_agent_sync(query, user_id, session_id, app_name=APP_NAME)
        
        # Return JSON response
        return jsonify({
            "response": response_text,
            "session_id": session_id,
            "user_id": user_id
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to process chat request"
        }), 500


@app.route('/chatStream', methods=['POST'])
def chat_stream():
    """
    Send a message to the agent and get a streaming response.
    Session is initialized on FIRST call, then reused on subsequent calls.
    
    Request body: {
        "query": "your message",
        "session_id": "required_session_id",
        "user_id": "optional_user_id"
    }
    Returns: Server-Sent Events (SSE) stream
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'query' not in data:
            return "Error: Missing required field 'query'", 400
        
        if 'session_id' not in data:
            return "Error: Missing required field 'session_id'. Call /getSession first.", 400
        
        query = data['query']
        session_id = data['session_id']
        user_id = data.get('user_id', 'user')
        
        def generate():
            """Generator function for streaming response"""
            try:
                # Will initialize session on first call, reuse on subsequent
                for chunk in call_agent_stream(query, user_id, session_id, app_name=APP_NAME):
                    # Send as Server-Sent Events format
                    yield f"data: {chunk}\n\n"
                
                # Send end signal
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                yield f"data: Error: {str(e)}\n\n"
        
        # Return streaming response
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "app_name": APP_NAME
    }), 200


if __name__ == "__main__":
    print("="*70)
    print("Flask API Server Starting")
    print("="*70)
    print(f"App Name: {APP_NAME}")
    print(f"Endpoints:")
    print(f"  POST /getSession  - Get session ID (not initialized)")
    print(f"  POST /chat        - Send message (initializes on first call)")
    print(f"  POST /chatStream  - Send message streaming (initializes on first call)")
    print(f"  GET  /health      - Health check")
    print("="*70)
    print("USAGE:")
    print("  1. Call /getSession to get a session_id")
    print("  2. Use that session_id in /chat (initialized on FIRST use)")
    print("  3. Keep using same session_id for conversation continuity")
    print("="*70)
    
    app.run(host='0.0.0.0', port=5001, debug=True)