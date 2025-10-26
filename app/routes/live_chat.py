# app/routes/live_chat.py
import io
import os
import datetime
import base64
from flask import Blueprint, request, abort, Response, jsonify
from app.services import transcription as T
from app.services.semantic_search_service import semantic_search_notes
from app.services.rag_service import get_rag_summary
from app.services.text_gen_service import get_audio_response, _to_wav_bytes

bp = Blueprint('live_chat', __name__, url_prefix='/api')

@bp.route('/chat', methods=['POST'])
def chat():
    message = request.json.get('message')
    if not message:
        return jsonify({'error': 'No message provided'}), 400

    # Utiliser le message pour chercher dans les notes
    matching_notes = semantic_search_notes(message)
    response = get_rag_summary(message, matching_notes, markdown=False)
    
    if not response:
        response = "I am sorry, I do not have enough information to answer that."
    
    # Générer l'audio de la réponse
    import base64
    audio_response = get_audio_response(response)
    
    # Encoder l'audio en base64
    audio_b64 = base64.b64encode(audio_response).decode('utf-8') if isinstance(audio_response, bytes) else base64.b64encode(audio_response.encode()).decode('utf-8')
    
    return jsonify({
        'response': response,
        'audioUrl': f'data:audio/wav;base64,{audio_b64}'
    })

@bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    
    # IMPORTANT: transcode whatever the browser recorded (likely audio/webm) -> WAV
    incoming = audio_file.read()
    wav_bytes = _to_wav_bytes(incoming)

    wav_io = io.BytesIO(wav_bytes)
    wav_io.name = "input.wav"

    query = T.process_audio(wav_io)  # expects a WAV file-like
    
    return jsonify({'transcription': query})
    
