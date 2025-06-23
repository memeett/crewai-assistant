# 🚀 SLC Assistant Flask API

Sistem asisten virtual untuk Software Laboratory Center (SLC) dengan Flask API dan CrewAI integration.

## 🎯 Features

- **Flask REST API** dengan POST endpoints
- **CrewAI Agents** untuk intelligent responses  
- **Supabase Integration** untuk data storage
- **Session Management** untuk conversation history
- **Smart Search** untuk mencari data asisten, prosedur mengajar, dan aturan ujian

## 📂 Project Structure

```
terbaru/
├── app.py                    # Flask application 
├── main.py                   # Interactive chat mode
├── config/
│   ├── agents.py            # AI agents configuration
│   └── tasks.py             # Task definitions
├── crew/
│   └── tools/
│       ├── pdf_tools.py     # PDF processing tools
│       └── search_tools/
│           └── search_engine.py  # Search functionality
├── test_api.py              # API testing script
├── requirements.txt         # Dependencies
└── .env                     # Environment variables
```

## 🔧 Setup

### 1. Environment Variables

Create `.env` file:
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
GOOGLE_API_KEY=your_google_api_key
```

### 2. Install Dependencies

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

### 3. Run Application

**Flask API:**
```bash
python app.py
```

**Interactive Chat:**
```bash
python main.py
```

## 🌐 API Endpoints

### POST `/api/chat`
Main chat interface

**Request:**
```json
{
  "message": "siapa luciano mathew",
  "session_id": "user123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Luciano Mathew Hinarta dengan initial LO24-1...",
  "session_id": "user123",
  "agent_used": "SLC Assistant Agent",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### POST `/api/embed`
Document embedding

**Request:**
```json
{
  "filename": "Extra.pdf",
  "session_id": "user123"
}
```

### GET `/api/sessions/{id}`
Get conversation history

### DELETE `/api/sessions/{id}`
Clear conversation history

## 🧪 Testing

```bash
# Test all endpoints
python test_api.py

# Test specific query
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "siapa luciano mathew", "session_id": "test"}'
```

## 💡 Usage Examples

### Search Assistant Data
```
"siapa luciano mathew"
"asisten dengan initial LM"  
"info asisten EA"
```

### Teaching Procedures
```
"bagaimana prosedur mengajar"
"aturan mengajar di SLC"
```

### Exam Rules
```
"prosedur pengawasan ujian"
"aturan ujian SLC"
```

## 🔍 How It Works

1. **Query Detection**: System detects query type (assistant search, teaching rules, exam rules)
2. **Smart Search**: Uses vector similarity search on Supabase database
3. **Content Parsing**: Extracts structured data from PDF content  
4. **AI Processing**: CrewAI agents process and format responses naturally
5. **Session Management**: Maintains conversation context per session

## 🛠️ Troubleshooting

### Flask App Won't Start
- Check `.env` file exists and has correct credentials
- Verify virtual environment is activated
- Ensure port 5000 is not in use

### "Agents Not Ready" Error
- Verify Google API Key is valid
- Check Supabase connection
- Ensure PDF documents are properly embedded

### Search Results Empty
- Verify data exists in Supabase `documents_rig_rag` table
- Check query spelling and format
- Try broader search terms

## 📦 Dependencies

- **Flask 3.0.0**: Web framework
- **CrewAI 0.30.11**: AI agent framework  
- **Supabase**: Database and storage
- **Google Generative AI**: Language model
- **LangChain**: AI orchestration tools

## 🔐 Security Notes

- Keep `.env` file secure and never commit to git
- Use environment variables for all sensitive data
- Consider rate limiting for production deployment
- Validate all user inputs

## 📝 Development Notes

- System uses Gemini 2.0 Flash model for AI responses
- PDF content is chunked and embedded with 768 dimensions
- Search combines metadata and content queries for best results
- Session data is stored in memory (consider Redis for production)

## 🚀 Production Deployment

For production use:
1. Use a production WSGI server (gunicorn, uwsgi)
2. Implement proper logging and monitoring  
3. Add rate limiting and input validation
4. Use Redis or database for session storage
5. Set up SSL/HTTPS
6. Configure firewall and security headers

## Description
 - CrewAI tools empower agents with capabilities ranging from web searching and data analysis to collaboration and delegating tasks among coworkers.

## Libraries Used
 - crewai==0.30.11
 - crewai-tools==0.2.6
 - langchain-google-genai==1.0.3
 - python-dotenv==1.0.1
 - streamlit==1.34.0

## Installation
 1. Prerequisites
    - Git
    - Command line familiarity
 2. Clone the Repository: `git clone https://github.com/NebeyouMusie/News-AI-Agents-Using-CrewAI-And-Google-Gemini-Pro-LLM-Models.git`
 3. Create and Activate Virtual Environment (Recommended)
    - `python -m venv venv`
    - `source venv/bin/activate`
 4. Navigate to the projects directory `cd ./News-AI-Agents-Using-CrewAI-And-Google-Gemini-Pro-LLM-Models` using your terminal
 5. Install Libraries: `pip install -r requirements.txt`
 6. run `python crew/crew.py`
 7. a markdown file called `news.md` will be saved at the root directory

## Collaboration
- Collaborations are welcomed ❤️

## Acknowledgments
 - I would like to thank [Krish Naik](https://www.youtube.com/@krishnaik06)
   
## Contact
 - LinkedIn: [Nebeyou Musie](https://www.linkedin.com/in/nebeyou-musie)
 - Gmail: nebeyoumusie@gmail.com
 - Telegram: [Nebeyou Musie](https://t.me/NebeyouMusie)




