from supabase import create_client, Client
import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import json
import re

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def detect_query_category(query: str) -> str:
    """CEK CATEGORY QUERY    """
    import re
    
    assistant_patterns = [
        r'\b(siapa|who)\b.*\b(dj|ea|dt|ju|lh|yd|cg|lc\d+)\b', 
        r'\b[a-z]{2}\b$',  
        r'\b(darwin|glory|jason|louis|yudhistira|christopher|gisella|justo)\b',  # Names
        r'\b(info|informasi|data)\b.*\b(asisten|assistant)\b',  # "info asisten"
        r'\b(asisten|assistant)\b.*\b(dj|ea|dt|ju|lh|yd|cg|lc\d+)\b',  # "asisten"
    ]
    
    teaching_patterns = [
        r'\b(aturan|prosedur|cara|bagaimana)\b.*\b(mengajar|teaching|ajar)\b',
        r'\b(mengajar|teaching)\b.*\b(aturan|prosedur|cara)\b',
        r'\b(rules|aturan)\b.*\b(mengajar|teaching)\b',
    ]
    
    exam_patterns = [
        r'\b(aturan|prosedur|cara|bagaimana)\b.*\b(ujian|exam|pengawasan|invigilate)\b',
        r'\b(ujian|exam|pengawasan)\b.*\b(aturan|prosedur|cara)\b',
        r'\b(rules|aturan)\b.*\b(ujian|exam)\b',
    ]
    
    for pattern in assistant_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return "assistant_search"
    
    for pattern in teaching_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return "teaching_rules"
    
    for pattern in exam_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return "exam_rules"
    
    return "general"

def search_assistant_data(query: str) -> str:
    """
    Search for assistant data and return in natural format for Gemini processing
    """
    try:
        print("🔍 Searching assistant data...")
        
        import re
        
        initials = re.findall(r'\b[a-zA-Z]{2}\b', query)
        
        name_words = [word for word in query.split() if len(word) > 2 and word.isalpha()]
        
        all_results = []
        
        for initial in initials:
            try:
                # Direct table search 
                response = supabase.table('documents_rig_rag').select('*').eq('metadata->>initial', initial.upper()).execute()
                if response.data:
                    all_results.extend(response.data)
                    print(f"Found {len(response.data)} results for initial: {initial.upper()}")
            except Exception as e:
                print(f"Error searching by initial {initial}: {e}")
        
        # Search by name if no initial results
        if not all_results:
            for name_word in name_words:
                try:
                    response = supabase.table('documents_rig_rag').select('*').ilike('metadata->>name', f'%{name_word}%').execute()
                    if response.data:
                        all_results.extend(response.data)
                        print(f"Found {len(response.data)} results for name: {name_word}")
                except Exception as e:
                    print(f"Error searching by name {name_word}: {e}")
        
        if not all_results:
            try:
                response = supabase.table('documents_rig_rag').select('*').ilike('content', f'%{query}%').execute()
                if response.data:
                    all_results.extend(response.data)
                    print(f"Found {len(response.data)} results in content")
            except Exception as e:
                print(f"Error in content search: {e}")
        
        if not all_results:
            return "Tidak ditemukan data asisten yang sesuai dengan pencarian Anda. Silakan coba dengan kata kunci lain atau pastikan penulisan sudah benar."

        seen_ids = set()
        unique_results = []
        for item in all_results:
            if item.get('id') not in seen_ids:
                unique_results.append(item)
                seen_ids.add(item.get('id'))
        
        result_info = []
        for item in unique_results[:3]:  # BALIKIN 3 DATA
            metadata = item.get('metadata', {})
            assistant_info = {
                'name': metadata.get('name', 'Tidak diketahui'),
                'initial': metadata.get('initial', 'Tidak diketahui'),
                'generation': metadata.get('gen', 'Tidak diketahui'),
                'initial_gen': metadata.get('initial_gen', 'Tidak diketahui'),
                'nim': metadata.get('nim', 'Tidak diketahui'),
                'email_edu': metadata.get('email_edu', 'Tidak diketahui'),
                'email_acid': metadata.get('email_acid', 'Tidak diketahui'),
                'binusian_id': metadata.get('binusian_id', 'Tidak diketahui'),
                'leader': metadata.get('leader', 'Tidak diketahui'),
                'major': metadata.get('major', 'Tidak diketahui'),
                'major_long': metadata.get('major_long', 'Tidak diketahui'),
                'streaming': metadata.get('streaming', 'Tidak diketahui'),
                'semester': metadata.get('semester', 'Tidak diketahui'),
                'location': metadata.get('location', 'Tidak diketahui'),
                'position': metadata.get('position', 'Tidak diketahui'),
                'shift': metadata.get('shift', 'Tidak diketahui')
            }
            result_info.append(assistant_info)
        
        if len(result_info) == 1:
            info = result_info[0]
            return f"""Ditemukan informasi asisten berikut:

Nama: {info['name']}
Initial: {info['initial']} (Generasi {info['generation']})
Initial + Generasi: {info['initial_gen']}
NIM: {info['nim']}
Binusian ID: {info['binusian_id']}
Email Edu: {info['email_edu']}
Email AC ID: {info['email_acid']}
Leader: {info['leader']}
Jurusan: {info['major_long']} ({info['major']})
Streaming: {info['streaming']}
Semester: {info['semester']}
Lokasi: {info['location']}
Posisi: {info['position']}
Shift: {info['shift']}

Gunakan informasi ini untuk memberikan jawaban yang natural dan informatif kepada user."""
        else:
            descriptions = []
            for i, info in enumerate(result_info, 1):
                desc = f"{i}. {info['name']} ({info['initial']}{info['generation']}) - {info['major_long']}, Lokasi: {info['location']}"
                descriptions.append(desc)
            
            return f"""Ditemukan {len(result_info)} asisten yang sesuai:

{chr(10).join(descriptions)}

Silakan pilih yang dimaksud atau berikan informasi lebih spesifik untuk mendapatkan detail lengkap."""
        
    except Exception as e:
        return f"Terjadi kesalahan saat mencari data asisten: {str(e)}"

