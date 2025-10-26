from collections import defaultdict
from app.services.notes_service import load_all_notes
from app.services.tags_service import get_tags_with_counts

def get_knowledge_map():
    """
    Génère une carte des connaissances basée sur les tags des notes.
    Les nœuds sont les tags, et les liens sont créés entre les tags qui apparaissent ensemble dans les mêmes notes.
    """
    # Récupérer tous les tags avec leurs occurrences
    tag_counts = get_tags_with_counts()
    
    # Créer un dictionnaire pour stocker les relations entre tags
    tag_relations = defaultdict(lambda: defaultdict(int))
    
    # Analyser toutes les notes pour trouver les relations entre tags
    all_notes = load_all_notes()
    for note in all_notes:
        tags = note.get('tags', [])
        # Pour chaque paire de tags dans la note
        for i, tag1 in enumerate(tags):
            for tag2 in tags[i+1:]:
                if tag1 in tag_counts and tag2 in tag_counts:
                    tag_relations[tag1][tag2] += 1
                    tag_relations[tag2][tag1] += 1
    
    # Créer les nœuds
    nodes = []
    for tag, count in tag_counts.items():
        if count > 0:  # Ne garder que les tags utilisés
            nodes.append({
                'id': tag,
                'label': tag,
                'data': {
                    'count': count,
                    'size': min(30 + count * 5, 60)  # Taille du nœud basée sur le nombre d'occurrences
                }
            })
    
    # Créer les liens
    edges = []
    processed_pairs = set()  # Pour éviter les doublons
    
    for tag1 in tag_relations:
        for tag2, weight in tag_relations[tag1].items():
            pair = tuple(sorted([tag1, tag2]))  # Créer une paire ordonnée pour éviter les doublons
            if pair not in processed_pairs:
                processed_pairs.add(pair)
                edges.append({
                    'from': tag1,
                    'to': tag2,
                    'label': str(weight),
                    'data': {
                        'weight': weight,
                        'strength': min(1 + weight * 0.5, 5)  # Épaisseur du lien basée sur le nombre de co-occurrences
                    }
                })
    
    return {
        'nodes': nodes,
        'edges': edges
    }