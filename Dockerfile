# SOOD AI v5.0.0 - Mission Control Docker Engine
# ---------------------------------------------

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2 and high-speed data processing
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements followed by installation to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application architecture
COPY . .

# Expose the terminal's operational port
EXPOSE 8080

# Command to synchronize and launch the Mission Control server.
# Optimized: 2 Workers with 4 Threads each (Gthread) to minimize memory footprint 
# while maintaining high-concurrency performance for AI analysis.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--worker-class", "gthread", "app:app"]
