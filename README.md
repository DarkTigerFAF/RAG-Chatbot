# 🤖 RAG-Chatbot (FastAPI + Groq)

## 📌 Overview
This project is a **Retrieval-Augmented Generation (RAG) Chatbot** built with **FastAPI** and **SQLAlchemy**.  
It provides:
- 🔐 **User authentication** with JWT (register/login)  
- 💬 **Chat endpoint** (protected, requires token)  
- 🕑 **Conversation history** stored per user  
- 🧠 **RAG pipeline** using Groq LLM + HuggingFace embeddings  

---

## ⚡ Tech Stack
- **Backend**: FastAPI  
- **Database**: SQLite (via SQLAlchemy ORM)  
- **Auth**: JWT (`python-jose`) + OAuth2PasswordBearer  
- **AI**:  
  - Groq API (`llama-3.1-8b-instant`)  
  - HuggingFace embeddings (`BAAI/bge-small-en-v1.5`)  
  - Semantic Kernel  

---

## 📂 Project Structure
```
app/
 ├── main.py               # FastAPI entrypoint
 ├── database.py           # DB session + Base
 ├── models.py             # SQLAlchemy models (User, History)
 ├── schemas.py            # Pydantic schemas
 ├── auth.py               # JWT utils, register/login
 ├── rag.py                # RAG pipeline
 └── routes/
      ├── auth_routes.py   # /register, /login
      └── chat_routes.py   # /chat, /history
.env                       # secrets and configs
requirements.txt
```

---

## 🗄 Database Models

### User
```python
id: int (PK)
username: str (unique)
hashed_password: str
history: relationship -> History[]
```

### History  
(Option A: role/content, Option B: question/answer)  

Current schema:
```python
id: int (PK)
user_id: int (FK -> users.id)
role: str (user/assistant)
content: str
timestamp: datetime
```

Alternative (simpler for QA):
```python
question: str
answer: str
```

---

## 🔐 Authentication Flow
1. `POST /auth/register` → Register new user  
2. `POST /auth/login` → Returns JWT token  
3. Use token as `Authorization: Bearer <token>`  
4. Protected routes depend on `get_current_user()`  

---

## 🚀 Endpoints

### Auth
- `POST /auth/register` → Create user  
- `POST /auth/login` → Get JWT  

### Chat
- `POST /chat` → Ask question (JWT required)  
- Runs RAG pipeline + saves history  

### History
- `GET /chat/history` → Returns user’s past Q&A  

---

## 🧠 RAG Pipeline
1. Embed docs with HuggingFace  
2. Embed query + cosine similarity  
3. Retrieve top docs  
4. Load last 7 history messages  
5. Send context + query to Groq LLM  
6. Save Q&A to database  

---

## ⚙️ Environment Variables (`.env`)
```ini
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_groq_key
OPENAI_API_BASE_URL=https://api.groq.com/openai/v1
JWT_SECRET=your_base64_secret
```

---

## ▶️ Running the Project
```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Run DB migrations (or auto-create tables)
alembic upgrade head

# 3. Start FastAPI
uvicorn app.main:app --reload
```

---

## 📌 Example Usage

### Register
```http
POST /auth/register
{
  "username": "alice",
  "password": "secret"
}
```

### Login
```http
POST /auth/login
→ { "access_token": "JWT...", "token_type": "bearer" }
```

### Chat
```http
POST /chat
Authorization: Bearer JWT...
{
  "query": "What is RAG?"
}
→ { "answer": "RAG combines retrieval with generation..." }
```

### History
```http
GET /chat/history
Authorization: Bearer JWT...
→ [
  {"question": "What is RAG?", "answer": "...", "created_at": "..."}
]
```
