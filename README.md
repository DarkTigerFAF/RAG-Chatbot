# 🤖 RAG-Chatbot (FastAPI + Groq)

## 📌 Overview
This project is a **Retrieval-Augmented Generation (RAG) Chatbot** built with **FastAPI** and **SQLAlchemy**.  
It provides:
- 🔐 **User authentication** with JWT (register/login)  
- 💬 **Chat endpoint** (protected, requires token)  
- 🕑 **Conversation history** stored per user  
- 🧠 **RAG pipeline** using Groq LLM + HuggingFace embeddings  
# RAG-Chatbot (FastAPI + Semantic Kernel + Azure)

## Overview
Production-ready Retrieval-Augmented Generation (RAG) chatbot using FastAPI, SQLAlchemy, Semantic Kernel, Azure OpenAI (chat + embeddings), and Azure AI Search for retrieval. It supports JWT auth, per-user history, and a clean service-based architecture with caching.

---

## Tech Stack
- FastAPI, Pydantic v2
- SQLAlchemy (SQLite by default)
- Auth: OAuth2 bearer + JWT (python-jose, passlib[bcrypt])
- Semantic Kernel (tool plugins, chat orchestration)
- Azure OpenAI: ChatCompletion via SK, embeddings via OpenAI Python SDK (AOAI endpoint)
- Azure AI Search: Vector + semantic hybrid search (async SDK)

---

## Project Structure
```
app/
  api/
    deps.py                 # auth dependency (JWT decode)
    routes/
      auth.py               # /auth/register, /auth/login
      chat.py               # /chat, /chat/history, /chat/service
  core/
    config.py               # load .env early
    database.py             # engine, Base, SessionLocal
  models/
    user.py                 # users table
    history.py              # chat Q/A history
    model_config.py         # chat services catalog
  schemas/
    auth.py                 # UserCreate, UserLogin, Token
    chat.py                 # ChatRequest/Response, ModelConfig, AzureConfig, HistoryPair, ServiceBundle
  services/
    auth/security.py        # hashing, JWT helpers
    rag/
      chat_service.py       # AzureChatCompletion client factory
      embedding_service.py  # Async AOAI embeddings
      vector_retriever.py   # Azure Search (vector + semantic)
      chat_history_service.py # cached SK ChatHistory + redaction
      plugins.py            # SK plugin: retrieval.retrieve()
      service_config.py     # env → AzureConfig
      service_registry.py   # DB → ModelConfig
      factory.py            # orchestrates RAG flow + caching
main.py                     # FastAPI app + routers
```

---

## Data Model
- users: id, username, hashed_password
- history: id, user_id, question, answer, timestamp
- chat_services: id, service_id (unique), chat_deployment, endpoint, api_key, api_version

---

## Auth Flow
1) POST /auth/register → create user and return JWT
2) POST /auth/login → return JWT
3) Use Authorization: Bearer <token> for protected routes

---

## Endpoints
- POST /auth/register → Token
- POST /auth/login → Token
- POST /chat?model=<service_id> → ChatResponse
- GET  /chat/history → list[HistoryPair]
- POST /chat/service → Create a chat service config in DB (ModelConfig)

---

## RAG Pipeline
- Build/reuse a ServiceBundle per service_id:
  - kernel: Semantic Kernel
  - chat_service: AzureChatCompletion client (ChatCompletionClientBase)
- Register retrieval plugin once per kernel: retrieval.retrieve(question, k)
- Build context with ChatHistoryService (cached per user, secret redaction, trimmed turns)
- Execute chat with FunctionChoiceBehavior.Auto and persist the Q/A pair

---

## Configuration
Environment variables (.env):
```
# JWT
JWT_SECRET=your_jwt_secret

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://<your-search-account>.search.windows.net
AZURE_SEARCH_ADMIN_KEY=<admin-key>
AZURE_SEARCH_INDEX=<index-name>

# Azure OpenAI (embeddings deployment name)
AOAI_EMBED_MODEL=<embedding-deployment-name>
```

Chat service settings are stored in DB via POST /chat/service using this payload:
```
{
  "service_id": "my-aoai",
  "chat_deployment": "gpt-4o-mini",
}
```

Azure AI Search index expectations:
- Fields: content (string), content_vector (vector)
- Semantic configuration named "semconf" (used by the query)

---

## Run
```bat
REM 1) Install deps
pip install -r requirements.txt

REM 2) Start API (tables auto-create)
uvicorn app.main:app --reload
```

---

## Quick Start (HTTP examples)
Register
```
POST /auth/register
{ "username": "alice", "password": "secret" }
```

Login
```
POST /auth/login
→ { "access_token": "JWT...", "token_type": "bearer" }
```

Create chat service
```
POST /chat/service
Authorization: Bearer JWT...
{ "service_id": "my-aoai", "chat_deployment": "gpt-4o-mini" }
```

Chat
```
POST /chat?model=my-aoai
Authorization: Bearer JWT...
{ "query": "What’s our refund policy?" }
→ { "answer": "... [#1] ..." }
```

History
```
GET /chat/history
Authorization: Bearer JWT...
→ [ { "question": "...", "answer": "...", "created_at": "..." } ]
```

---

## Notes
- ServiceBundle is typed (Kernel, ChatCompletionClientBase) and cached per service_id.
- Chat history is cached per user with secret redaction and turn trimming.
- Retrieval uses vector + semantic; ensure your index and "semconf" are configured.
