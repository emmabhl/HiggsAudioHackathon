import openai
import base64
import os

BOSON_API_KEY = os.getenv("BOSON_API_KEY")

def encode_audio_to_base64(file_path: str) -> str:
    """Encode audio file to base64 format."""
    with open(file_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode("utf-8")

client = openai.Client(
    api_key=BOSON_API_KEY,
    base_url="https://hackathon.boson.ai/v1"
)

# Transcribe audio
audio_path = "data/01.mp3"
audio_base64 = encode_audio_to_base64(audio_path)
file_format = audio_path.split(".")[-1]

response = client.chat.completions.create(
    model="higgs-audio-understanding-Hackathon",
    messages=[
        {"role": "system", "content": "Transcribe this audio for me."},
        {
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
        },
    ],
    max_completion_tokens=2048,
    temperature=0.0,
)

print(response.choices[0].message.content)