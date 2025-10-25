import os
from werkzeug.utils import secure_filename
from app.services.transcription import process_audio
from app.services.rag_service import get_rag_summary
from app.services.notes_service import load_all_notes

def process_question(audio_file):
    """
    Process an audio question file:
    1. Save the audio temporarily
    2. Transcribe it to text
    3. Use RAG to find relevant context and generate an answer
    4. Clean up temporary file
    5. Return the question and answer
    """
    try:
        # Save audio file temporarily
        filename = secure_filename(audio_file.filename)
        temp_path = os.path.join('app/static/temp', filename)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        audio_file.save(temp_path)
        
        # Transcribe audio to text
        question_text = process_audio(temp_path)
        
        # Get answer using RAG
        # First load all notes to provide context
        all_notes = load_all_notes()
        answer = get_rag_summary(question_text, all_notes)
        
        # Clean up
        os.remove(temp_path)
        
        return {
            'question': question_text,
            'answer': answer
        }
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e