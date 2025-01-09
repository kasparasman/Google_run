from fastapi import FastAPI
from routers import chat, speech
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
# Lambda handler
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))