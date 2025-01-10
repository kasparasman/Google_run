from fastapi import FastAPI
from routers import chat, speech
import os
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 1) Load env vars from .env (if present)
load_dotenv()

app = FastAPI()

# 2) Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Allow cookies and authentication
    allow_methods=["*"],      # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],      # Allow all headers
)

# 3) Include feature routers
app.include_router(chat.router, prefix="/chat")
app.include_router(speech.router, prefix="/speech")

# 4) Simple check route showing which keys exist
@app.get("/test-keys")
async def test_keys():
    keys_status = {
        "LANGCHAIN_API_KEY": "✅ Found" if os.getenv("LANGCHAIN_API_KEY") else "❌ Missing",
        "OPENAI_API_KEY": "✅ Found" if os.getenv("OPENAI_API_KEY") else "❌ Missing",
        "SECRET_KEY": "✅ Found" if os.getenv("SECRET_KEY") else "❌ Missing",
        "ELEVENLABS_API_KEY": "✅ Found" if os.getenv("ELEVENLABS_API_KEY") else "❌ Missing",
        "VOICE_ID": "✅ Found" if os.getenv("VOICE_ID") else "❌ Missing"
    }

    # Add a summary count
    found_count = sum(1 for status in keys_status.values() if "Found" in status)
    keys_status["SUMMARY"] = f"{found_count}/5 keys found"
    return keys_status

# 5) Health route
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 6) Debug route that returns full environment variables (no masking!)
@app.get("/debug/env")
async def debug_env():
    """
    WARNING: This route prints FULL secrets!
    Use only in a non-production environment or for debugging.
    """
    return {
        "LANGCHAIN_API_KEY": os.getenv("LANGCHAIN_API_KEY", ""),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "SECRET_KEY": os.getenv("SECRET_KEY", ""),
        "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY", ""),
        "VOICE_ID": os.getenv("VOICE_ID", ""),
    }

# 7) Main entrypoint for local runs
if __name__ == "__main__":
    import uvicorn
    #  By default, Cloud Run sets $PORT=8080. Locally, you can set another port if you like.
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
