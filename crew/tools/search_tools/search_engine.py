from supabase import create_client, Client
import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import json
import re
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
import time

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

_parsed_cache: Dict[str, dict] = {}
_query_cache: Dict[str, str] = {}

ASSISTANT_PATTERNS = [
    re.compile(r'\b(siapa|who)\b.*\b(dj|ea|dt|ju|lh|yd|cg|lc\d+)\b', re.IGNORECASE),
    re.compile(r'\b[a-z]{2}\b$', re.IGNORECASE),
    re.compile(r'\b(darwin|glory|jason|louis|yudhistira|christopher|gisella|justo|luciano|mathew)\b', re.IGNORECASE),
    re.compile(r'\b(info|informasi|data)\b.*\b(asisten|assistant)\b', re.IGNORECASE),
    re.compile(r'\b(asisten|assistant)\b.*\b(dj|ea|dt|ju|lh|yd|cg|lc\d+)\b', re.IGNORECASE),
    re.compile(r'\b(siapa|who)\b.*\b(asisten|assistant)\b', re.IGNORECASE),
    re.compile(r'\b(siapa|who)\b.*[A-Za-z]{3,}', re.IGNORECASE),
]

TEACHING_PATTERNS = [
    re.compile(r'\b(aturan|prosedur|cara|bagaimana)\b.*\b(mengajar|teaching|ajar)\b', re.IGNORECASE),
    re.compile(r'\b(mengajar|teaching)\b.*\b(aturan|prosedur|cara)\b', re.IGNORECASE),
    re.compile(r'\b(rules|aturan)\b.*\b(mengajar|teaching)\b', re.IGNORECASE),
]

EXAM_PATTERNS = [
    re.compile(r'\b(aturan|prosedur|cara|bagaimana)\b.*\b(ujian|exam|pengawasan|invigilate)\b', re.IGNORECASE),
    re.compile(r'\b(ujian|exam|pengawasan)\b.*\b(aturan|prosedur|cara)\b', re.IGNORECASE),
    re.compile(r'\b(rules|aturan)\b.*\b(ujian|exam)\b', re.IGNORECASE),
]

@lru_cache(maxsize=128)
def detect_query_category(query: str) -> str:
    """Optimized query category detection with caching"""
    for pattern in ASSISTANT_PATTERNS:
        if pattern.search(query):
            return "assistant_search"
    
    for pattern in TEACHING_PATTERNS:
        if pattern.search(query):
            return "teaching_rules"
    
    for pattern in EXAM_PATTERNS:
        if pattern.search(query):
            return "exam_rules"
    
    return "general"

def parse_assistant_data_from_content(content: str) -> dict:
    """Optimized parser with caching"""
    content_hash = str(hash(content))
    if content_hash in _parsed_cache:
        return _parsed_cache[content_hash]
    
    result = {
        'name': 'Tidak diketahui', 'initial': 'Tidak diketahui', 'location': 'Tidak diketahui',
        'position': 'Tidak diketahui', 'shift': 'Tidak diketahui', 'generation': 'Tidak diketahui',
        'initial_gen': 'Tidak diketahui', 'nim': 'Tidak diketahui', 'email_edu': 'Tidak diketahui',
        'email_acid': 'Tidak diketahui', 'binusian_id': 'Tidak diketahui', 'leader': 'Tidak diketahui',
        'major': 'Tidak diketahui', 'major_long': 'Tidak diketahui', 'streaming': 'Tidak diketahui',
        'semester': 'Tidak diketahui'
    }
    
    if not content:
        _parsed_cache[content_hash] = result
        return result
    
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    field_positions = {}
    for i, line in enumerate(lines):
        if line == ':' and i > 0:
            field_name = lines[i-1].lower()
            field_positions[field_name] = i + 1
    
    field_mapping = {
        'name': 'name',
        'location': 'location', 
        'position': 'position',
        'shift': 'shift',
        'initial': 'initial',
        'gen': 'generation',
        'nim': 'nim',
        'leader': 'leader',
        'major': 'major',
        'streaming': 'streaming',
        'semester': 'semester'
    }
    
    for field_name, result_key in field_mapping.items():
        if field_name in field_positions:
            start_pos = field_positions[field_name]
            values = []
            for j in range(start_pos, len(lines)):
                if lines[j] == ':':
                    break
                values.append(lines[j])
            if values:
                result[result_key] = ' '.join(values).strip()
    
    for i in range(len(lines)-4):
        if (lines[i].lower() == 'initial' and lines[i+1] == '+' and 
            lines[i+2].lower() == 'gen' and lines[i+3] == ':'):
            result['initial_gen'] = lines[i+4] if i+4 < len(lines) else 'Tidak diketahui'
            break
    
    for i in range(len(lines)-3):
        if (lines[i].lower() == 'major' and lines[i+1] == '(Long)' and lines[i+2] == ':'):
            values = []
            j = i + 3
            while j < len(lines) and lines[j] != ':' and lines[j].lower() != 'major':
                values.append(lines[j])
                j += 1
            result['major_long'] = ' '.join(values).strip() or 'Tidak diketahui'
            break
    
    _parsed_cache[content_hash] = result
    return result

