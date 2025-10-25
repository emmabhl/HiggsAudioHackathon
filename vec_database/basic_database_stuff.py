import chromadb
import numpy as np
import librosa  # or torchaudio
from higgs_audio.boson_multimodal.audio_processing.higgs_audio_tokenizer import load_higgs_audio_tokenizer
from huggingface_hub import hf_hub_download
import torch


print("Loading tokenizer")
tokenizer = load_higgs_audio_tokenizer("bosonai/higgs-audio-v2-tokenizer", device="mps")

print("Loading chromadb")
client = chromadb.PersistentClient(path="HiggsAudioHackathon/vec_database/audio_db")
collection = client.create_collection(name="audio_embeddings")

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

def chunk_waveform(wv, sr, chunk_seconds=10):
    chunk_size = int(chunk_seconds * sr)
    return [wv[i:i+chunk_size] for i in range(0, len(wv), chunk_size)]

print("Tokenizing (embedding) and adding to vdb...")
for idx, filepath in enumerate(filepaths):
    # Ensure waveform and sr match tokenizer expectation
    print("Loading file and chunks")
    wv, sr = librosa.load(filepath, sr=tokenizer.sampling_rate, mono=True)
    chunks = chunk_waveform(wv, sr, chunk_seconds=10)

    for i, chunk in enumerate(chunks):
        if len(chunk) < sr:  # optional: skip very short trailing audio
            continue
        codes = tokenizer.encode(chunk, sr)
        if hasattr(codes, "audio_codes"):
            code_tensor = codes.audio_codes
        else:
            code_tensor = codes

        # Suppose code_tensor shape is (n_codebooks, n_frames)
        # Mean pool over frames (axis=1) to get fixed length [n_codebooks]
        embedding = code_tensor.to(torch.float32).mean(axis=1)
        embedding = embedding.cpu().numpy().astype(float)

        print(f"Chunk size: {embedding.size}")
        collection.add(
            ids=[f"audio_{idx}_{i}"],
            embeddings=[embedding.tolist()],
            metadatas=[{"filename": filepath, "segment": i}]
        )
