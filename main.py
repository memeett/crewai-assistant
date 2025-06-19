from crewai import Crew, Process
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import time

from config.agents import create_agents
from config.tasks import create_task

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase.table('documents_rig_rag').select("*").limit(1).execute()
    print("Successfully connected to Supabase")
except Exception as e:
    print(f"Error connecting to Supabase: {str(e)}")
    raise

# Conversation memory
conversation_memory = []

def add_to_memory(user_input: str, assistant_response: str):
    """Add conversation to memory"""
    conversation_memory.append({
        "user": user_input,
        "assistant": assistant_response,
        "timestamp": time.time()
    })
    if len(conversation_memory) > 10:
        conversation_memory.pop(0)

def get_conversation_context() -> str:
    """Get conversation context for agents"""
    if not conversation_memory:
        return "Ini adalah percakapan pertama."
    
    context = "Konteks percakapan sebelumnya:\n"
    for i, conv in enumerate(conversation_memory[-3:], 1):
        context += f"{i}. User: {conv['user']}\n   Assistant: {conv['assistant']}\n"
    return context

def run_interactive_chat():
    """Run interactive chat mode"""
    print("\nSLC Assistant System")
    print("=" * 50)
    print("Halo! Saya adalah asisten virtual untuk Software Laboratory Center.")
    print("\nSaya dapat membantu Anda dengan:")
    print("1. Mencari informasi asisten SLC (sebutkan initial)")
    print("2. Prosedur dan aturan mengajar")  
    print("3. Prosedur dan aturan pengawasan ujian")
    print("4. Update embeddings PDF (ketik 'embed [nama_file.pdf]' atau 'embed all')")
    print("\nKetik 'quit' atau 'exit' untuk keluar.\n")
    
    try:
        assistant_agent, embed_agent = create_agents()
    except Exception as e:
        print(f"Error creating agents: {str(e)}")
        return
    
    while True:
        try:
            user_input = input("Anda: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'keluar', 'q']:
                print("\nTerima kasih telah menggunakan SLC Assistant System!")
                break
            
            if not user_input:
                continue
            
            context = get_conversation_context()
            
            # untuk membantu gemini memilih agent y
            query_lower = user_input.lower()
            if any(keyword in query_lower for keyword in ['embed', 'update']):
                task = create_task(embed_agent, user_input, context)
                crew = Crew(
                    agents=[embed_agent],
                    tasks=[task],
                    verbose=False,
                    process=Process.sequential
                )
            else:
                task = create_task(assistant_agent, user_input, context)
                crew = Crew(
                    agents=[assistant_agent],
                    tasks=[task],
                    verbose=False,
                    process=Process.sequential
                )
            
            print("\nSedang memproses...")
            result = crew.kickoff()
            
            response = str(result)
            print(f"\nAssistant: {response}\n")
            
            add_to_memory(user_input, response)
            
        except KeyboardInterrupt:
            print("\n\nTerima kasih telah menggunakan SLC Assistant System!")
            break
        except Exception as e:
            print(f"\nTerjadi kesalahan: {str(e)}")
            print("Silakan coba lagi.\n")

if __name__ == "__main__":
    run_interactive_chat() 