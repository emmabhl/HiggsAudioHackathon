from app.services.notes_service import load_all_notes, load_note_ids

import chromadb
from sentence_transformers import SentenceTransformer

print('Called')
collection_name = "journal_notes"
client = chromadb.Client()
encoder = SentenceTransformer("BAAI/bge-base-en-v1.5")

def semantic_search_notes(query, threshold=0.5, top_k=10):
    query_embedding = encoder.encode(query).tolist()

    collection = client.get_or_create_collection(name=collection_name)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["ids", "distances"]
    )

    matching_ids = []
    scores = results["distances"][0]
    ids = results["ids"][0]

    for idx, score in enumerate(scores):
        # Note: Chroma returns smaller distances = more similar (depending on metric)
        if score is not None and score < threshold:
            matching_ids.append(ids[idx])

    print(scores)
    matching_notes = load_note_ids(matching_ids)
    return matching_notes
