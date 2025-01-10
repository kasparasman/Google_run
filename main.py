from fastapi import FastAPI
from routers import chat, speech
import os
from fastapi.middleware.cors import CORSMiddleware

openai_key = os.getenv('OPENAI_API_KEY')


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Allow cookies and authentication
    allow_methods=["*"],    # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],    # Allow all headers
)

# Include all feature routers
app.include_router(chat.router, prefix="/chat")
app.include_router(speech.router, prefix="/speech")


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
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
# Lambda handler
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))