def search_teaching_procedures(query: str) -> str:
    """
    Search for teaching procedures and return natural content for processing
    """
    try:
        print("📚 Searching teaching procedures...")
        
        teaching_keywords = ['mengajar', 'teaching', 'ajar', 'prosedur', 'aturan', 'procedure', 'rules']
        
        results = []
        for keyword in teaching_keywords:
            try:
                response = supabase.table('documents_rig_rag').select('*').ilike('content', f'%{keyword}%').limit(10).execute()
                if response.data:
                    results.extend(response.data)
            except Exception as e:
                print(f"Error searching teaching keyword {keyword}: {e}")
        
        if not results:
            return "Maaf, saat ini tidak ditemukan informasi tentang prosedur mengajar dalam database. Silakan hubungi coordinator SLC untuk informasi lebih lanjut."
        
        content_pieces = []
        seen_content = set()
        
        for item in results[:15]:  
            content = item.get('content', '').strip()
            if content and len(content) > 30 and content not in seen_content:  # Avoid duplicates
                content_lower = content.lower()
                if any(keyword in content_lower for keyword in ['mengajar', 'teaching', 'prosedur', 'aturan']):
                    content_pieces.append(content)
                    seen_content.add(content)
        
        if not content_pieces:
            return "Informasi prosedur mengajar ditemukan tapi tidak cukup detail. Silakan hubungi coordinator SLC untuk informasi lengkap."
        
        combined_content = "\n\n".join(content_pieces[:8])  # Limit to avoid token overload
        return f"""Berikut informasi tentang prosedur mengajar yang ditemukan dalam dokumen SLC:

{combined_content}

Berikan ringkasan dan penjelasan yang mudah dipahami berdasarkan informasi di atas."""
        
    except Exception as e:
        return f"Terjadi kesalahan saat mencari prosedur mengajar: {str(e)}"

