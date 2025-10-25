import chromadb
import numpy as np
import librosa  # or torchaudio
from sentence_transformers import SentenceTransformer
from huggingface_hub import hf_hub_download
import base64
import openai, os, io
import soundfile as sf
from pydub import AudioSegment
from tqdm import tqdm



BOSON_API_KEY = os.getenv("BOSON_API_KEY")

print("Loading tokenizer")
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

print("Loading chromadb")
client = chromadb.PersistentClient(path="vec_database/audio_db")
collection = client.get_or_create_collection(name="text_embeddings")

bosonclient = openai.Client(
    api_key=BOSON_API_KEY,
    base_url="https://hackathon.boson.ai/v1"
)

print("Loading data")
repo_id = "ofarrelle/higgs-hackathon-2025"
wav_folder = "beethoven/wavs"
filenames = [f"{str(i).zfill(2)}.wav" for i in range(1, 6)]

filepaths = []
for name in filenames:
    file_path = hf_hub_download(
        repo_id=repo_id, 
        filename=f"{wav_folder}/{name}",
        repo_type="dataset"  # change to "model" if the repo is a model repo
    )
    filepaths.append(file_path)
audios = []
# for i in filepaths:
#     audios.append(AudioSegment.from_wav(i))

audios.append(AudioSegment.from_wav(filepaths[0]))
chunk_size = 10000
file_format = "wav"

audio_base64 = []

def segment_to_base64(seg, fmt):
    # normalize + mono + resample for better ASR stability
    buf = io.BytesIO()
    seg.export(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

for audio in audios:
    for ms in range(0, len(audio), chunk_size):
        audio_base64.append(segment_to_base64(audio[ms:ms+chunk_size], file_format))

def recognize_audio(chunk):
   
    system_prompt = (
        "You are an AI assistant for audio understanding.\n"
        "Process the entire audio file, even if there are silent sections.\n"
        "Provide accurate transcription and any relevant context."
    )
    
    response = bosonclient.chat.completions.create(
        model="higgs-audio-understanding-Hackathon",  # Use understanding model
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": chunk,
                            "format": "wav"
                        }
                    },
                ]
            }
        ],
        max_completion_tokens=4096,
        temperature=0,
    )
    
    # Extract transcription
    transcription = response.choices[0].message.content
    
    return transcription

print("Tokenizing (embedding) and adding to vdb...")

for i, chunk in enumerate(tqdm(audio_base64)):
    # Convert to text
    text_info = recognize_audio(chunk)
    embedding = model.encode(text_info)

    collection.add(
        ids=[f"audio_{i}"],
        embeddings=[embedding],
        documents=[text_info],
        metadatas=[{"segment": i}]
    )
