# Dockerfile (single file, two targets via docker-compose targets)
FROM python:3.12-slim AS base
# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc libsqlite3-dev curl &&
rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# nn API target 
FROM base AS api
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app",
"--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
# nn Dashboard target 
FROM base AS dashboard
EXPOSE 8501
CMD ["streamlit", "run", "src/dashboard/app.py",
"--server.port=8501", "--server.address=0.0.0.0"]