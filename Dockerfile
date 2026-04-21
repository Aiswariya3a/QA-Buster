FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY database.py .
COPY ingest.py .
COPY llm_worker.py .
COPY main.py .
COPY static/ ./static/

# Create database directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "main.py"]
