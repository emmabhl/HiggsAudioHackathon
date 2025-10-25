import librosa
import torch
from higgs_audio.boson_multimodal.audio_processing.higgs_audio_tokenizer import load_higgs_audio_tokenizer
import chromadb
import io, base64, openai, os
from sentence_transformers import SentenceTransformer
from pydub import AudioSegment
# Load your query audio (same sample rate as your database!)
BOSON_API_KEY = os.getenv("BOSON_API_KEY")

model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

wv = AudioSegment.from_wav("misc_audiofiles/beethoven's last.wav")



def segment_to_base64(seg, fmt):
    # normalize + mono + resample for better ASR stability
    buf = io.BytesIO()
    seg.export(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

b64wv = segment_to_base64(wv, "wav")

bosonclient = openai.Client(
    api_key=BOSON_API_KEY,
    base_url="https://hackathon.boson.ai/v1"
)

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

text = recognize_audio(b64wv)

# If your DB uses chunking and mean pooling (as above), do the same:
query_embedding = model.encode(text)

client = chromadb.PersistentClient(path="vec_database/audio_db")
collection = client.get_or_create_collection(name="text_embeddings")


# Now query the Chroma collection for the most similar entry
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3,  # Adjust as needed
)

print(results)
# Examine what was retrieved:
for i in range(len(results['ids'][0])):
    print("Best match ID:", results["ids"][0][i])
    print("Best match document:", results.get("documents", [[None]])[0][i])
