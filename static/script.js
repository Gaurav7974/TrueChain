class GraphRAGApp {
    constructor() {
        this.socket = null;
        this.graph = null;
        this.currentSessionId = null;
        this.graphData = { nodes: [], links: [] };
        
        this.initializeElements();
        this.bindEvents();
        
        // Only initialize graph if libraries are loaded
        if (typeof ThreeForceGraph !== 'undefined' && typeof THREE !== 'undefined') {
            this.initializeGraph();
        } else {
            console.error('Three.js or ThreeForceGraph not available');
        }
    }
    
    initializeElements() {
        this.queryInput = document.getElementById('queryInput');
        this.searchBtn = document.getElementById('searchBtn');
        this.resultsContainer = document.getElementById('resultsContainer');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.sessionStatus = document.getElementById('sessionStatus');
    }
    
    bindEvents() {
        this.searchBtn.addEventListener('click', () => this.handleSearch());
        this.queryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch();
            }
        });
    }
    
    handleSearch() {
        const query = this.queryInput.value.trim();
        if (!query) return;
        
        this.startNewSearch(query);
    }
    
    startNewSearch(query) {
        // Reset UI
        this.resultsContainer.innerHTML = '';
        this.addStatusMessage('Searching sources...');
        
        // Generate new session ID
        this.currentSessionId = 'session_' + Date.now();
        this.sessionStatus.textContent = `Session: ${this.currentSessionId}`;
        
        // Show loading
        this.loadingIndicator.style.display = 'flex';
        this.searchBtn.disabled = true;
        
        // Create WebSocket connection
        this.connectWebSocket(query);
    }
    
    connectWebSocket(query) {
        // Close existing connection if any
        if (this.socket) {
            this.socket.close();
        }
        
        // Create new WebSocket connection
        const wsUrl = `ws://${window.location.host}/api/ws/stream/${this.currentSessionId}`;
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
            console.log('Connected to WebSocket');
            // Send the query
            this.socket.send(JSON.stringify({
                query: query,
                search_type: 'tavily'
            }));
        };
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.socket.onclose = () => {
            console.log('WebSocket connection closed');
            this.loadingIndicator.style.display = 'none';
            this.searchBtn.disabled = false;
        };
        
        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.addStatusMessage('Connection error. Please try again.');
            this.loadingIndicator.style.display = 'none';
            this.searchBtn.disabled = false;
        };
    }
    
    handleWebSocketMessage(data) {
        switch(data.event) {
            case 'status':
                this.addStatusMessage(data.message);
                break;
                
            case 'source':
                this.addResultItem(data);
                this.addNodeToGraph(data);
                break;
                
            case 'done':
                this.addStatusMessage(`Search completed. Found ${data.total_results} results.`);
                break;
                
            case 'error':
                this.addStatusMessage(`Error: ${data.message}`, 'error');
                break;
        }
    }
    
    addStatusMessage(message, type = 'info') {
        const statusDiv = document.createElement('div');
        statusDiv.className = `status-message ${type}`;
        statusDiv.textContent = message;
        this.resultsContainer.appendChild(statusDiv);
        
        // Scroll to bottom
        this.resultsContainer.scrollTop = this.resultsContainer.scrollHeight;
    }
    
    addResultItem(data) {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'result-item';
        
        resultDiv.innerHTML = `
            <a href="${data.url}" target="_blank" class="result-title">${data.title}</a>
            <div class="result-url">${data.url}</div>
            <div class="result-snippet">${data.snippet}</div>
        `;
        
        this.resultsContainer.appendChild(resultDiv);
        
        // Scroll to bottom
        this.resultsContainer.scrollTop = this.resultsContainer.scrollHeight;
    }
    
    initializeGraph() {
        const container = document.getElementById('graphContainer');
        const loadingElement = document.getElementById('graphLoading');
        const errorElement = document.getElementById('graphError');
        
        try {
            this.graph = ThreeForceGraph();
            
            // Apply configurations step by step to identify which one fails
            this.graph.graphData(this.graphData);
            
            // Check if nodeLabel method exists
            if (typeof this.graph.nodeLabel === 'function') {
                this.graph.nodeLabel('name');
            }
            
            if (typeof this.graph.nodeAutoColorBy === 'function') {
                this.graph.nodeAutoColorBy('group');
            }
            
            if (typeof this.graph.linkDirectionalParticles === 'function') {
                this.graph.linkDirectionalParticles(true);
            }
            
            if (typeof this.graph.linkDirectionalParticleSpeed === 'function') {
                this.graph.linkDirectionalParticleSpeed(0.003);
            }
            
            if (typeof this.graph.nodeVal === 'function') {
                this.graph.nodeVal('size');
            }
            
            if (typeof this.graph.nodeResolution === 'function') {
                this.graph.nodeResolution(16);
            }
            
            if (typeof this.graph.linkWidth === 'function') {
                this.graph.linkWidth(1);
            }
            
            if (typeof this.graph.linkColor === 'function') {
                this.graph.linkColor(() => '#999');
            }
            
            if (typeof this.graph.nodeRelSize === 'function') {
                this.graph.nodeRelSize(8);
            }
            
            if (typeof this.graph.warmupTicks === 'function') {
                this.graph.warmupTicks(30);
            }
            
            if (typeof this.graph.cooldownTicks === 'function') {
                this.graph.cooldownTicks(0);
            }
            
            // Remove loading indicator
            if (loadingElement) {
                loadingElement.style.display = 'none';
            }
            
            container.appendChild(this.graph.domElement());
            
            // Set initial camera position
            if (typeof this.graph.cameraPosition === 'function') {
                this.graph.cameraPosition({ z: 300 });
            }
        } catch (error) {
            console.error('Error initializing graph:', error);
            if (errorElement) {
                errorElement.style.display = 'block';
            }
        }
    }
    
    addNodeToGraph(data) {
        // Add query node if not exists
        if (!this.graphData.nodes.some(node => node.id === this.currentSessionId)) {
            this.graphData.nodes.push({
                id: this.currentSessionId,
                name: this.queryInput.value.substring(0, 30) + '...',
                type: 'query',
                group: 'query',
                size: 20
            });
        }
        
        // Add source node
        const nodeId = data.source_id;
        if (!this.graphData.nodes.some(node => node.id === nodeId)) {
            this.graphData.nodes.push({
                id: nodeId,
                name: data.title.substring(0, 30) + '...',
                url: data.url,
                type: 'source',
                group: 'source',
                size: 8
            });
        }
        
        // Add link from query to source
        const linkExists = this.graphData.links.some(link => 
            link.source === this.currentSessionId && link.target === nodeId
        );
        
        if (!linkExists) {
            this.graphData.links.push({
                source: this.currentSessionId,
                target: nodeId
            });
        }
        
        // Update graph
        if (this.graph) {
            this.graph.graphData(this.graphData);
        }
    }
}

// Initialize the app when the page loads
function initializeApp() {
    if (typeof ThreeForceGraph !== 'undefined' && typeof THREE !== 'undefined') {
        new GraphRAGApp();
    } else {
        console.error('Three.js or ThreeForceGraph not loaded');
        setTimeout(initializeApp, 100); // Retry after 100ms
    }
}

document.addEventListener('DOMContentLoaded', initializeApp);