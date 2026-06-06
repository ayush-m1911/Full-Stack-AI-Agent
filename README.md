# 🤖 Datasmith — AI Agent Application

A **production-ready** full-stack scaffold for building AI Agent applications. Features a polished chat interface, multi-file upload, agent trace visualization, and a structured FastAPI backend — all ready to plug your AI model into.

---

## ✨ Features

| Area | Details |
|---|---|
| **Chat UI** | Real-time chat bubbles with user/assistant avatars, timestamps, auto-scroll |
| **File Upload** | Multi-file drag-and-drop with type/size validation, file chips |
| **Agent Trace** | Step-by-step collapsible trace panel with status icons and durations |
| **Result Panel** | Formatted output area with clipboard copy |
| **Responsive** | Sidebar + chat + panels layout that scales cleanly |
| **Dark Mode** | Dark-first design with glassmorphism and gradient accents |

---

## 🏗 Project Structure

```
Datasmith/
├── frontend/               # React + Vite + TypeScript + TailwindCSS v4
│   ├── src/
│   │   ├── api/            # Axios API client
│   │   ├── components/
│   │   │   ├── Chat/       # MessageHistory, InputBox, FileUpload
│   │   │   ├── AgentTrace/ # Trace panel
│   │   │   ├── ResultPanel/# Result display
│   │   │   └── Sidebar/    # Nav sidebar
│   │   ├── hooks/          # useChat, useFileUpload
│   │   └── types/          # Shared TypeScript types
│   ├── Dockerfile
│   ├── nginx.conf
│   └── .env.example
│
├── backend/                # FastAPI + Python 3.12
│   ├── app/
│   │   ├── api/routes/     # health.py, chat.py, upload.py
│   │   ├── core/           # config.py, cors.py
│   │   ├── models/         # schemas.py (Pydantic)
│   │   ├── services/       # agent_service.py, upload_service.py
│   │   └── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js ≥ 20
- Python ≥ 3.12
- Docker & Docker Compose (for containerized setup)

---

### Option A — Local Development

#### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
copy .env.example .env

# Start development server
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000  
Swagger docs at: http://localhost:8000/docs

#### 2. Frontend

```bash
cd frontend

# Copy and configure environment
copy .env.example .env

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:5173

---

### Option B — Docker Compose (Production)

```bash
# From the project root
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend (Nginx) | http://localhost:80 |
| Backend (FastAPI) | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## 📡 API Reference

### Health

```http
GET /api/v1/health
```

Returns app status, version, and timestamp.

### Chat

```http
POST /api/v1/chat
Content-Type: application/json

{
  "session_id": "optional-uuid",
  "message": "Your question here",
  "file_ids": ["file-uuid-1", "file-uuid-2"]
}
```

Returns:
```json
{
  "session_id": "...",
  "message": { "id": "...", "role": "assistant", "content": "..." },
  "trace": [{ "step": 1, "name": "Input Validation", "status": "done", "duration_ms": 12 }],
  "result": "..."
}
```

### Upload

```http
POST /api/v1/upload
Content-Type: multipart/form-data

files: [File, File, ...]
```

Returns file metadata including IDs to reference in chat requests.

### Sessions

```http
GET /api/v1/chat/sessions
GET /api/v1/chat/sessions/{session_id}/history
```

---

## 🔌 Plugging In Your AI

1. Open `backend/app/services/agent_service.py`
2. Replace the stub logic inside `process_chat()` with your LLM/agent call:

```python
async def process_chat(session_id, user_message, file_ids=None):
    # Replace this block:
    response = await your_llm_client.complete(user_message)
    
    trace = [TraceStep(step=1, name="LLM Call", status="done", ...)]
    assistant_msg = ChatMessage(role="assistant", content=response.text)
    
    return ChatResponse(session_id=session_id, message=assistant_msg, trace=trace)
```

The API layer, session management, and UI remain unchanged.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend Framework | React 19 + Vite 6 |
| Language | TypeScript |
| Styling | TailwindCSS v4 |
| HTTP Client | Axios |
| Icons | Lucide React |
| Backend Framework | FastAPI |
| Validation | Pydantic v2 |
| Server | Uvicorn |
| Containerization | Docker + Nginx |

---

## 📦 Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `Datasmith AI Agent` | Application name |
| `DEBUG` | `false` | Debug mode |
| `ALLOWED_ORIGINS` | `[...]` | CORS allowed origins |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max upload size |
| `UPLOAD_DIR` | `uploads` | Upload directory |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Backend base URL |

---

## 📝 License

MIT — use freely, build something great.
