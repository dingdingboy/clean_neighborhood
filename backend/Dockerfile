FROM python:3.11-slim

WORKDIR /app

# Configure pip to use Alibaba Cloud mirror (PRC)
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com

# Install Python dependencies (without system packages)
COPY pyproject.toml .
RUN pip install --no-cache-dir -e "."

# Copy application code
COPY app/ ./app/
COPY celery_worker/ ./celery_worker/
COPY ai/ ./ai/

# Create storage directory
RUN mkdir -p storage/uploads storage/processed

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