def search_exam_procedures(query: str) -> str:
    """
    Search for exam procedures and return natural content for processing
    """
    try:
        print("📝 Searching exam procedures...")
        
        exam_keywords = ['ujian', 'exam', 'pengawasan', 'invigilate', 'prosedur', 'aturan', 'procedure', 'rules']
        
        results = []
        for keyword in exam_keywords:
            try:
                response = supabase.table('documents_rig_rag').select('*').ilike('content', f'%{keyword}%').limit(10).execute()
                if response.data:
                    results.extend(response.data)
            except Exception as e:
                print(f"Error searching exam keyword {keyword}: {e}")
        
        if not results:
            return "Maaf, saat ini tidak ditemukan informasi tentang prosedur pengawasan ujian dalam database. Silakan hubungi coordinator SLC untuk informasi lebih lanjut."
        
        content_pieces = []
        seen_content = set()
        
        for item in results[:15]: 
            content = item.get('content', '').strip()
            if content and len(content) > 30 and content not in seen_content:  # Avoid duplicates
                content_lower = content.lower()
                if any(keyword in content_lower for keyword in ['ujian', 'exam', 'pengawasan', 'prosedur', 'aturan']):
                    content_pieces.append(content)
                    seen_content.add(content)
        
        if not content_pieces:
            return "Informasi prosedur pengawasan ujian ditemukan tapi tidak cukup detail. Silakan hubungi coordinator SLC untuk informasi lengkap."
        
        combined_content = "\n\n".join(content_pieces[:8])  #
        return f"""Berikut informasi tentang prosedur pengawasan ujian yang ditemukan dalam dokumen SLC:

{combined_content}

Berikan ringkasan dan penjelasan yang mudah dipahami berdasarkan informasi di atas."""
        
    except Exception as e:
        return f"Terjadi kesalahan saat mencari prosedur ujian: {str(e)}"

