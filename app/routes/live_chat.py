# app/routes/live_chat.py
import io
from flask import Blueprint, request, abort, Response
from app.services import transcription as T
from app.services.semantic_search_service import semantic_search_notes
from app.services.rag_service import get_rag_summary
from app.services.text_gen_service import get_audio_response, _to_wav_bytes

bp = Blueprint('live_chat', __name__, url_prefix='/live_chat')

@bp.route('/response', methods=['POST'])
def response():
    ctype = (request.headers.get('Content-Type') or '').lower()
    if not (ctype.startswith('audio/') or ctype == 'application/octet-stream'):
        abort(400, description="Send raw audio blob in the request body with Content-Type audio/* or application/octet-stream.")

    incoming = request.get_data(cache=False)
    if not incoming:
        abort(400, description="Empty audio payload.")

    # IMPORTANT: transcode whatever the browser recorded (likely audio/webm) -> WAV
    wav_bytes = _to_wav_bytes(incoming)

    wav_io = io.BytesIO(wav_bytes)
    wav_io.name = "input.wav"

    query = T.process_audio(wav_io)  # expects a WAV file-like
    matching_notes = semantic_search_notes(query)
    summary = "" if not query.strip() else get_rag_summary(query, matching_notes, markdown=False)
    if summary == '':
        print('shit broken')
    print(summary)

    output_audio = get_audio_response(summary)  # should already be WAV bytes
    return Response(output_audio, mimetype='audio/wav')