def optimized_assistant_search(query: str) -> str:
    """Highly optimized assistant search with single query strategy"""
    try:
        print("🚀 Optimized assistant search...")
        
        initials = re.findall(r'\b[a-zA-Z]{2}\b', query)
        name_words = [word for word in query.split() if len(word) > 2 and word.isalpha()]
        
        conditions = []
        params = {}
        
        if initials:
            initial_conditions = []
            for i, initial in enumerate(initials):
                initial_conditions.append(f"metadata->>'initial' ilike %s")
                params[f'initial_{i}'] = f'%{initial.upper()}%'
            if initial_conditions:
                conditions.append(f"({' OR '.join(initial_conditions)})")
        
        if name_words:
            name_conditions = []
            for i, word in enumerate(name_words):
                name_conditions.append(f"(metadata->>'name' ilike %s OR content ilike %s)")
                params[f'name_{i}_1'] = f'%{word}%'
                params[f'name_{i}_2'] = f'%{word}%'
            if name_conditions:
                conditions.append(f"({' OR '.join(name_conditions)})")
        
        if not conditions:
            conditions.append("content ilike %s")
            params['general'] = f'%{query}%'
        
        where_clause = ' OR '.join(conditions)
        
        try:
            response = supabase.rpc('search_assistants_optimized', {
                'search_query': query,
                'limit_count': 10
            }).execute()
            
            if not response.data:
                response = supabase.table('documents_rig_rag').select('*').limit(10).execute()
                all_results = [item for item in response.data if any(
                    word.lower() in item.get('content', '').lower() or 
                    word.lower() in str(item.get('metadata', {})).lower()
                    for word in name_words + [query]
                )]
            else:
                all_results = response.data
                
        except Exception:
            all_results = []
            
            for initial in initials:
                try:
                    response = supabase.table('documents_rig_rag').select('*').eq('metadata->>initial', initial.upper()).limit(5).execute()
                    all_results.extend(response.data)
                except Exception:
                    pass
            
            if not all_results:
                for word in name_words[:2]:
                    try:
                        response = supabase.table('documents_rig_rag').select('*').ilike('content', f'%{word}%').limit(5).execute()
                        all_results.extend(response.data)
                    except Exception:
                        pass
        
        if not all_results:
            return "Tidak ditemukan data asisten yang sesuai dengan pencarian Anda. Silakan coba dengan kata kunci lain atau pastikan penulisan sudah benar."
        
        seen_ids = set()
        unique_results = []
        for item in all_results:
            item_id = item.get('id')
            if item_id not in seen_ids:
                unique_results.append(item)
                seen_ids.add(item_id)
        
        result_info = []
        for item in unique_results[:3]:
            content = item.get('content', '')
            if content:
                assistant_info = parse_assistant_data_from_content(content)
                if assistant_info['name'] != 'Tidak diketahui':
                    result_info.append(assistant_info)
        
        if not result_info:
            return "Data ditemukan tapi tidak bisa diparse dengan baik. Silakan coba kata kunci yang lebih spesifik."
        
        if len(result_info) == 1:
            info = result_info[0]
            return f"""Ditemukan informasi asisten berikut:

Nama: {info['name']}
Initial: {info['initial']}
Initial + Generasi: {info['initial_gen']}
Lokasi: {info['location']}
Posisi: {info['position']}
Shift: {info['shift']}
Jurusan: {info['major_long']} ({info['major']})
Streaming: {info['streaming']}
Semester: {info['semester']}
Leader: {info['leader']}

Gunakan informasi ini untuk memberikan jawaban yang natural dan informatif kepada user."""
        else:
            descriptions = [
                f"{i}. {info['name']} ({info['initial_gen']}) - {info['major_long']}, Lokasi: {info['location']}"
                for i, info in enumerate(result_info, 1)
            ]
            return f"Ditemukan {len(result_info)} asisten yang sesuai:\n\n" + "\n".join(descriptions) + "\n\nSilakan pilih yang dimaksud atau berikan informasi lebih spesifik."
        
    except Exception as e:
        return f"Terjadi kesalahan saat mencari data asisten: {str(e)}"

