from flask import Blueprint, request, jsonify
from app.services.question_service import process_question

question_bp = Blueprint('question', __name__)

@question_bp.route('/api/ask_question', methods=['POST'])
def ask_question():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
        
    audio_file = request.files['audio']
    if not audio_file:
        return jsonify({'error': 'Empty audio file'}), 400
        
    try:
        result = process_question(audio_file)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500