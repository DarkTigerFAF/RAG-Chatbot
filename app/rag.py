import os, asyncio
from dotenv import load_dotenv
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.hugging_face import HuggingFaceTextEmbedding
from openai import AsyncOpenAI
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from .models import History

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

LLM_MODEL = "llama-3.1-8b-instant"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"

# -------------------
# Kernel + Services
# -------------------
kernel = sk.Kernel()

groq_client = AsyncOpenAI(
    api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1"
)

kernel.add_service(
    OpenAIChatCompletion(
        service_id="chat",
        ai_model_id=LLM_MODEL,
        async_client=groq_client,
    )
)

kernel.add_service(
    HuggingFaceTextEmbedding(service_id="embed", ai_model_id=EMBED_MODEL, device=0)
)

embed_service = kernel.get_service("embed")

# -------------------
# Demo Docs (replace with your source later)
# -------------------
documents = {
    "doc1": "Python is a high-level programming language created by Guido van Rossum in 1991.",
    "doc2": "Semantic Kernel is a lightweight SDK to mix programming languages with AI services.",
    "doc3": "RAG combines information retrieval with text generation for grounded AI responses.",
    "doc4": "Machine learning lets systems learn from experience without explicit programming.",
}
doc_texts = list(documents.values())


# -------------------
# RAG with history
# -------------------
async def rag_chat(db: Session, user_id: int, question: str) -> str:

    doc_embeddings = await asyncio.gather(
        *[embed_service.generate_embeddings(t) for t in doc_texts]
    )
    # 1. Embed query
    q_embed = await embed_service.generate_embeddings(question)

    # 2. Retrieve docs
    sims = cosine_similarity([q_embed], doc_embeddings)[0]
    top_idx = sims.argsort()[-2:][::-1]
    context = "\n\n".join(doc_texts[i] for i in top_idx)

    # 3. Get last 7 messages
    history = (
        db.query(History)
        .filter(History.user_id == user_id)
        .order_by(History.timestamp.desc())
        .limit(7)
        .all()[::-1]
    )
    hist_str = "\n".join([f"{m.role}: {m.content}" for m in history])

    # 4. Prompt template
    prompt = """
    Context:
    {{$context}}

    History:
    {{$history}}

    Question: {{$question}}
    Answer:
    """

    # 5. Run through SK
    result = await kernel.invoke_prompt(
        prompt=prompt,
        context=context,
        history=hist_str,
        question=question,
        service_id="chat",
    )
    answer = str(result)

    # 6. Save to DB
    db.add(History(user_id=user_id, role="user", content=question))
    db.add(History(user_id=user_id, role="assistant", content=answer))
    db.commit()

    return answer
