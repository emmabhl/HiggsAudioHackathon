from faster_whisper import WhisperModel
import openai
import io
from pydub import AudioSegment
import os
import base64

model = WhisperModel("small", compute_type="int8", device="cpu")

def transcribe(wav_path: str) -> str:
    print("Transcription")
    segments, info = model.transcribe(wav_path, beam_size=5)
    segments = list(segments)
    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
    ret = "".join(segment.text for segment in segments)
    #ret = [segment.text for segment in segments]
    return ret

bosonclient = openai.Client(
    api_key=os.getenv("BOSON_API_KEY"),
    base_url="https://hackathon.boson.ai/v1"
)

def process_audio(audio_data):
    #return update_recording(audio_data)
    return transcribe(audio_data)


def transcribe2(audio_path: str, chunk_size: int = 10000) -> list[str]:
    
    def segment_to_base64(seg, fmt):
        # normalize + mono + resample for better ASR stability
        buf = io.BytesIO()
        seg.export(buf, format=fmt)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    
    file_format = audio_path.split(".")[-1]
    if file_format.lower() == "wav":
        audio = AudioSegment.from_wav(audio_path)
    elif file_format.lower() == "mp3":
        audio = AudioSegment.from_mp3(audio_path)
    else:
        raise ValueError("Unsupported audio format. Use WAV or MP3.")

    chunk_transcriptions = []

    for ms in range(0, len(audio), chunk_size):
        tmp = segment_to_base64(audio[ms:ms+chunk_size], file_format)
        transcr = recognize_audio(tmp)
        chunk_transcriptions.append(transcr)
            
    return chunk_transcriptions

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