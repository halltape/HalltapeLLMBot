### Как запускается бот?

## Предподготовка
1. Установить .venv
```python
python3 -m venv .venv
```
2. Активировать его
```python
source .venv/bin/activate
```
3. Установить все библиотеки
```python
pip install -r requirements.txt
```

## Собрать RAG

*RAG -- это база данных, на основе которой TelegramBot будет выдавать информацию.*

1. Проверить содержимое файла или добавить новую информацию в `bot/context/` (Можно в json или markdown. Парсит оба формата)
2. Поменять ПРОМПТ под свою задачу в `utils/prompt_instructions` (Описание для бота, кто он такой, его поведение)
2. Запустить сборку RAG в chromadb из папки `bot`
```python
python3 rag_data.py
```
3. RAG создан! Все работает. Если нужны изменения, вернуться к п.1 или 2


## Запускаем бота

1. Создать файлик `.env` и наполнить его типа:

TELEGRAM_TOKEN=********
DEEPSEEK_API_KEY=********
DEEPSEEK_MODEL=deepseek-chat


2. Выполнить команду
```bash
docker build -t ai_assistant . && docker rm -f bot && docker run --name bot -d ai_assistant
```


Модель для эмбединга взята отсюда
`https://huggingface.co/ai-forever/ru-en-RoSBERTa`
