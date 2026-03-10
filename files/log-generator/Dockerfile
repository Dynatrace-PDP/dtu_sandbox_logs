FROM python:3.13-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create directory for config overrides (via ConfigMap)
RUN mkdir -p /etc/log-generator

# Set Python to run in unbuffered mode for real-time log output
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "-m", "src.main"]
