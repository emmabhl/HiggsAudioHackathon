import openai, base64, os, io, wave

def get_audio_response(text_to_say, samplerate=24000):
    """
    Streams PCM16 audio from Boson and returns it as WAV bytes (in memory).
    """
    api_key = os.getenv("BOSON_API_KEY")
    if not api_key:
        raise RuntimeError("BOSON_API_KEY is not set.")

    client = openai.Client(api_key=api_key, base_url="https://hackathon.boson.ai/v1")

    messages = [
        {"role": "system", "content": "Convert the following text from the user into speech."},
        {"role": "user", "content": text_to_say},
    ]

    pcm_buf = bytearray()

    stream = client.chat.completions.create(
        model="higgs-audio-generation-Hackathon",
        messages=messages,
        modalities=["text", "audio"],
        audio={"format": "pcm16"},  # raw PCM16 chunks
        stream=True,
        max_completion_tokens=300,
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
