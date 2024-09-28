# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies globally
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Explicitly install Gunicorn
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY src/ ./src/

# Create a non-root user
RUN adduser --disabled-password appuser
USER appuser

# Expose port
EXPOSE 8080

# Define environment variables
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/ || exit 1

# Run the application using Gunicorn for better performance
CMD ["gunicorn", "-b", "0.0.0.0:8080", "src.main:app"]