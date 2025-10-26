from app.services.notes_service import load_all_notes, load_note_ids

import chromadb
from sentence_transformers import SentenceTransformer

# Preload model and client
collection_name = "chroma_data"
client = chromadb.PersistentClient(path=collection_name)
encoder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

def semantic_search_notes(query, threshold=1.5, top_k=10):
    # Initialize vector database and encoder

    query_embedding = encoder.encode(query).tolist()

    collection = client.get_or_create_collection(name=collection_name)
    print('Number of vectors in collection:', collection.count())

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    matching_ids = []
    scores = results["distances"][0]
    ids = results["ids"][0]

    for idx, score in enumerate(scores):
        # Note: Chroma returns smaller distances = more similar (depending on metric)
        print(f"ID: {ids[idx]}, Score: {score}")
        if score is not None and score < threshold:
            matching_ids.append(ids[idx])

    matching_notes = load_note_ids(matching_ids)
    return matching_notes