# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Ensures logs/output appear immediately in Docker logs
ENV PYTHONUNBUFFERED=1 

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies from pyproject.toml (without installing the package itself)
RUN pip install --upgrade pip && \
    pip install $(python -c "import tomllib; f = open('pyproject.toml', 'rb'); data = tomllib.load(f); print(' '.join([dep.replace(' ', '') for dep in data['project']['dependencies']]))")

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application using uvicorn directly
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
