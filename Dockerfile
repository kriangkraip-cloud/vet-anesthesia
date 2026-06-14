FROM python:3.11-slim

WORKDIR /app

# System libs required by matplotlib + Thai font packages for Railway server
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libfreetype6-dev \
    pkg-config \
    fonts-thai-tlwg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persistent directories (overridden by Docker volume)
RUN mkdir -p /app/data /app/exports

ENV DATA_DIR=/app/data
ENV PORT=8100

EXPOSE 8100

CMD ["sh", "-c", "python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
