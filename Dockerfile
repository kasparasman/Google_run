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

ENV LANGCHAIN_API_KEY="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"
ENV OPENAI_API_KEY="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"
ENV SECRET_KEY="4b850dafcbd64467e742effd987092f1cce3f5f06b11c04befa45f763eb23166"
ENV ELEVENLABS_API_KEY="sk_a9680d7cbc98ccd67dc607ea34de269ffadf525369bbe239"
ENV VOICE_ID="ultIypcv8jQiHOQCSlPH"

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
