import openai
import base64
import os
import subprocess
import tempfile
import glob
import time

BOSON_API_KEY = os.getenv("BOSON_API_KEY")

def encode_audio_to_base64(file_path: str) -> str:
    """Encode audio file to base64 format."""
    with open(file_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode("utf-8")

client = openai.Client(
    api_key=BOSON_API_KEY,
    base_url="https://hackathon.boson.ai/v1"
)

def split_audio(input_path: str, chunk_length: int = 60, out_dir: str | None = None) -> list[str]:
    """Split input audio into chunks of chunk_length seconds using ffmpeg.
    Returns a sorted list of chunk file paths."""
    if out_dir is None:
        out_dir = os.path.join(tempfile.mkdtemp(prefix="audio_chunks_"))
    os.makedirs(out_dir, exist_ok=True)

    # Use ffmpeg segmenter
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-f", "segment",
        "-segment_time", str(chunk_length),
        "-reset_timestamps", "1",
        os.path.join(out_dir, "chunk%03d." + input_path.split(".")[-1])
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    chunks = sorted(glob.glob(os.path.join(out_dir, "chunk*." + input_path.split(".")[-1])))
    return chunks

def transcribe_chunk(chunk_path: str, prev_transcript: str | None = None, max_tokens: int = 2048) -> tuple[str, dict]:
    """Send one chunk to the model and return (transcribed_text, response_meta)."""
    audio_base64 = encode_audio_to_base64(chunk_path)
    file_format = chunk_path.split(".")[-1]

    # Keep only recent context to avoid huge messages
    prev_ctx = (prev_transcript[-4000:]) if prev_transcript else None

    messages = [
        {"role": "system", "content": "You are transcribing audio to text. Do not invent content."}
    ]
    if prev_ctx:
        messages.append({
            "role": "system",
            "content": "Already transcribed :\n" + prev_ctx + "\n\nFor the next audio chunk, continue the transcription after the text already provided and do not add repetitions."
        })
    messages.append({
        "role": "user",
        "content": [
            {
                "type": "input_audio",
                "input_audio": {
                    "data": audio_base64,
                    "format": file_format,
                },
            },
        ],
    })

    response = client.chat.completions.create(
        model="higgs-audio-understanding-Hackathon",
        messages=messages,
        max_completion_tokens=max_tokens,
        temperature=0.0,
    )

    # Extract text safely
    text = ""
    try:
        text = response.choices[0].message.content
    except Exception:
        text = ""

    meta = {
        "finish_reason": getattr(response.choices[0], "finish_reason", None),
        "usage": getattr(response, "usage", None),
        "raw": response
    }
    return text, meta

def transcribe_full_audio(audio_path: str, chunk_length: int = 5) -> str:
    """Split audio, transcribe chunks sequentially and return full transcription."""
    chunks = split_audio(audio_path, chunk_length=chunk_length)
    full_transcript = ""
    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i+1}/{len(chunks)}: {chunk}")
        chunk_text, meta = transcribe_chunk(chunk, prev_transcript=full_transcript)
        print("finish_reason:", meta["finish_reason"])
        # If model stopped because of length, attempt to continue for the same chunk
        if meta["finish_reason"] == "length":
            print("The chunk response was truncated; attempting to continue for this chunk...")
            # Provide the partial chunk_text as context and ask to continue the chunk
            cont_prompt = "\n".join([full_transcript, chunk_text])
            more_text, more_meta = transcribe_chunk(chunk, prev_transcript=cont_prompt)
            chunk_text += " " + more_text
            print("finish_reason (continuation):", more_meta["finish_reason"])

        # Append chunk transcription
        full_transcript = (full_transcript + " " + chunk_text).strip()
        # small pause to avoid rate limits
        time.sleep(0.5)

    return full_transcript

def transcribe(audio_path: str) -> str:
    final_text = transcribe_full_audio(audio_path, chunk_length=5)
    print("=== TRANSCRIPTION COMPLETE ===")
    print(final_text)
    return final_text