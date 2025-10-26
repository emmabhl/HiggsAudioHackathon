from flask import Blueprint, jsonify
from app.services.knowledge_map_service import get_knowledge_map

bp = Blueprint('knowledge_map', __name__)

@bp.route('/api/knowledge-map')
def knowledge_map():
    """
    Endpoint pour obtenir la carte des connaissances basée sur les tags.
    """
    return jsonify(get_knowledge_map())