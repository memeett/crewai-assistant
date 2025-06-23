import os
import glob
import uuid
import time
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from tenacity import retry, stop_after_attempt, wait_exponential
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def process_pdf_file(pdf_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    pdf_reader = PdfReader(pdf_path)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    
    file_name = os.path.basename(pdf_path)
    file_path = os.path.abspath(pdf_path)
    
    documents = []
    for i, chunk in enumerate(chunks):
        doc = {
            "content": chunk,
            "metadata": {
                "source": file_name,
                "file_path": file_path,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
        }
        documents.append(doc)
    
    return documents

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_embedding(text: str, embeddings: GoogleGenerativeAIEmbeddings) -> List[float]:
    try:
        return embeddings.embed_query(text)
    except Exception as e:
        print(f"Error getting embedding: {str(e)}")
        raise

def embed_and_store_pdf(pdf_path: str) -> str:
    try:
        documents = process_pdf_file(pdf_path)
        if not documents:
            return f"Error: No content extracted from {pdf_path}"
        
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=GOOGLE_API_KEY)
        
        success_count = 0
        error_count = 0
        
        for i, doc in enumerate(documents):
            try:
                embedding_vector = get_embedding(doc["content"], embeddings)
                
                data = {
                    "id": str(uuid.uuid4()),
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "embedding": embedding_vector
                }
                
                supabase.table("documents_rig_rag").insert(data).execute()
                success_count += 1
                
                if i < len(documents) - 1:
                    time.sleep(0.5)
                
            except Exception as e:
                print(f"Error processing chunk {i}: {str(e)}")
                error_count += 1
        
        return f"Processed {len(documents)} chunks from {pdf_path}:\n" \
               f"- Successfully embedded and stored: {success_count}\n" \
               f"- Failed: {error_count}"
    
    except Exception as e:
        return f"Error processing {pdf_path}: {str(e)}"

def embed_pdfs_in_directory(directory: str = None) -> str:
    if directory is None:
        directory = os.getcwd()

    pdf_pattern = os.path.join(directory, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        return f"No PDF files found in {directory}"
    
    results = []
    for pdf_file in pdf_files:
        print(f"\nProcessing {pdf_file}...")
        result = embed_and_store_pdf(pdf_file)
        results.append(f"\n{os.path.basename(pdf_file)}:\n{result}")
    
    return "\n".join(results)

def update_embeddings_tool(instruction: str) -> str:
    instruction = instruction.lower().strip()
    
    if 'embed pdf' in instruction:
        parts = instruction.split('embed pdf')
        if len(parts) > 1:
            filename = parts[1].strip()
            if filename == 'all':
                return embed_pdfs_in_directory()
            return embed_and_store_pdf(filename)
    
    if 'all' in instruction or 'semua' in instruction:
        return embed_pdfs_in_directory()
    
    pdf_files = glob.glob("*.pdf")
    for pdf_file in pdf_files:
        filename_base = os.path.splitext(pdf_file)[0].lower()
        if filename_base in instruction:
            return embed_and_store_pdf(pdf_file)
    
    return f"Instruksi tidak dikenali. Gunakan format: 'embed pdf nama_file.pdf' atau 'embed pdf all'" 