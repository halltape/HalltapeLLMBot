FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY bot.py big_rag.py rag_data.py /app/
COPY context/ /app/context/
COPY utils/ /app/utils/
COPY chromadb/ /app/chromadb/
COPY .env /app/.env


CMD ["python", "bot.py"]
