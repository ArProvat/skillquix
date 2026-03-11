FROM python:3.11-slim AS builder

# Install build deps only in builder — NOT copied to final image
RUN apt-get update && \
     apt-get install -y --no-install-recommends \
          build-essential \
          gcc \
          ca-certificates \
     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# ✅ CPU-only torch — saves ~1.5GB
RUN pip install --no-cache-dir --upgrade pip && \
     pip install --no-cache-dir \
          torch==2.2.0+cpu \
          --index-url https://download.pytorch.org/whl/cpu && \
     pip install --no-cache-dir -r requirements.txt && \
     pip install --no-cache-dir duckduckgo-search curl-cffi


# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ✅ Runtime only needs ffmpeg + ca-certificates — NOT build-essential
RUN apt-get update && \
     apt-get install -y --no-install-recommends \
          ffmpeg \
          ca-certificates \
     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin


COPY . .

EXPOSE 8888

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8888"]