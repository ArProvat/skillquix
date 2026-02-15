FROM python:3.11-slim As builder

RUN sed -i 's/ main$/ main contrib non-free non-free-firmware/' /etc/apt/sources.list.d/debian.sources && \
     apt-get update && \
     apt-get install -y --no-install-recommends build-essential ffmpeg ca-certificates && \
     rm -rf /var/lib/apt/lists/*

WORKDIR /app 

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
     pip install --no-cache-dir -r requirements.txt


FROM python:3.11-slim

RUN sed -i 's/ main$/ main contrib non-free non-free-firmware/' /etc/apt/sources.list.d/debian.sources && \
     apt-get update && \
     apt-get install -y --no-install-recommends build-essential ffmpeg ca-certificates && \
     rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]