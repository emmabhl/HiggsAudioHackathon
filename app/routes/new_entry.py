import datetime
import json
import os
import subprocess
import uuid
import chromadb
from chromadb.utils import embedding_functions
from flask import Blueprint, render_template, request, jsonify
from sentence_transformers import SentenceTransformer
from app.services import transcription as T
from app.services.transcription_information import get_title_summary_tags_from_transcription
from app.services.notes_service import load_note_ids


NOTES_DIR = 'app/static/notes'
bp = Blueprint('new_entry', __name__, url_prefix='/new_entry')

collection_name = "journal_notes"
client = chromadb.PersistentClient(path="chroma_data")


encoder = SentenceTransformer("BAAI/bge-base-en-v1.5")

def query_collection(query, collection_name="journal_notes", top_k=5):
    # embed query
    query_embedding = encoder.encode(query).tolist()

    # get or create the collection
    collection = client.get_or_create_collection(
        name=collection_name,
        # we are using external embedder so we can pass embedding_function=None
    )

    # perform query
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["ids", "documents", "metadatas"]
    )

    matching_ids = results["ids"][0]
    # optionally you can get documents or metadatas:
    # matching_docs = results["documents"][0]
    matching_notes = load_note_ids(matching_ids)

    return matching_notes


def add_to_vectordb(note_id, summary, collection_name="journal_notes", tags=None):
    collection = client.get_or_create_collection(name=collection_name)

    embedding = encoder.encode([summary])[0].tolist()

    # ensure string ID
    note_id = str(note_id)

    collection.add(
        ids=[note_id],
        embeddings=[embedding],
        metadatas=[{"tags": tags, "source": "upload_file"}] if tags is not None else [{"source": "upload_file"}],
        documents=[summary]
    )

import uuid

def store_collection(data, collection_name="journal_notes"):
    # If existing collection and you want to start fresh, you can delete:
    try:
        client.delete_collection(name=collection_name)
    except ValueError:
        pass

    collection = client.create_collection(
        name=collection_name,
        # embedding_function=None # we compute embeddings outside
    )

    ids = []
    embeddings = []
    metadatas = []
    documents = []

    for item in data:
        title, formatted_text, tags = get_title_summary_tags_from_transcription(item)
        note_id = str(uuid.uuid4())

        ids.append(note_id)
        embeddings.append(encoder.encode([formatted_text])[0].tolist())
        documents.append(formatted_text)
        metadatas.append({"title": title, "tags": tags})

    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=documents
    )

@bp.route('/', methods=['GET'])
def new_entry():
    return render_template('new_entry.html')

@bp.route('/stream_audio', methods=['POST'])
def stream_audio():
    audio_data = request.files['audio']
    transcript_chunk = "" #transcription.process_audio(audio_data)
    return jsonify({'transcription': transcript_chunk})

@bp.route('/upload_file', methods=['POST'])
def upload_file():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    if not audio_file.filename:
        return jsonify({'error': 'No file selected'}), 400

    # Générer un ID unique pour la note
    current_time = datetime.datetime.now()
    note_id = int(current_time.timestamp())
    
    # Créer le dossier pour sauvegarder la note
    save_path = os.path.join(NOTES_DIR, str(note_id))
    os.makedirs(save_path, exist_ok=True)

    # Sauvegarder le fichier audio original
    original_path = os.path.join(save_path, os.path.basename(audio_file.filename))
    audio_file.save(original_path)
    # Renamer le fichier uploadé en audio.wav
    os.rename(original_path, os.path.join(save_path, 'audio.wav'))

    # Convertir en WAV si nécessaire
    wav_path = os.path.join(save_path, 'audio.wav')
    subprocess.call(f'ffmpeg -y -i "{wav_path}" "{wav_path}"', shell=True)

    # Transcrire l'audio
    transcription = T.process_audio(wav_path)
    
    # Extraire le titre, le résumé et les tags
    title, summary, tags = get_title_summary_tags_from_transcription(transcription)
    
    # Créer les métadonnées
    datetime_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
    json_dict = {
        'id': str(note_id),
        'title': title,
        'summary': summary,
        'tags': tags,
        'transcription': transcription,
        'datetime': datetime_str,
        'original_filename': audio_file.filename
    }

    # Sauvegarder les métadonnées
    json_path = os.path.join(save_path, 'data.json')
    with open(json_path, 'w') as json_file:
        json.dump(json_dict, json_file, indent=4)

    # Ajouter à la base de données vectorielle
    add_to_vectordb(note_id, summary)

    return jsonify({'message': 'File uploaded and processed successfully', 'note_id': str(note_id)}), 200

@bp.route('/save_entry', methods=['POST'])
def save_entry():
    if 'audio' not in request.files or 'transcription' not in request.form:
        return jsonify({'error': 'Missing audio or transcription data'}), 400

    audio_data = request.files['audio']

    # Generate a unique note ID using the current timestamp (as an integer)
    current_time = datetime.datetime.now()
    note_id = int(current_time.timestamp())

    # Create a directory to store the note
    save_path = os.path.join(NOTES_DIR, str(note_id))
    os.makedirs(save_path, exist_ok=True)

    # Save the audio data
    audio_path = os.path.join(save_path, f'audio.webm')
    audio_data.save(audio_path)

    subprocess.call(f'ffmpeg -y -i {save_path}/audio.webm {save_path}/audio.wav', shell=True)

    transcription = T.process_audio(os.path.join(save_path, 'audio.wav'))

    # Extract the title, summary, and tags from the transcription
    title, summary, tags = get_title_summary_tags_from_transcription(transcription)

    # Create a human-readable datetime string
    datetime_str = current_time.strftime('%Y-%m-%d %H:%M:%S')

    # Save the JSON metadata
    json_dict = {
        'id': str(note_id),
        'title': title,
        'summary': summary,
        'tags': tags,
        'transcription': transcription,
        'datetime': datetime_str
    }

    json_path = os.path.join(save_path, f'data.json')
    with open(json_path, 'w') as json_file:
        json.dump(json_dict, json_file, indent=4)

    ## Add the note to the vector database
    add_to_vectordb(note_id, summary)

    # # Save the audio data
    # audio_data.seek(0)
    # audio_path = os.path.join(save_path, f'audio.wav')
    # audio_data.save(audio_path)

    # Additional logic such as saving to a database can be added here

    return jsonify({'message': 'Entry saved successfully', 'note_id': str(note_id)}), 200