def enhanced_hybrid_search(query: str) -> str:
    """
    Enhanced hybrid search with better name matching - returns natural format
    """
    try:
        query_lower = query.lower().strip()
        all_results = []
        
        import re
        potential_initials = re.findall(r'\b[a-zA-Z]{2}\b', query)
        
        for initial in potential_initials:
            response = supabase.table('documents_rig_rag').select('*').eq('metadata->>initial', initial.upper()).limit(10).execute()
            if response.data:
                for item in response.data:
                    item['search_strategy'] = 'exact_initial'
                    item['relevance_score'] = 1.0
                all_results.extend(response.data)
                print(f"Found {len(response.data)} results for initial: {initial.upper()}")
        
        if not all_results:
            response = supabase.table('documents_rig_rag').select('*').ilike('metadata->>name', f'%{query_lower}%').limit(10).execute()
            if response.data:
                for item in response.data:
                    # Calculate name similarity
                    name = item.get('metadata', {}).get('name', '').lower()
                    if query_lower in name:
                        similarity = len(query_lower) / len(name) if name else 0
                        item['search_strategy'] = 'name_match'
                        item['relevance_score'] = 0.9 + similarity * 0.1
                all_results.extend(response.data)
                print(f"Found {len(response.data)} results for name: {query_lower}")
        
        if not all_results:
            words = [word for word in query_lower.split() if len(word) > 2]
            for word in words:
                # Search in name field
                response = supabase.table('documents_rig_rag').select('*').ilike('metadata->>name', f'%{word}%').limit(8).execute()
                if response.data:
                    for item in response.data:
                        item['search_strategy'] = f'word_match_{word}'
                        item['relevance_score'] = 0.7
                    all_results.extend(response.data)
                    print(f"Found {len(response.data)} results for word: {word}")
        
        if not all_results:
            response = supabase.table('documents_rig_rag').select('*').ilike('content', f'%{query_lower}%').limit(15).execute()
            if response.data:
                for item in response.data:
                    item['search_strategy'] = 'content_match'
                    item['relevance_score'] = 0.5
                all_results.extend(response.data)
                print(f"Found {len(response.data)} results in content")
        
        if not all_results:
            return "Maaf, tidak ditemukan informasi yang sesuai dengan pencarian Anda. Silakan coba dengan kata kunci yang berbeda atau lebih spesifik."
        
        seen_ids = set()
        unique_results = []
        for item in all_results:
            if item.get('id') not in seen_ids:
                unique_results.append(item)
                seen_ids.add(item.get('id'))
        
        # Sort by relevance score
        unique_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        top_results = unique_results[:5]
        
        assistant_results = []
        content_results = []
        
        for item in top_results:
            metadata = item.get('metadata', {})
            if metadata.get('initial') or metadata.get('name'):
                assistant_results.append(item)
            else:
                content_results.append(item)
        
        if assistant_results:
            formatted_assistants = []
            for item in assistant_results[:3]:
                metadata = item.get('metadata', {})
                assistant_info = {
                    'name': metadata.get('name', 'Tidak diketahui'),
                    'initial': metadata.get('initial', 'Tidak diketahui'),
                    'generation': metadata.get('gen', 'Tidak diketahui'),
                    'major_long': metadata.get('major_long', 'Tidak diketahui'),
                    'location': metadata.get('location', 'Tidak diketahui'),
                    'position': metadata.get('position', 'Tidak diketahui')
                }
                formatted_assistants.append(assistant_info)
            
            if len(formatted_assistants) == 1:
                info = formatted_assistants[0]
                return f"""Ditemukan informasi asisten: {info['name']} ({info['initial']}) dari jurusan {info['major_long']}, berlokasi di {info['location']} dengan posisi {info['position']}.

Apakah ini informasi yang Anda cari? Jika ya, saya bisa memberikan detail lengkap lainnya."""
            else:
                descriptions = []
                for info in formatted_assistants:
                    desc = f"• {info['name']} ({info['initial']}) - {info['major_long']}, {info['location']}"
                    descriptions.append(desc)
                
                return f"""Ditemukan beberapa asisten yang sesuai:

{chr(10).join(descriptions)}

Silakan sebutkan nama atau initial yang lebih spesifik untuk mendapatkan informasi detail."""
        
        elif content_results:
            relevant_content = []
            for item in content_results[:5]:
                content = item.get('content', '').strip()
                if content and len(content) > 30:
                    relevant_content.append(content)
            
            if relevant_content:
                combined_content = "\n\n".join(relevant_content[:3])  # Limit content
                return f"""Ditemukan informasi terkait pencarian Anda:

{combined_content}

Apakah informasi ini membantu? Jika Anda mencari hal yang lebih spesifik, silakan berikan detail tambahan."""
        
        return "Ditemukan beberapa hasil pencarian, tapi tidak cukup spesifik. Silakan coba dengan kata kunci yang lebih detail atau spesifik."
        
    except Exception as e:
        return f"Terjadi kesalahan saat melakukan pencarian: {str(e)}. Silakan coba lagi atau hubungi administrator."

def smart_search_tool(query: str) -> str:
    """
    Smart search that determines the best search strategy based on query type
    and returns raw data for Gemini to process naturally
    """
    try:
        query_normalized = query.lower().strip()
        
        query_type = detect_query_category(query_normalized)
        
        print(f"Detected query type: {query_type}")
        
        if query_type == "assistant_search":
            return search_assistant_data(query_normalized)
        elif query_type == "teaching_rules":
            return search_teaching_procedures(query_normalized)
        elif query_type == "exam_rules":
            return search_exam_procedures(query_normalized)
        else:
            return enhanced_hybrid_search(query)
            
    except Exception as e:
        return f"Error in smart search: {str(e)}" 