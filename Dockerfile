FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY terabox_direct_api.py .

# Create downloads directory
RUN mkdir -p /app/downloads

EXPOSE 8000

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
CMD python -c "import requests; requests.get('http://localhost:8000/info', timeout=5)" || exit 1

# Start FastAPI
CMD ["uvicorn", "terabox_direct_api:app", "--host", "0.0.0.0", "--port", "8000"]
