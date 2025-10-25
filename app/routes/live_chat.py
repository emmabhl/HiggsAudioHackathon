from app.services.semantic_search_service import semantic_search_notes
from flask import Blueprint, request, abort, Response
from app.services import transcription as T
from app.services.rag_service import get_rag_summary
from app.services.text_gen_service import get_audio_response
import io, subprocess

NOTES_DIR = 'app/static/notes'
bp = Blueprint('live_chat', __name__, url_prefix='/live_chat')

@bp.route('/response', methods=['POST'])
def response():
    ctype = (request.headers.get('Content-Type') or '').lower()
    if not (ctype.startswith('audio/') or ctype == 'application/octet-stream'):
        abort(400, description="Send raw audio blob in the request body with Content-Type audio/* or application/octet-stream.")

    # Read raw blob -> WAV bytes
    incoming = request.get_data(cache=False)
    if not incoming:
        abort(400, description="Empty audio payload.")
    wav_bytes = _to_wav_bytes(incoming)

    # In-memory file-like for transcriber
    wav_io = io.BytesIO(wav_bytes)
    wav_io.name = "input.wav"
    query = T.process_audio("input.wav")
    matching_notes = semantic_search_notes(query)

    if len(query) == 0:
        summary = ""
    else:
        # Call the semantic search service to find matching notes
        summary = get_rag_summary(query, matching_notes)

    output_audio = get_audio_response(summary)

    return Response(output_audio, mimetype='audio/wav')

def _to_wav_bytes(input_audio: bytes) -> bytes:
    """Convert arbitrary audio blob -> WAV (pcm_s16le, mono, 24 kHz) using ffmpeg."""
    proc = subprocess.run(
        [
            "ffmpeg",
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
