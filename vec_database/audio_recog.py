#!/usr/bin/env python3
"""
Audio Recognition with Higgs Audio Understanding
Handles MP3 input, adds noise to silence, and transcribes audio.
"""

import os
import base64
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from openai import OpenAI

# ────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────
BOSON_API_KEY = os.getenv("BOSON_API_KEY")
if not BOSON_API_KEY:
    raise ValueError("Set BOSON_API_KEY environment variable")

client = OpenAI(
    api_key=BOSON_API_KEY,
    base_url="https://hackathon.boson.ai/v1"
)

# ────────────────────────────────────────────────────────────
# Audio Preprocessing
# ────────────────────────────────────────────────────────────
def mp3_to_wav(mp3_path: str, wav_path: str) -> str:
    """Convert MP3 to WAV format (24kHz mono recommended)."""
    audio = AudioSegment.from_mp3(mp3_path)
    audio = audio.set_frame_rate(24000).set_channels(1)
    audio.export(wav_path, format="wav")
    return wav_path


def add_noise_to_silence(wav_path: str, output_path: str, noise_db: float = -60) -> str:
    """
    Add low-level noise to near-silent sections to prevent
    premature stop token generation.
    """
    data, sr = sf.read(wav_path)
    
    # Ensure mono
    if len(data.shape) > 1:
        data = data.mean(axis=1)
    
    # Calculate noise amplitude
    amplitude = np.max(np.abs(data))
    noise_amp = amplitude * (10 ** (noise_db / 20))
    
    # Add noise where signal is near zero
    silence_mask = np.abs(data) < 1e-4
    noise = np.random.uniform(-noise_amp, noise_amp, size=np.sum(silence_mask))
    data[silence_mask] += noise
    
    sf.write(output_path, data, sr)
    return output_path


# ────────────────────────────────────────────────────────────
# API Helper
# ────────────────────────────────────────────────────────────
def encode_audio_base64(path: str) -> str:
    """Encode audio file to base64 string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ────────────────────────────────────────────────────────────
# Main Recognition Function
# ────────────────────────────────────────────────────────────
def recognize_audio(audio_path: str, prompt: str = "Transcribe this audio.") -> str:
    """
    Recognize/transcribe audio using Higgs Audio Understanding.
    
    Args:
        audio_path: Path to MP3 or WAV file
        prompt: Optional instruction for the model
        
    Returns:
        Transcription text
    """
    # Step 1: Convert to WAV if needed
    if audio_path.lower().endswith(".mp3"):
        wav_path = audio_path.replace(".mp3", "_converted.wav")
        print(f"Converting {audio_path} to WAV...")
        mp3_to_wav(audio_path, wav_path)
    else:
        wav_path = audio_path
    
    # Step 2: Add noise to silence sections
    processed_path = wav_path.replace(".wav", "_processed.wav")
    print(f"Processing silence in {wav_path}...")
    add_noise_to_silence(wav_path, processed_path)
    
    # Step 3: Encode audio
    audio_b64 = encode_audio_base64(processed_path)
    
    # Step 4: Call Higgs Audio Understanding API
    print("Sending to Higgs Audio Understanding API...")
    
    system_prompt = (
        "You are an AI assistant for audio understanding.\n"
        "Process the entire audio file, even if there are silent sections.\n"
        "Provide accurate transcription and any relevant context."
    )
    
    response = client.chat.completions.create(
        model="higgs-audio-understanding-Hackathon",  # Use understanding model
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_b64,
                            "format": "wav"
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }
        ],
        modalities=["text", "audio"],
        max_completion_tokens=4096,
        temperature=0.7,
        top_p=0.95,
        stream=False,
        stop=[],  # Don't stop on silence
        extra_body={"top_k": 50}
    )
    
    # Step 5: Extract transcription
    transcription = response.choices[0].message.content
    
    # Cleanup temporary files
    if wav_path != audio_path:
        os.remove(wav_path)
    os.remove(processed_path)
    
    return transcription


# ────────────────────────────────────────────────────────────
# CLI Usage
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python audio_recognition.py <audio_file.mp3> [prompt]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    custom_prompt = sys.argv[2] if len(sys.argv) > 2 else "Transcribe this audio accurately."
    
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Processing: {input_file}")
    print(f"{'='*60}\n")
    
    try:
        result = recognize_audio(input_file, custom_prompt)
        
        print(f"\n{'='*60}")
        print("TRANSCRIPTION:")
        print(f"{'='*60}\n")
        print(result)
        
        # Save to text file
        output_file = input_file.replace(".mp3", "_transcription.txt").replace(".wav", "_transcription.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\n✓ Saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
