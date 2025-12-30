# big_rag.py
from pathlib import Path
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = BASE_DIR / "chromadb"

# Тот же самый эмбеддинг, что в rag_data.py
emb = HuggingFaceEmbeddings(
    model_name="ai-forever/ru-en-RoSBERTa",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

# Подключаемся к уже созданной базе
db = Chroma(
    persist_directory=str(CHROMA_DIR),
    embedding_function=emb,
)

retriever = db.as_retriever(search_kwargs={"k": 6})


def build_context(query: str) -> str:
    """
    Ищем релевантные куски из prompt_markdown.md и
    собираем их в один текстовый блок.
    """
    docs = retriever.get_relevant_documents(query)
    if not docs:
        return ""

    chunks = [d.page_content for d in docs]
    context = "\n\n---\n\n".join(chunks)
    # На всякий — обрежем, чтобы не раздувать system_prompt
    return context[:8000]