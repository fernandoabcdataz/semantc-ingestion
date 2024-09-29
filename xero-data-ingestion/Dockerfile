# Use the base Python image
FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and application code
COPY src/requirements.txt ./requirements.txt
COPY src/ ./src/

# Install Python dependencies (including gunicorn)
RUN pip install --no-cache-dir --no-user -r requirements.txt

# Create a non-root user
RUN adduser --disabled-password appuser
USER appuser

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/ || exit 1

# Run the application using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "src.main:app"]