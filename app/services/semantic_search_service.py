from app.services.notes_service import load_all_notes, load_note_ids
from pymilvus import Collection
from sentence_transformers import SentenceTransformer

print('Called')
collection_name = "journal_notes"
client = Collection("journal_notes")
encoder = SentenceTransformer("BAAI/bge-base-en-v1.5")

def semantic_search_notes(query, threshold=0.5):
    """
    Perform a semantic search on the saved notes based on the query.

    Args:
        query (str): The search query.

    Returns:
        list: A list of matching notes.
    """
    # In practice, you'd use a proper model like a RAG pipeline, or a semantic search tool like FAISS or ElasticSearch.

    search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
    results = client.search(
        data=[encoder.encode(query).tolist()],
        anns_field="embedding",
        param=search_params,
        limit=10
    )

    matching_ids = [hit.id for hit in results[0] if hit.score > threshold]
    print([hit.score for hit in results[0]])
    matching_notes = load_note_ids(matching_ids)

    return matching_notes