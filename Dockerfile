# Stage 1: Build dependencies and package wheels
FROM python:3.12-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y build-essential

# Install pip and other build tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements.txt and install dependencies as wheels
COPY requirements.txt /app/
RUN pip wheel --no-cache-dir --wheel-dir wheels -r requirements.txt

# Stage 2: Runtime image
FROM python:3.12-slim AS runner
WORKDIR /app

# Copy the pre-built wheels and application code
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install wheels (dependencies)
RUN pip install --no-cache-dir /wheels/*

# Create directory structure
RUN mkdir -p /app/routers
RUN mkdir -p /app/vectorstore
COPY ffmpeg/ffmpeg /usr/local/bin/ffmpeg
COPY ffmpeg/ffprobe /usr/local/bin/ffprobe
# Copy application files
COPY vectorstore/ /app/vectorstore/

COPY main.py /app/
COPY routers/__init__.py /app/routers/
COPY routers/chat.py /app/routers/
COPY routers/chatbot_logic.py /app/routers/
COPY routers/speech.py /app/routers/
COPY voice.json /app/



# Expose the port the app runs on
EXPOSE 8080

# Command to run the server
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1
