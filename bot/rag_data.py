from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Путь до файла или папки с документами для RAG
# Можно подставить .md или .json — скрипт возьмёт оба.
SOURCE_PATH = Path("context")
# Куда сохранять Chroma
PERSIST_DIR = "./chromadb"
# Какие расширения индексируем
ALLOWED_SUFFIXES = {".md", ".json"}


def load_texts(source_path: Path):
    """Читает один файл или все файлы нужных расширений из папки."""
    if source_path.is_file():
        print(f"Используем один файл: {source_path}")
        return [source_path.read_text(encoding="utf-8")]

    base = Path(source_path)
    files = [p for p in base.rglob("*") if p.suffix.lower() in ALLOWED_SUFFIXES]

    print(f"Используем папку: {source_path}. Найдено файлов: {len(files)}")
    return [p.read_text(encoding="utf-8") for p in files]


if __name__ == "__main__":
    # ---- 1. Загружаем сырой текст ----
    raw_texts = load_texts(SOURCE_PATH)

    if not raw_texts:
        raise RuntimeError("Не нашли ни одного текста для индексации")

    # ---- 2. Режем на чанки ----
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=True,
    )

    docs = []
    for t in raw_texts:
        chunks = splitter.split_text(t)
        docs.extend(chunks)

    print(f"Всего чанков: {len(docs)}")

    emb = HuggingFaceEmbeddings(
        model_name="ai-forever/ru-en-RoSBERTa",
        model_kwargs={"device": "cpu"},  # или "cuda"
        encode_kwargs={"normalize_embeddings": True},
    )

    # ---- 4. Создаём Chroma без метаданных ----
    db = Chroma.from_texts(
        texts=docs,
        embedding=emb,
        persist_directory=PERSIST_DIR,
    )

    print(f"✅ Готово! Chroma сохранена в {PERSIST_DIR}")
