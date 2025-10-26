import openai, base64, os, io, wave, subprocess
FFPEG = "C:/ffmpeg/bin/ffmpeg.exe" 

api_key = os.getenv("BOSON_API_KEY")
if not api_key:
    raise RuntimeError("BOSON_API_KEY is not set.")

client = openai.Client(api_key=api_key, base_url="https://hackathon.boson.ai/v1")

def get_audio_response(text_to_say, samplerate=24000):
    """
    Streams PCM16 audio from Boson and returns it as WAV bytes (in memory).
    """

    messages = [
        {"role": "system", "content": "Convert the following text from the user into speech. In english please"},
        {"role": "user", "content": text_to_say},
    ]

    pcm_buf = bytearray()

    stream = client.chat.completions.create(
        model="higgs-audio-generation-Hackathon",
        messages=messages,
        modalities=["text", "audio"],
        audio={"format": "pcm16"},  # raw PCM16 chunks
        stream=True,
        max_completion_tokens=10000,
    )

    for chunk in stream:
        delta = getattr(chunk.choices[0], "delta", None)
        audio = getattr(delta, "audio", None)
        if not audio or "data" not in audio:
            continue
        pcm_buf += base64.b64decode(audio["data"])

    # Convert to WAV format in-memory
    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(bytes(pcm_buf))

    return wav_io.getvalue()  # returns WAV bytes only

def _to_wav_bytes(input_audio: bytes) -> bytes:
    """Convert arbitrary audio blob -> WAV (pcm_s16le, mono, 24 kHz) using ffmpeg."""
    proc = subprocess.run(
        [
            FFPEG,
            "-hide_banner", "-loglevel", "error",
            "-i", "pipe:0",
            "-ac", "1",
            "-ar", "24000",
            "-f", "wav",
            "-acodec", "pcm_s16le",
            "pipe:1",
        ],
        input=input_audio,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,

    )
    return proc.stdout

def encode_audio_to_base64(file_path: str):
    with open(file_path, "rb") as audio_file: 
        return base64.b64encode(audio_file.read()).decode("utf-8")

def audio_to_txt(audio_path):
    audio = encode_audio_to_base64(audio_path)

    response = client.chat.completions.create(
        model="higgs-audio-understanding-Hackathon",
        messages=[
            {"role": "system", "content": "Transcribe this audio for me. If it sounds like music say there is music playing. If there is a pause, keep listening"},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio,
                            "format": 'wav',
                        },
                    },
                ],
            },
        ],
        max_completion_tokens=100000,
        temperature=0.0,
        stop=["<|end_of_text|>"],
    )
    
    return response.choices[0].message.content