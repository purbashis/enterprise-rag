FROM node:24-alpine AS frontend-build

WORKDIR /workspace/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FRONTEND_DIST=/app/frontend/dist \
    DATA_PATH=/app/data \
    VECTOR_STORE_PATH=/app/vector_store \
    MEMORY_DB_PATH=/app/data/memory.sqlite3

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY --from=frontend-build /workspace/frontend/dist ./frontend/dist

RUN useradd --create-home --shell /usr/sbin/nologin app \
    && mkdir -p /app/data /app/vector_store \
    && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
