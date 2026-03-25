FROM python:3.11-slim

WORKDIR /app

# Зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Код бота
COPY . .

# HuggingFace Spaces требует порт 7860
EXPOSE 7860

CMD ["python", "main.py"]
