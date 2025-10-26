// Fonction pour générer une couleur basée sur le texte du tag
function getTagColor(tag) {
    // Utiliser un hash simple pour générer un nombre à partir du texte
    let hash = 0;
    for (let i = 0; i < tag.length; i++) {
        hash = tag.charCodeAt(i) + ((hash << 5) - hash);
    }

    // Liste de couleurs prédéfinies avec un bon contraste
    const colors = [
        '#6366f1', // primary-color
        '#8b5cf6', // secondary-color
        '#3b82f6', // accent-color
        '#10b981', // success-color
        '#f59e0b', // warning-color
        '#ef4444', // error-color
        '#06b6d4', // cyan
        '#ec4899', // pink
        '#14b8a6', // teal
        '#f97316', // orange
        '#8b5cf6', // purple
        '#84cc16', // lime
    ];

    // Utiliser le hash pour sélectionner une couleur
    const index = Math.abs(hash) % colors.length;
    return colors[index];
}

// Fonction pour appliquer la couleur à tous les tags
function applyTagColors() {
    const tags = document.querySelectorAll('.badge');
    tags.forEach(tag => {
        const tagText = tag.textContent.trim();
        const color = getTagColor(tagText);
        tag.style.backgroundColor = color;
        tag.style.color = '#ffffff';
    });
}

// Appliquer les couleurs quand le DOM est chargé
document.addEventListener('DOMContentLoaded', applyTagColors);