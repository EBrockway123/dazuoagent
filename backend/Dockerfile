FROM python:3.11-slim

WORKDIR /app

# OS-level deps for building wheels (psycopg, etc.) — keep minimal.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first so Docker can cache the layer.
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["dazuoagent-api"]