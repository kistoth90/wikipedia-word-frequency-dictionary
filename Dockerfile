# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies directly (not as editable package)
RUN pip install --upgrade pip && \
    pip install \
    "fastapi[standard]>=0.128.7,<0.129.0" \
    "httpx>=0.28.1,<0.29.0" \
    "logger>=1.4,<2.0" \
    "beautifulsoup4>=4.14.3,<5.0.0" \
    "python-dotenv>=1.2.1,<2.0.0" \
    "lxml>=6.0.2,<7.0.0"

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/docs', timeout=5)"

# Run the application using uvicorn directly
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
