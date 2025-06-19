from crewai import Agent
from langchain_google_genai import GoogleGenerativeAI
from langchain.tools import Tool
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import tools
from crew.tools.search_tools.search_engine import smart_search_tool
from crew.tools.pdf_tools import update_embeddings_tool

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def create_agents():
    """Create the two main agents for SLC Assistant System"""
    
    # Create simplified tools
    search_tool = Tool(
        name="search_tool",
        func=smart_search_tool,
        description="Vector similarity search tool for finding any information from SLC documents. Can search by assistant names, initials, teaching procedures, exam rules, or any related content."
    )
    
    embed_tool = Tool(
        name="update_embeddings_tool",
        func=update_embeddings_tool,
        description="Tool for updating PDF embeddings in Supabase database"
    )
    
    # Agent 1: SLC Assistant Agent (Simplified)
    assistant_agent = Agent(
        role='SLC Assistant Agent',
        goal='Membantu asisten SLC dengan memberikan informasi yang akurat dan natural tentang data asisten, prosedur mengajar, dan prosedur pengawasan ujian',
        backstory='''Saya adalah asisten virtual untuk Software Laboratory Center (SLC) yang berpengalaman dan ramah. 
        
        Saya memiliki akses ke database lengkap SLC dan dapat membantu dengan:
        1. Mencari informasi data asisten (berdasarkan nama, initial, atau detail lainnya)
        2. Memberikan informasi prosedur dan aturan mengajar
        3. Memberikan informasi prosedur dan aturan pengawasan ujian
        
        Ketika memberikan informasi, saya selalu:
        - Memberikan jawaban yang natural dan conversational
        - Mengolah data mentah menjadi informasi yang mudah dipahami  
        - Menyesuaikan tone dan gaya bicara yang ramah dan professional
        - Memberikan konteks dan penjelasan tambahan jika diperlukan
        - Tidak hanya copy-paste data mentah, tapi mengolahnya menjadi jawaban yang bermakna
        
        Jika ada pertanyaan di luar ketiga hal ini, saya akan dengan jujur mengatakan bahwa saya tidak tahu dan menyarankan untuk menghubungi coordinator SLC.''',
        allow_delegation=False,
        verbose=True,
        tools=[search_tool],
        llm=GoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.9, google_api_key=GOOGLE_API_KEY)
    )
    
    # Agent 2: Update Embed Supabase Agent  
    embed_agent = Agent(
        role='Update Embed Supabase Agent',
        goal='Mengelola dan memperbarui embeddings PDF di database Supabase untuk memastikan informasi terbaru tersedia',
        backstory='''Saya adalah agent yang bertanggung jawab untuk mengelola embeddings PDF di database Supabase.
        Tugas saya adalah memproses file PDF dan menyimpan embeddings-nya ke dalam tabel documents_rig_rag
        dengan dimensi 768 untuk pencarian semantik yang optimal.
        
        Saya dapat memproses file PDF individual atau semua file PDF sekaligus sesuai kebutuhan.''',
        allow_delegation=False,
        verbose=True,
        tools=[embed_tool],
        llm=GoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.1, google_api_key=GOOGLE_API_KEY)
    )
    
    return assistant_agent, embed_agent 