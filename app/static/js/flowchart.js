class KnowledgeMap {
    constructor(container) {
        this.container = container;
        this.nodes = new Map();
        this.edges = new Map();
        this.width = container.clientWidth;
        this.height = container.clientHeight;
        this.initializeSVG();
        this.initializeSimulation();

        // Redimensionner le SVG quand la fenêtre change de taille
        window.addEventListener('resize', () => {
            this.width = container.clientWidth;
            this.height = container.clientHeight;
            this.svg
                .attr('width', this.width)
                .attr('height', this.height);
            this.simulation
                .force('center', d3.forceCenter(this.width / 2, this.height / 2))
                .force('bounds', () => this.boundingForce());
            this.simulation.alpha(1).restart();
        });
    }

    initializeSVG() {
        // Créer l'élément SVG avec D3.js
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .classed('knowledge-map', true);

        // Définir les marqueurs de flèche pour les liens
        this.svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', 35)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#999');

        // Ajouter un groupe pour le zoom
        this.g = this.svg.append('g');

        // Ajouter le comportement de zoom
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });

        this.svg.call(this.zoom);
    }

    initializeSimulation() {
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(150))
            .force('charge', d3.forceManyBody().strength(-100))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(60))
            .force('bounds', () => this.boundingForce())
            .on('tick', () => this.tick());
            
        // Ajout d'une marge pour éviter que les nœuds ne touchent les bords
        this.margin = 20;
    }

    // Ajouter un nœud au flowchart
    addNode(id, label, data = {}) {
        if (!this.nodes.has(id)) {
            const node = { 
                id, 
                label, 
                ...data,
                x: this.width / 2 + (Math.random() - 0.5) * 100,
                y: this.height / 2 + (Math.random() - 0.5) * 100
            };
            this.nodes.set(id, node);
            this.updateVisualization();
        }
    }

    // Ajouter une connexion entre deux nœuds
    addEdge(fromId, toId, label = '') {
        const edgeId = `${fromId}-${toId}`;
        if (!this.edges.has(edgeId) && this.nodes.has(fromId) && this.nodes.has(toId)) {
            this.edges.set(edgeId, { 
                id: edgeId,
                source: this.nodes.get(fromId),
                target: this.nodes.get(toId),
                label 
            });
            this.updateVisualization();
        }
    }

    tick() {
        // Mettre à jour les positions des liens
        this.g.selectAll('.link')
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        // Mettre à jour les positions des nœuds
        this.g.selectAll('.node')
            .attr('transform', d => `translate(${d.x},${d.y})`);
    }

    // Mettre à jour la visualisation
    updateVisualization() {
        const nodesArray = Array.from(this.nodes.values());
        const linksArray = Array.from(this.edges.values());

        // Mettre à jour les liens
        const links = this.g.selectAll('.link')
            .data(linksArray, d => d.id);

        links.exit().remove();

        const linksEnter = links.enter()
            .append('line')
            .attr('class', 'link')
            .style('stroke', '#999')
            .style('stroke-width', d => d.data?.strength || 2)
            .style('stroke-opacity', 0.6)
            .attr('marker-end', 'url(#arrowhead)');

        // Mettre à jour les nœuds
        const nodes = this.g.selectAll('.node')
            .data(nodesArray, d => d.id);

        nodes.exit().remove();

        const nodesEnter = nodes.enter()
            .append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', (event, d) => this.dragstarted(event, d))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragended(event, d)))
            .on('click', (event, d) => this.nodeClicked(d));

        nodesEnter.append('circle')
            .attr('r', d => d.data?.size || 30)
            .style('fill', d => getTagColor(d.label))
            .style('stroke', 'var(--glass-border)')
            .style('stroke-width', 2)
            .style('cursor', 'pointer');

        nodesEnter.append('text')
            .text(d => d.label)
            .attr('text-anchor', 'middle')
            .attr('dy', '.35em')
            .style('fill', 'var(--text-primary)')
            .style('font-size', '12px')
            .style('pointer-events', 'none');

        // Mettre à jour la simulation
        this.simulation.nodes(nodesArray);
        this.simulation.force('link').links(linksArray);
        this.simulation.alpha(1).restart();
    }

    dragstarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragended(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    boundingForce() {
        this.simulation.nodes().forEach(node => {
            // Calculer le rayon effectif du nœud (y compris la marge)
            const r = (node.data?.size || 30) + this.margin;
            
            // Contraindre les positions x et y
            node.x = Math.max(r, Math.min(this.width - r, node.x));
            node.y = Math.max(r, Math.min(this.height - r, node.y));
        });
    }

    nodeClicked(node) {
        // Rediriger vers la galerie de notes avec le tag sélectionné
        window.location.href = `/note_gallery?tag=${encodeURIComponent(node.label)}`;
    }
}

// Ajouter les styles CSS nécessaires
const style = document.createElement('style');
style.textContent = `
    .knowledge-map {
        background: transparent;
    }
    .node circle {
        transition: fill 0.3s ease, stroke-width 0.3s ease;
    }
    .node:hover circle {
        fill: var(--secondary-color);
        stroke-width: 3px;
    }
    .link {
        transition: stroke-width 0.3s ease, stroke-opacity 0.3s ease;
    }
    .link:hover {
        stroke-width: 3px;
        stroke-opacity: 1;
    }
`;
document.head.appendChild(style);

// Initialiser le flowchart
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('flowchart-container');
    if (!container) return;

    const knowledgeMap = new KnowledgeMap(container);

    // Charger les données initiales
    fetch('/api/knowledge-map')
        .then(response => response.json())
        .then(data => {
            // Ajouter d'abord tous les nœuds
            data.nodes.forEach(node => {
                knowledgeMap.addNode(node.id, node.label, node.data);
            });
            // Puis ajouter les connexions
            data.edges.forEach(edge => {
                knowledgeMap.addEdge(edge.from, edge.to, edge.label);
            });
        })
        .catch(error => {
            console.error('Error loading knowledge map:', error);
            // Ajouter des données d'exemple en cas d'erreur
            const topics = ['Python', 'JavaScript', 'Machine Learning', 'Web Development', 'Data Science'];
            topics.forEach((topic, i) => {
                knowledgeMap.addNode(i.toString(), topic);
                if (i > 0) {
                    knowledgeMap.addEdge((i-1).toString(), i.toString());
                }
            });
        });

    // Gérer les événements de redimensionnement
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            container.style.height = `${container.parentElement.clientHeight}px`;
        }, 250);
    });
});
