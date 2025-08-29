# 🤖 RAG-Chatbot (FastAPI + Semantic Kernel + Azure)

## 📌 Overview
This project is a **Retrieval-Augmented Generation (RAG) Chatbot** built with **FastAPI**, **Semantic Kernel**, and **Azure AI services**.  
It provides:
- **User authentication** with JWT (register/login)  
- **Chat endpoint** (protected, requires token)  
- **Conversation history** stored per user with caching and redaction
- **RAG pipeline** using Azure OpenAI + Azure AI Search  
- **Dynamic chat service configuration** via database

---

## 🛠️ Tech Stack
- **Backend**: FastAPI, Pydantic v2, SQLAlchemy
- **Database**: SQLite (optimized with WAL mode)
- **Authentication**: OAuth2 Bearer + JWT (python-jose, passlib[bcrypt])
- **AI Framework**: Semantic Kernel with function calling
- **Azure Services**: 
  - Azure OpenAI (chat completion)
  - Azure AI Search (vector + semantic hybrid search)
- **Response Format**: ORJSON for performance
- **Middleware**: CORS, GZip compression

---

## 📁 Project Structure
```
app/
├── api/
│   ├── deps.py                     # JWT auth dependency
│   └── routes/
│       ├── auth.py                 # /auth/register, /auth/login
│       └── chat.py                 # /chat, /chat/history, /chat/service
├── core/
│   ├── config.py                   # Environment variable loading
│   └── database.py                 # SQLAlchemy engine, Base, session
├── models/
│   ├── user.py                     # User table model
│   ├── history.py                  # Chat history table model
│   └── model_config.py             # Chat services configuration table
├── schemas/
│   ├── auth.py                     # Auth request/response models
│   └── chat.py                     # Chat request/response models
└── services/
    ├── auth/
    │   └── security.py             # Password hashing, JWT creation
    └── rag/
        ├── chat_service.py         # Azure chat completion client
        ├── vector_retriever.py     # Azure AI Search retrieval
        ├── chat_history_service.py # Chat history with caching & redaction
        ├── plugins.py              # Semantic Kernel retrieval plugin
        ├── service_config.py       # Environment to config mapping
        ├── service_registry.py     # Database to config loading
        └── factory.py              # RAG orchestration with caching
```

---

## 🗄️ Data Model
- **users**: id, username, hashed_password
- **history**: id, user_id, question, answer, timestamp (with indexed user_id + timestamp)
- **chat_services**: id, service_id (unique), chat_deployment

---

## 🔐 Authentication Flow
1. **POST** `/auth/register` → Create user and return JWT
2. **POST** `/auth/login` → Validate credentials and return JWT  
3. Use `Authorization: Bearer <token>` header for protected routes

---

## 🚀 API Endpoints

### Authentication
- `POST /auth/register` → Token
- `POST /auth/login` → Token

### Chat
- `POST /chat?model=<service_id>` → ChatResponse (requires auth)
- `GET /chat/history` → list[HistoryPair] (requires auth)
- `POST /chat/service` → Create chat service configuration (requires auth)

---

## 🤖 RAG Pipeline Architecture

### Core Components
1. **ServiceBundle Caching**: Reusable chat services cached per `service_id`
2. **Semantic Kernel Integration**: 
   - Function calling with `FunctionChoiceBehavior.Auto`
   - Vector search plugin: `retrieval.retrieve(question, k)`
3. **Chat History Service**:
   - Per-user conversation caching with `ChatHistoryTruncationReducer`
   - Automatic secret redaction (API keys, tokens, passwords)
   - Configurable turn limits (default: 8 turns)
4. **Azure AI Search**: Vector + semantic hybrid search with 50 top-k retrieval

### Flow
1. Load/cache `ModelConfig` from database by `service_id`
2. Create/reuse `ServiceBundle` (Semantic Kernel + Azure chat service)
3. Build conversation context with history and system prompt
4. Execute chat with automatic function calling for retrieval
5. Persist question-answer pair asynchronously

---

## ⚙️ Configuration

### Environment Variables (.env)
```env
# JWT Authentication
JWT_SECRET=your_jwt_secret_key

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://<your-search-service>.search.windows.net
AZURE_SEARCH_ADMIN_KEY=<your-admin-key>
AZURE_SEARCH_INDEX=<your-index-name>

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_API_VERSION=2024-06-01
AOAI_EMBED_MODEL=<embedding-deployment-name>

# CORS (optional)
CORS_ORIGINS=*
```

### Dynamic Chat Service Configuration
Chat services are stored in the database. Create them via API:
```json
POST /chat/service
{
  "service_id": "gpt-4o-mini",
  "chat_deployment": "gpt-4o-mini-deployment"
}
```

### Azure AI Search Index Requirements
- **Fields**: `content` (string), `content_vector` (vector)
- **Semantic Configuration**: Named `"semconf"`
- **Query Type**: Hybrid vector + semantic search

---

## 🚀 Quick Start

### 1. Installation
```bash
pip install -r requirements.txt
```

### 2. Environment Setup
Create `.env` file with required Azure credentials (see Configuration section)

### 3. Run Application
```bash
uvicorn app.main:app --reload
```
Tables are auto-created on startup.

---

## 📋 Usage Examples

### Register User
```bash
POST /auth/register
Content-Type: application/json

{
  "username": "alice", 
  "password": "secure123"
}
```

### Login
```bash
POST /auth/login
Content-Type: application/json

{
  "username": "alice", 
  "password": "secure123"  
}

# Response: {"access_token": "eyJ...", "token_type": "bearer"}
```

### Create Chat Service
```bash
POST /chat/service
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "service_id": "gpt-4o-mini",
  "chat_deployment": "gpt-4o-mini-deployment"
}
```

### Chat with RAG
```bash
POST /chat?model=gpt-4o-mini  
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "query": "What is your refund policy?"
}

# Response: {"answer": "Based on retrieved information [#1]..."}
```

### Get Chat History
```bash
GET /chat/history
Authorization: Bearer <your-jwt-token>

# Response: [{"question": "...", "answer": "...", "created_at": "..."}]
```

---

## 🔧 Key Features

### Performance Optimizations
- **SQLite WAL Mode**: Optimized for concurrent reads
- **Service Caching**: Reusable Semantic Kernel services
- **ORJSON Responses**: Fast JSON serialization
- **GZip Compression**: Reduced bandwidth usage

### Security Features
- **JWT Authentication**: Stateless user sessions
- **Secret Redaction**: Automatic sanitization of sensitive data in chat history
- **CORS Configuration**: Configurable cross-origin policies
- **Password Hashing**: Bcrypt with salt

### RAG Enhancements
- **Hybrid Search**: Vector similarity + semantic ranking
- **Function Calling**: Automatic retrieval integration via Semantic Kernel
- **Context Management**: Smart conversation history truncation
- **Error Handling**: Graceful service unavailability responses

---

## 🔍 System Prompt
The RAG assistant follows strict guidelines:
- Answers based only on retrieved chunks `[#n]` and chat history
- Compensates for user typos by matching intended meaning
- Cites sources for all factual statements
- Handles multi-part questions by answering supported parts
- Never fabricates information outside retrieved context

---

## 📝 Notes
- Chat history is cached per user with automatic secret redaction
- ServiceBundle instances are cached per `service_id` for performance
- Vector retrieval uses top-k=50 with semantic reranking
- Database uses optimized SQLite settings for production workloads
- All responses use ORJSON for improved serialization performance