@lru_cache(maxsize=32)
def optimized_content_search(query: str, search_type: str) -> str:
    """Optimized content search with caching"""
    try:
        cache_key = f"{search_type}_{query}"
        if cache_key in _query_cache:
            return _query_cache[cache_key]
        
        if search_type == "teaching":
            keywords = ['mengajar', 'teaching', 'prosedur', 'aturan']
            search_desc = "📚 Searching teaching procedures..."
            not_found_msg = "Maaf, tidak ditemukan informasi tentang prosedur mengajar dalam database."
        else:
            keywords = ['ujian', 'exam', 'pengawasan', 'prosedur', 'aturan']
            search_desc = "📝 Searching exam procedures..."
            not_found_msg = "Maaf, tidak ditemukan informasi tentang prosedur pengawasan ujian dalam database."
        
        print(search_desc)
        
        keyword_conditions = " OR ".join([f"content ilike '%{keyword}%'" for keyword in keywords])
        
        try:
            response = supabase.table('documents_rig_rag').select('content').limit(20).execute()
            if not response.data:
                _query_cache[cache_key] = not_found_msg
                return not_found_msg
            
            relevant_content = []
            seen_content = set()
            
            for item in response.data:
                content = item.get('content', '').strip()
                if (content and len(content) > 30 and content not in seen_content and
                    any(keyword in content.lower() for keyword in keywords)):
                    relevant_content.append(content)
                    seen_content.add(content)
                    if len(relevant_content) >= 5:
                        break
            
            if not relevant_content:
                _query_cache[cache_key] = not_found_msg
                return not_found_msg
            
            combined_content = "\n\n".join(relevant_content)
            result = f"""Berikut informasi tentang {'prosedur mengajar' if search_type == 'teaching' else 'prosedur pengawasan ujian'} yang ditemukan:

{combined_content}

Berikan ringkasan dan penjelasan yang mudah dipahami berdasarkan informasi di atas."""
            
            _query_cache[cache_key] = result
            return result
            
        except Exception as e:
            error_msg = f"Error dalam pencarian: {str(e)}"
            _query_cache[cache_key] = error_msg
            return error_msg
        
    except Exception as e:
        return f"Terjadi kesalahan sistem: {str(e)}"

def smart_search_tool(query: str) -> str:
    """Ultra-fast smart search with optimized routing"""
    try:
        start_time = time.time()
        query_normalized = query.lower().strip()
        
        query_type = detect_query_category(query_normalized)
        
        print(f"🎯 Query type: {query_type} (detected in {time.time() - start_time:.3f}s)")
        
        if query_type == "assistant_search":
            return optimized_assistant_search(query_normalized)
        elif query_type == "teaching_rules":
            return optimized_content_search(query_normalized, "teaching")
        elif query_type == "exam_rules":
            return optimized_content_search(query_normalized, "exam")
        else:
            return enhanced_hybrid_search(query)
            
    except Exception as e:
        return f"Error in smart search: {str(e)}"

def search_assistant_data(query: str) -> str:
    """Wrapper for backwards compatibility"""
    return optimized_assistant_search(query)

def search_teaching_procedures(query: str) -> str:
    """Wrapper for backwards compatibility"""
    return optimized_content_search(query, "teaching")

def search_exam_procedures(query: str) -> str:
    """Wrapper for backwards compatibility"""
    return optimized_content_search(query, "exam")

def enhanced_hybrid_search(query: str) -> str:
    """Simplified hybrid search for general queries"""
    try:
        response = supabase.table('documents_rig_rag').select('*').ilike('content', f'%{query}%').limit(10).execute()
        
        if not response.data:
            return "Maaf, tidak ditemukan informasi yang sesuai dengan pencarian Anda."
        
        content_pieces = []
        for item in response.data[:5]:
            content = item.get('content', '').strip()
            if content and len(content) > 30:
                content_pieces.append(content[:200] + "..." if len(content) > 200 else content)
        
        if content_pieces:
            return f"Ditemukan informasi berikut:\n\n" + "\n\n".join(content_pieces)
        
        return "Informasi ditemukan tapi tidak dapat diproses dengan baik. Silakan coba kata kunci lain."
        
    except Exception as e:
        return f"Terjadi kesalahan saat mencari: {str(e)}"

def clear_cache():
    """Clear all caches"""
    global _parsed_cache, _query_cache
    _parsed_cache.clear()
    _query_cache.clear()
    detect_query_category.cache_clear()
    optimized_content_search.cache_clear()

def get_cache_stats():
    """Get cache statistics"""
    return {
        'parsed_cache_size': len(_parsed_cache),
        'query_cache_size': len(_query_cache),
        'category_cache_info': detect_query_category.cache_info(),
        'content_cache_info': optimized_content_search.cache_info()
    } 