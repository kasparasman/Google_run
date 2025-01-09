from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from google.cloud import speech
import json
import ffmpeg
import io
import subprocess
import logging

router = APIRouter()
def load_credentials(json_path):
    with open(json_path, "r") as f:
        return json.load(f)
def convert_to_linear16_ffmpeg(audio_blob):
    input_stream = io.BytesIO(audio_blob)
    output_stream = io.BytesIO()

    command = [
        "ffmpeg",
        "-i", "pipe:0",  # Read input from stdin
        "-ar", "44100",  # Set sample rate
        "-ac", "1",
        "-f", "wav",     # Explicitly set output format as WAV
        "-c:a", "pcm_s16le",  # Use LINEAR16 encoding
        "pipe:1",  # Write output to stdout
    ]
    try:
        process = subprocess.run(
            command,
            input=input_stream.read(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return process.stdout
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
        raise e
def transcribe_audio_with_credentials(audio_content, credentials):
    print(f"Audio content length: {len(audio_content)} bytes")
    print("Initializing SpeechClient...")
    # Use credentials directly
    client = speech.SpeechClient.from_service_account_info(credentials)

    # Configure the recognition request
    audio = speech.RecognitionAudio(content=audio_content)
    print(f"Audio object created: {audio}")

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,  # Match your audio format
        sample_rate_hertz=44100,  # Adjust if needed
        language_code="en-US",
    )
    print("Sending request to Google Cloud Speech-to-Text API...")

    # Perform transcription
    response = client.recognize(config=config, audio=audio)
    # Extract the transcription
    if response.results:
        print(f"Transcription result: {response.results[0].alternatives[0].transcript}")
        return response.results[0].alternatives[0].transcript
    else:
        return "No transcription available."

@router.post("/transcribe")
# Set up client with credentials
async def transcribe(audio: UploadFile = File(...)):
    print(audio.content_type)
    try:
        logging.info(f"Received file: {audio.filename}")

        audio_content = await audio.read()
        logging.info(f"File size: {len(audio_content)} bytes")
        print(f"File size: {len(audio_content)} bytes")  # Ensure the file is not empty
        converted_audio = convert_to_linear16_ffmpeg(audio_content)
        credentials = load_credentials("./voice.json")
        print(f"Converted audio size: {len(converted_audio)} bytes")
        transcription = transcribe_audio_with_credentials(converted_audio, credentials)

        # Return the transcription as JSON
        return {"message": transcription}
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
        return JSONResponse(content={"error": "Audio conversion failed."}, status_code=500)
    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)