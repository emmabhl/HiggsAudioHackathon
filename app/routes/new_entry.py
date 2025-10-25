import datetime
import json
import os
import subprocess
import uuid
from pymilvus import Collection, FieldSchema, DataType, CollectionSchema
from flask import Blueprint, render_template, request, jsonify
from sentence_transformers import SentenceTransformer
from app.services import transcription as T
from app.services.transcription_information import get_title_summary_tags_from_transcription
from app.services.notes_service import load_note_ids


NOTES_DIR = 'app/static/notes'
bp = Blueprint('new_entry', __name__, url_prefix='/new_entry')

collection_name = "journal_notes"
client = Collection("journal_notes")
encoder = SentenceTransformer("BAAI/bge-base-en-v1.5")

def query_collection(query, collection_name="journal_notes"):
    """
    Perform a semantic search on the saved notes based on the query.
    """
    search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
    results = client.search(
        data=[encoder.encode(query).tolist()],
        anns_field="embedding",
        param=search_params,
        limit=5
    )

    matching_ids = [hit.id for hit in results[0]]
    matching_notes = load_note_ids(matching_ids)

    return matching_notes


def add_to_vectordb(note_id, summary, collection_name="journal_notes"):
    if not Collection(collection_name).is_empty:
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=encoder.get_sentence_embedding_dimension())
        ]
        schema = CollectionSchema(fields=fields, description="Journal notes for semantic search")
        collection = Collection(name=collection_name, schema=schema)

    embedding = encoder.encode([summary])[0].tolist()
    client.insert([
        {"id": note_id, "embedding": embedding}
    ])

def store_collection(data, collection_name="journal_notes"):
    """
    Store notes in the vector database.
    """
    if Collection(collection_name).is_empty:
        Collection(collection_name).drop()

    fields = [
        FieldSchema(name="id", dtype=DataType.STRING, is_primary=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=encoder.get_sentence_embedding_dimension())
    ]
    schema = CollectionSchema(fields=fields, description="Journal notes for semantic search")
    collection = Collection(name=collection_name, schema=schema)

    documents = []
    for item in data:
        title, formatted_text, tags = get_title_summary_tags_from_transcription(item)
        note_id = str(uuid.uuid4())

        documents.append(
            {
                "id": note_id,
                "embedding": encoder.encode([formatted_text])[0].tolist()
            }
        )

    client.insert(documents)




@bp.route('/', methods=['GET'])
def new_entry():
    return render_template('new_entry.html')

@bp.route('/stream_audio', methods=['POST'])
def stream_audio():
    audio_data = request.files['audio']
    transcript_chunk = "" #transcription.process_audio(audio_data)
    return jsonify({'transcription': transcript_chunk})

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
