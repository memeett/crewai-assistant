from crewai import Task

def create_task(agent, query: str, context: str = ""):
    """Create task based on query type"""
    query_lower = query.lower()
    
    if any(keyword in query_lower for keyword in ['embed', 'update', 'pdf']):
        return Task(
            description=f"""
            Context: {context}
            User request: {query}
            
            Lakukan update embeddings PDF sesuai permintaan user. 
            Jika user meminta embed file tertentu, proses file tersebut.
            Jika user meminta embed semua file, proses semua PDF yang tersedia.
            
            Berikan laporan yang jelas tentang hasil proses embedding.
            """,
            expected_output="Laporan hasil update embeddings PDF dengan status sukses atau error",
            agent=agent
        )
    else:
        return Task(
            description=f"""
            Context: {context}
            User query: {query}
            
            Sebagai SLC Assistant yang ramah dan profesional, bantu user dengan memberikan informasi yang natural dan mudah dipahami:
            
            1. Jika user mencari informasi asisten (nama/initial), gunakan search tool dan:
               - Olah data yang ditemukan menjadi jawaban yang conversational
               - Sebutkan informasi penting seperti nama, initial, jurusan, semester, lokasi
               - Tambahkan konteks yang relevan dan helpful
               - Jangan hanya copy-paste data mentah
            
            2. Jika user bertanya tentang prosedur mengajar:
               - Gunakan search tool untuk mendapatkan informasi
               - Rangkum prosedur dalam bahasa yang mudah dipahami
               - Berikan poin-poin penting secara terstruktur
               - Tambahkan tips atau saran jika relevan
            
            3. Jika user bertanya tentang prosedur pengawasan ujian:
               - Gunakan search tool untuk mendapatkan informasi
               - Jelaskan prosedur dengan jelas dan sistematis
               - Highlight hal-hal penting yang perlu diperhatikan
               - Berikan panduan step-by-step jika diperlukan
            
            PENTING: 
            - Selalu berikan jawaban yang natural, ramah, dan conversational
            - Jangan memberikan output mentah atau format JSON
            - Olah informasi menjadi bahasa yang mudah dipahami
            - Sesuaikan tone dengan konteks pertanyaan
            - Jika informasi tidak lengkap, sampaikan dengan sopan dan tawarkan alternatif
            
            Jika pertanyaan di luar 3 hal di atas, jelaskan dengan ramah bahwa Anda hanya dapat membantu dengan informasi asisten SLC, prosedur mengajar, dan prosedur ujian.
            """,
            expected_output="Jawaban yang natural, informatif, dan mudah dipahami dalam bahasa Indonesia yang ramah dan profesional",
            agent=agent
        ) 