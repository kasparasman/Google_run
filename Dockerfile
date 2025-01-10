# Stage 1: Build dependencies and package wheels
FROM python:3.12-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install pip and other build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements.txt and install dependencies as wheels
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir wheels -r requirements.txt

# Stage 2: Runtime image
FROM python:3.12-slim AS runner
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy wheels and install dependencies
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Create directory structure
RUN mkdir -p /app/routers /app/vectorstore

# Copy application files (changed order to optimize caching)
COPY routers/ /app/routers/
COPY vectorstore/ /app/vectorstore/
COPY main.py .

# Port configuration for Cloud Run
ENV PORT 8080
EXPOSE ${PORT}

# Command to run the server
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1