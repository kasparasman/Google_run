from fastapi import APIRouter, Request, HTTPException, Query, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from elevenlabs.client import ElevenLabs
from .chatbot_logic import conversational_rag_chain
import os
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Move environment variables to main.py if you want to share them
REQUIRED_ENV_VARS = {
    "VOICE_ID": os.getenv("VOICE_ID"),
    "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "LANGCHAIN_API_KEY": os.getenv("LANGCHAIN_API_KEY")
}
for var_name, var_value in REQUIRED_ENV_VARS.items():
    if not var_value:
        logger.error(f"Missing required environment variable: {var_name}")
        raise ValueError(f"Missing required environment variable: {var_name}")
async def get_session_id(request: Request) -> str:
    try:
        data = await request.json()
        return data.get("session_id")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error processing request")


@router.post("")  # This becomes /chat when mounted
async def chat_handler(request: Request, session_id: str = Depends(get_session_id)):
    try:
        start_time = time.time()
        logger.debug(f"[TIMING] /chat: start={start_time:.4f}")
        data = await request.json()
        message = data.get("message", "")

        if not message:
            raise HTTPException(status_code=400, detail="No message provided.")

        chain_start = time.time()
        logger.debug(f"[TIMING] chain_invoke_start: {chain_start:.4f}")

        response = conversational_rag_chain.invoke(
            {"input": message},
            {"configurable": {"session_id": session_id}}
        )
        chain_end = time.time()
        chain_duration = chain_end - chain_start
        logger.debug(f"[TIMING] chain_invoke_end total={chain_duration:.4f}")



        answer = response.get("answer", "fail") if isinstance(response, dict) else "fail for else"
        end_time = time.time()
        total_duration = end_time - start_time
        logger.debug(f"[TIMING] /chat: end={end_time:.4f} (total={total_duration:.4f})")
        return {"response": answer, "response_time_seconds": total_duration, "chain_time_seconds": chain_duration}
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


@router.get("/tts")  # This becomes /chat/tts
def tts_endpoint(textToSpeak: str = Query(...)):
    client = ElevenLabs(api_key=REQUIRED_ENV_VARS["ELEVENLABS_API_KEY"])
    audio_stream = client.text_to_speech.convert_as_stream(
        text=textToSpeak,
        voice_id=REQUIRED_ENV_VARS["VOICE_ID"],
        model_id="eleven_flash_v2_5"
    )
    return StreamingResponse(audio_stream, media_type="audio/mpeg")