from flask import Flask, request, jsonify
from flask_cors import CORS
from crewai import Crew, Process
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import time
from datetime import datetime

from config.agents import create_agents
from config.tasks import create_task

load_dotenv()

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    print("📋 Please copy config_template.env to .env and fill in your actual values")
    print("💡 You need to configure:")
    print("   - SUPABASE_URL: Your Supabase project URL")
    print("   - SUPABASE_KEY: Your Supabase anon key")
    print("   - GOOGLE_API_KEY: Your Google API key")
    raise ValueError("Missing required environment variables. Please create .env file.")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    test_response = supabase.table('documents_rig_rag').select("*").limit(1).execute()
    print("✅ Successfully connected to Supabase")
    print(f"📊 Database has {len(test_response.data)} records (showing 1)")
except Exception as e:
    print(f"❌ Error connecting to Supabase: {str(e)}")
    print("💡 Please check your SUPABASE_URL and SUPABASE_KEY in .env file")
    raise

try:
    assistant_agent, embed_agent = create_agents()
    print("Successfully created agents")
except Exception as e:
    print(f"Error creating agents: {str(e)}")
    assistant_agent, embed_agent = None, None

conversation_sessions = {}

def add_to_memory(session_id: str, user_input: str, assistant_response: str):
    """Add conversation to memory for a specific session"""
    if session_id not in conversation_sessions:
        conversation_sessions[session_id] = []
    
    conversation_sessions[session_id].append({
        "user": user_input,
        "assistant": assistant_response,
        "timestamp": time.time()
    })
    
    if len(conversation_sessions[session_id]) > 10:
        conversation_sessions[session_id].pop(0)

def get_conversation_context(session_id: str) -> str:
    """Get conversation context for a specific session"""
    if session_id not in conversation_sessions or not conversation_sessions[session_id]:
        return "Ini adalah percakapan pertama."
    
    context = "Konteks percakapan sebelumnya:\n"
    for i, conv in enumerate(conversation_sessions[session_id][-3:], 1):
        context += f"{i}. User: {conv['user']}\n   Assistant: {conv['assistant']}\n"
    return context

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "success",
        "message": "SLC Assistant API is running",
        "timestamp": datetime.now().isoformat(),
        "agents_status": "ready" if assistant_agent and embed_agent else "not_ready"
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        user_input = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        
        if not user_input:
            return jsonify({
                "status": "error",
                "message": "Message cannot be empty"
            }), 400
        
        if not assistant_agent or not embed_agent:
            return jsonify({
                "status": "error",
                "message": "Agents not properly initialized"
            }), 500
        
        context = get_conversation_context(session_id)
        
        query_lower = user_input.lower()
        if any(keyword in query_lower for keyword in ['embed', 'update']):
            selected_agent = embed_agent
            task = create_task(embed_agent, user_input, context)
            crew = Crew(
                agents=[embed_agent],
                tasks=[task],
                verbose=False,
                process=Process.sequential
            )
        else:
            selected_agent = assistant_agent
            task = create_task(assistant_agent, user_input, context)
            crew = Crew(
                agents=[assistant_agent],
                tasks=[task],
                verbose=False,
                process=Process.sequential
            )
        
        result = crew.kickoff()
        response = str(result)
        
        add_to_memory(session_id, user_input, response)
        
        return jsonify({
            "status": "success",
            "message": response,
            "session_id": session_id,
            "agent_used": selected_agent.role if selected_agent else "unknown",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/embed', methods=['POST'])
def embed_documents():
    """Endpoint specifically for embedding documents"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        filename = data.get('filename', 'all')
        session_id = data.get('session_id', 'default')
        
        if not embed_agent:
            return jsonify({
                "status": "error",
                "message": "Embed agent not properly initialized"
            }), 500
        
        embed_command = f"embed {filename}"
        context = get_conversation_context(session_id)
        
        task = create_task(embed_agent, embed_command, context)
        crew = Crew(
            agents=[embed_agent],
            tasks=[task],
            verbose=False,
            process=Process.sequential
        )
        
        result = crew.kickoff()
        response = str(result)
        
        add_to_memory(session_id, embed_command, response)
        
        return jsonify({
            "status": "success",
            "message": response,
            "filename": filename,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session_history(session_id):
    """Get conversation history for a specific session"""
    try:
        if session_id not in conversation_sessions:
            return jsonify({
                "status": "success",
                "history": [],
                "session_id": session_id,
                "message": "No conversation history found for this session"
            })
        
        return jsonify({
            "status": "success",
            "history": conversation_sessions[session_id],
            "session_id": session_id,
            "count": len(conversation_sessions[session_id]),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def clear_session(session_id):
    """Clear conversation history for a specific session"""
    try:
        if session_id in conversation_sessions:
            del conversation_sessions[session_id]
            message = f"Session {session_id} cleared successfully"
        else:
            message = f"Session {session_id} not found"
        
        return jsonify({
            "status": "success",
            "message": message,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    print("\n🚀 Starting SLC Assistant API Server...")
    print("📋 Available endpoints:")
    print("   GET  /              - Health check")
    print("   POST /api/chat      - Main chat endpoint")
    print("   POST /api/embed     - Embed documents")
    print("   GET  /api/sessions/<id> - Get session history")
    print("   DELETE /api/sessions/<id> - Clear session")
    print("\n🌐 Access the API at: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 