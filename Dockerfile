FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia código e banco (IMPORTANTE pro Render)
COPY app /app/app
COPY data /app/data

# Render injeta a porta em $PORT, então não pode fixar 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]