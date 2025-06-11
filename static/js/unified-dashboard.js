/**
 * Unified Dashboard JavaScript
 * Handles all interactive functionality for the unified dashboard
 */

class UnifiedDashboard {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.searchDebounceTimer = null;
        this.activeTab = 'overview';
        this.agents = new Map();
        this.activityFeed = [];
        this.systemMetrics = {};
        
        this.init();
    }

    init() {
        this.setupWebSocket();
        this.setupTabNavigation();
        this.setupGlobalSearch();
        this.setupQuickExecute();
        this.setupAgentControls();
        this.setupMobileInteractions();
        this.setupEventListeners();
        this.startRealtimeUpdates();
    }

    // WebSocket Management
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.showNotification('Connected to real-time updates', 'success');
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showNotification('Connection error', 'error');
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.attemptReconnect();
        };
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            console.log(`Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`);
            
            setTimeout(() => {
                this.setupWebSocket();
            }, delay);
        } else {
            this.showNotification('Unable to connect to server. Please refresh the page.', 'error');
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'agent_update':
                this.updateAgentStatus(data.payload);
                break;
            case 'system_metrics':
                this.updateSystemMetrics(data.payload);
                break;
            case 'activity':
                this.addActivityItem(data.payload);
                break;
            case 'task_update':
                this.updateTaskStatus(data.payload);
                break;
            case 'notification':
                this.showNotification(data.payload.message, data.payload.type);
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    // Tab Navigation
    setupTabNavigation() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const targetTab = button.dataset.tab;
                this.switchTab(targetTab);
            });
        });
        
        // Handle browser back/forward
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.tab) {
                this.switchTab(e.state.tab, false);
            }
        });
        
        // Set initial tab from URL or default
        const urlParams = new URLSearchParams(window.location.search);
        const initialTab = urlParams.get('tab') || 'overview';
        this.switchTab(initialTab);
    }

    switchTab(tabName, updateHistory = true) {
        // Update active tab button
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.toggle('active', button.dataset.tab === tabName);
        });
        
        // Update visible content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });
        
        this.activeTab = tabName;
        
        // Update URL without page reload
        if (updateHistory) {
            const url = new URL(window.location);
            url.searchParams.set('tab', tabName);
            window.history.pushState({ tab: tabName }, '', url);
        }
        
        // Load tab-specific data
        this.loadTabData(tabName);
    }

    loadTabData(tabName) {
        switch (tabName) {
            case 'overview':
                this.loadOverviewData();
                break;
            case 'agents':
                this.loadAgentsData();
                break;
            case 'tasks':
                this.loadTasksData();
                break;
            case 'knowledge':
                this.loadKnowledgeData();
                break;
            case 'activity':
                this.loadActivityData();
                break;
        }
    }

    // Global Search
    setupGlobalSearch() {
        const searchInput = document.getElementById('global-search');
        const searchResults = document.getElementById('search-results');
        
        if (!searchInput) return;
        
        searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchDebounceTimer);
            const query = e.target.value.trim();
            
            if (query.length < 2) {
                searchResults.classList.add('hidden');
                return;
            }
            
            this.searchDebounceTimer = setTimeout(() => {
                this.performSearch(query);
            }, 300);
        });
        
        // Close search results when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                searchResults.classList.add('hidden');
            }
        });
        
        // Keyboard navigation for search results
        searchInput.addEventListener('keydown', (e) => {
            this.handleSearchKeyboardNavigation(e);
        });
    }

    async performSearch(query) {
        const searchResults = document.getElementById('search-results');
        searchResults.innerHTML = '<div class="search-loading">Searching...</div>';
        searchResults.classList.remove('hidden');
        
        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const results = await response.json();
            
            this.displaySearchResults(results);
        } catch (error) {
            console.error('Search error:', error);
            searchResults.innerHTML = '<div class="search-error">Search failed. Please try again.</div>';
        }
    }

    displaySearchResults(results) {
        const searchResults = document.getElementById('search-results');
        
        if (results.length === 0) {
            searchResults.innerHTML = '<div class="search-empty">No results found</div>';
            return;
        }
        
        const resultsHTML = results.map((result, index) => `
            <div class="search-result-item" data-index="${index}" data-type="${result.type}" data-id="${result.id}">
                <div class="search-result-icon">
                    <i class="fas fa-${this.getIconForType(result.type)}"></i>
                </div>
                <div class="search-result-content">
                    <div class="search-result-title">${this.highlightSearchTerm(result.title, result.query)}</div>
                    <div class="search-result-description">${this.highlightSearchTerm(result.description, result.query)}</div>
                    <div class="search-result-meta">${result.type} • ${result.timestamp}</div>
                </div>
            </div>
        `).join('');
        
        searchResults.innerHTML = resultsHTML;
        
        // Add click handlers to results
        searchResults.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                this.handleSearchResultClick(results[item.dataset.index]);
            });
        });
    }

    highlightSearchTerm(text, query) {
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    getIconForType(type) {
        const icons = {
            agent: 'robot',
            task: 'tasks',
            note: 'sticky-note',
            video: 'video',
            channel: 'broadcast-tower',
            book: 'book',
            habit: 'calendar-check'
        };
        return icons[type] || 'file';
    }

    handleSearchResultClick(result) {
        document.getElementById('search-results').classList.add('hidden');
        document.getElementById('global-search').value = '';
        
        // Navigate based on result type
        switch (result.type) {
            case 'agent':
                this.switchTab('agents');
                this.highlightAgent(result.id);
                break;
            case 'task':
                this.switchTab('tasks');
                this.scrollToTask(result.id);
                break;
            case 'note':
            case 'video':
            case 'channel':
                this.switchTab('knowledge');
                this.openKnowledgeItem(result.id, result.type);
                break;
            default:
                console.log('Unknown result type:', result.type);
        }
    }

    handleSearchKeyboardNavigation(e) {
        const searchResults = document.getElementById('search-results');
        const items = searchResults.querySelectorAll('.search-result-item');
        const currentActive = searchResults.querySelector('.search-result-item.active');
        
        let currentIndex = -1;
        if (currentActive) {
            currentIndex = parseInt(currentActive.dataset.index);
        }
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                if (currentIndex < items.length - 1) {
                    this.setActiveSearchResult(currentIndex + 1);
                }
                break;
            case 'ArrowUp':
                e.preventDefault();
                if (currentIndex > 0) {
                    this.setActiveSearchResult(currentIndex - 1);
                }
                break;
            case 'Enter':
                e.preventDefault();
                if (currentActive) {
                    currentActive.click();
                }
                break;
            case 'Escape':
                searchResults.classList.add('hidden');
                break;
        }
    }

    setActiveSearchResult(index) {
        const searchResults = document.getElementById('search-results');
        searchResults.querySelectorAll('.search-result-item').forEach((item, i) => {
            item.classList.toggle('active', i === index);
        });
    }

    // Quick Execute
    setupQuickExecute() {
        const quickExecuteBtn = document.getElementById('quick-execute-btn');
        const quickExecuteModal = document.getElementById('quick-execute-modal');
        const quickExecuteInput = document.getElementById('quick-execute-input');
        const quickExecuteSubmit = document.getElementById('quick-execute-submit');
        const quickExecuteClose = document.getElementById('quick-execute-close');
        
        if (!quickExecuteBtn || !quickExecuteModal) return;
        
        // Open modal
        quickExecuteBtn.addEventListener('click', () => {
            quickExecuteModal.classList.remove('hidden');
            quickExecuteInput.focus();
            this.loadCommandSuggestions();
        });
        
        // Close modal
        quickExecuteClose.addEventListener('click', () => {
            quickExecuteModal.classList.add('hidden');
            quickExecuteInput.value = '';
        });
        
        // Close on outside click
        quickExecuteModal.addEventListener('click', (e) => {
            if (e.target === quickExecuteModal) {
                quickExecuteModal.classList.add('hidden');
            }
        });
        
        // Submit command
        quickExecuteSubmit.addEventListener('click', () => {
            this.executeCommand(quickExecuteInput.value);
        });
        
        quickExecuteInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.executeCommand(quickExecuteInput.value);
            }
        });
        
        // Command suggestions
        quickExecuteInput.addEventListener('input', (e) => {
            this.updateCommandSuggestions(e.target.value);
        });
        
        // Keyboard shortcut (Ctrl+K or Cmd+K)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                quickExecuteBtn.click();
            }
        });
    }

    loadCommandSuggestions() {
        const suggestions = [
            { command: 'analyze', description: 'Analyze current system state' },
            { command: 'optimize', description: 'Optimize system performance' },
            { command: 'backup', description: 'Create system backup' },
            { command: 'sync', description: 'Sync all integrations' },
            { command: 'report', description: 'Generate status report' },
            { command: 'heal', description: 'Run self-healing diagnostics' },
            { command: 'update', description: 'Update all agents' },
            { command: 'restart', description: 'Restart specific agent' }
        ];
        
        this.displayCommandSuggestions(suggestions);
    }

    updateCommandSuggestions(input) {
        const suggestions = document.querySelectorAll('.command-suggestion');
        suggestions.forEach(suggestion => {
            const command = suggestion.dataset.command;
            const matches = command.toLowerCase().includes(input.toLowerCase());
            suggestion.style.display = matches ? 'block' : 'none';
        });
    }

    displayCommandSuggestions(suggestions) {
        const suggestionsContainer = document.getElementById('command-suggestions');
        if (!suggestionsContainer) return;
        
        const suggestionsHTML = suggestions.map(item => `
            <div class="command-suggestion" data-command="${item.command}">
                <div class="command-name">${item.command}</div>
                <div class="command-description">${item.description}</div>
            </div>
        `).join('');
        
        suggestionsContainer.innerHTML = suggestionsHTML;
        
        // Add click handlers
        suggestionsContainer.querySelectorAll('.command-suggestion').forEach(item => {
            item.addEventListener('click', () => {
                document.getElementById('quick-execute-input').value = item.dataset.command;
                this.executeCommand(item.dataset.command);
            });
        });
    }

    async executeCommand(command) {
        if (!command.trim()) return;
        
        const modal = document.getElementById('quick-execute-modal');
        const input = document.getElementById('quick-execute-input');
        const submitBtn = document.getElementById('quick-execute-submit');
        
        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Executing...';
        
        try {
            const response = await fetch('/api/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ command })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(`Command executed: ${command}`, 'success');
                modal.classList.add('hidden');
                input.value = '';
                
                // Handle command-specific actions
                this.handleCommandResult(command, result);
            } else {
                this.showNotification(`Command failed: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('Command execution error:', error);
            this.showNotification('Failed to execute command', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-play"></i> Execute';
        }
    }

    handleCommandResult(command, result) {
        // Handle specific command results
        switch (command.split(' ')[0]) {
            case 'analyze':
                this.displayAnalysisResults(result.data);
                break;
            case 'optimize':
                this.showOptimizationStatus(result.data);
                break;
            case 'backup':
                this.showBackupStatus(result.data);
                break;
            case 'sync':
                this.refreshAllData();
                break;
            case 'report':
                this.downloadReport(result.data);
                break;
            case 'heal':
                this.showHealingResults(result.data);
                break;
            case 'update':
                this.refreshAgentStatuses();
                break;
            case 'restart':
                this.refreshAgentStatuses();
                break;
        }
    }

    // Agent Management
    setupAgentControls() {
        // Agent action buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.agent-start-btn')) {
                this.startAgent(e.target.dataset.agentId);
            } else if (e.target.matches('.agent-stop-btn')) {
                this.stopAgent(e.target.dataset.agentId);
            } else if (e.target.matches('.agent-restart-btn')) {
                this.restartAgent(e.target.dataset.agentId);
            } else if (e.target.matches('.agent-config-btn')) {
                this.openAgentConfig(e.target.dataset.agentId);
            }
        });
    }

    async startAgent(agentId) {
        try {
            const response = await fetch(`/api/agents/${agentId}/start`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification(`Agent ${agentId} started`, 'success');
                this.updateAgentStatus({ id: agentId, status: 'running' });
            } else {
                throw new Error('Failed to start agent');
            }
        } catch (error) {
            console.error('Error starting agent:', error);
            this.showNotification(`Failed to start agent ${agentId}`, 'error');
        }
    }

    async stopAgent(agentId) {
        try {
            const response = await fetch(`/api/agents/${agentId}/stop`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification(`Agent ${agentId} stopped`, 'success');
                this.updateAgentStatus({ id: agentId, status: 'stopped' });
            } else {
                throw new Error('Failed to stop agent');
            }
        } catch (error) {
            console.error('Error stopping agent:', error);
            this.showNotification(`Failed to stop agent ${agentId}`, 'error');
        }
    }

    async restartAgent(agentId) {
        await this.stopAgent(agentId);
        setTimeout(() => {
            this.startAgent(agentId);
        }, 1000);
    }

    openAgentConfig(agentId) {
        // Open configuration modal
        const configModal = document.getElementById('agent-config-modal');
        if (configModal) {
            this.loadAgentConfig(agentId);
            configModal.classList.remove('hidden');
        }
    }

    updateAgentStatus(data) {
        const agentCard = document.querySelector(`[data-agent-id="${data.id}"]`);
        if (!agentCard) return;
        
        // Update status indicator
        const statusIndicator = agentCard.querySelector('.agent-status');
        statusIndicator.className = `agent-status ${data.status}`;
        statusIndicator.textContent = data.status;
        
        // Update metrics if provided
        if (data.metrics) {
            const metricsContainer = agentCard.querySelector('.agent-metrics');
            if (metricsContainer) {
                metricsContainer.innerHTML = this.renderAgentMetrics(data.metrics);
            }
        }
        
        // Update last active time
        if (data.lastActive) {
            const lastActiveElement = agentCard.querySelector('.agent-last-active');
            if (lastActiveElement) {
                lastActiveElement.textContent = `Last active: ${this.formatTime(data.lastActive)}`;
            }
        }
        
        // Store in agents map
        this.agents.set(data.id, data);
    }

    renderAgentMetrics(metrics) {
        return `
            <div class="metric">
                <span class="metric-label">CPU:</span>
                <span class="metric-value">${metrics.cpu || '0'}%</span>
            </div>
            <div class="metric">
                <span class="metric-label">Memory:</span>
                <span class="metric-value">${metrics.memory || '0'}MB</span>
            </div>
            <div class="metric">
                <span class="metric-label">Tasks:</span>
                <span class="metric-value">${metrics.tasks || '0'}</span>
            </div>
        `;
    }

    // Real-time Updates
    startRealtimeUpdates() {
        // Update system metrics every 5 seconds
        this.updateSystemMetrics();
        setInterval(() => {
            this.updateSystemMetrics();
        }, 5000);
        
        // Update agent statuses every 10 seconds
        this.refreshAgentStatuses();
        setInterval(() => {
            this.refreshAgentStatuses();
        }, 10000);
        
        // Update activity feed every 30 seconds
        setInterval(() => {
            if (this.activeTab === 'activity') {
                this.loadActivityData();
            }
        }, 30000);
    }

    async updateSystemMetrics(data = null) {
        if (!data) {
            try {
                const response = await fetch('/api/system/metrics');
                data = await response.json();
            } catch (error) {
                console.error('Error fetching system metrics:', error);
                return;
            }
        }
        
        this.systemMetrics = data;
        
        // Update UI elements
        const elements = {
            'system-cpu': data.cpu,
            'system-memory': data.memory,
            'system-disk': data.disk,
            'system-uptime': this.formatUptime(data.uptime),
            'active-agents': data.activeAgents,
            'total-tasks': data.totalTasks,
            'knowledge-items': data.knowledgeItems
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
        
        // Update charts if available
        if (window.dashboardCharts) {
            window.dashboardCharts.updateMetrics(data);
        }
    }

    async refreshAgentStatuses() {
        try {
            const response = await fetch('/api/agents/status');
            const agents = await response.json();
            
            agents.forEach(agent => {
                this.updateAgentStatus(agent);
            });
        } catch (error) {
            console.error('Error refreshing agent statuses:', error);
        }
    }

    // Activity Feed
    addActivityItem(item) {
        this.activityFeed.unshift(item);
        
        // Keep only last 100 items
        if (this.activityFeed.length > 100) {
            this.activityFeed.pop();
        }
        
        // Update UI if on activity tab
        if (this.activeTab === 'activity') {
            this.renderActivityItem(item, true);
        }
        
        // Update activity counter
        const counter = document.getElementById('activity-counter');
        if (counter) {
            counter.textContent = this.activityFeed.length;
        }
    }

    renderActivityItem(item, prepend = false) {
        const activityContainer = document.getElementById('activity-feed');
        if (!activityContainer) return;
        
        const itemHTML = `
            <div class="activity-item ${item.type}" data-id="${item.id}">
                <div class="activity-icon">
                    <i class="fas fa-${this.getActivityIcon(item.type)}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${item.title}</div>
                    <div class="activity-description">${item.description}</div>
                    <div class="activity-meta">
                        <span class="activity-time">${this.formatTime(item.timestamp)}</span>
                        <span class="activity-source">${item.source}</span>
                    </div>
                </div>
            </div>
        `;
        
        if (prepend) {
            activityContainer.insertAdjacentHTML('afterbegin', itemHTML);
            
            // Animate new item
            const newItem = activityContainer.firstElementChild;
            newItem.style.opacity = '0';
            newItem.style.transform = 'translateY(-20px)';
            
            requestAnimationFrame(() => {
                newItem.style.transition = 'all 0.3s ease';
                newItem.style.opacity = '1';
                newItem.style.transform = 'translateY(0)';
            });
        } else {
            activityContainer.insertAdjacentHTML('beforeend', itemHTML);
        }
    }

    getActivityIcon(type) {
        const icons = {
            'agent_start': 'play-circle',
            'agent_stop': 'stop-circle',
            'task_created': 'plus-circle',
            'task_completed': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle',
            'sync': 'sync',
            'backup': 'save',
            'system': 'cogs'
        };
        return icons[type] || 'circle';
    }

    // Mobile Interactions
    setupMobileInteractions() {
        // Touch gestures for tab switching
        let touchStartX = 0;
        let touchEndX = 0;
        
        const tabContainer = document.querySelector('.tab-container');
        if (tabContainer) {
            tabContainer.addEventListener('touchstart', (e) => {
                touchStartX = e.changedTouches[0].screenX;
            });
            
            tabContainer.addEventListener('touchend', (e) => {
                touchEndX = e.changedTouches[0].screenX;
                this.handleSwipe();
            });
        }
        
        // Mobile menu toggle
        const mobileMenuBtn = document.getElementById('mobile-menu-toggle');
        const sidebar = document.querySelector('.dashboard-sidebar');
        
        if (mobileMenuBtn && sidebar) {
            mobileMenuBtn.addEventListener('click', () => {
                sidebar.classList.toggle('mobile-open');
            });
            
            // Close sidebar when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.dashboard-sidebar') && 
                    !e.target.closest('#mobile-menu-toggle')) {
                    sidebar.classList.remove('mobile-open');
                }
            });
        }
        
        // Responsive charts
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    handleSwipe() {
        const swipeDistance = touchEndX - touchStartX;
        const minSwipeDistance = 50;
        
        if (Math.abs(swipeDistance) < minSwipeDistance) return;
        
        const tabs = ['overview', 'agents', 'tasks', 'knowledge', 'activity'];
        const currentIndex = tabs.indexOf(this.activeTab);
        
        if (swipeDistance > 0 && currentIndex > 0) {
            // Swipe right - previous tab
            this.switchTab(tabs[currentIndex - 1]);
        } else if (swipeDistance < 0 && currentIndex < tabs.length - 1) {
            // Swipe left - next tab
            this.switchTab(tabs[currentIndex + 1]);
        }
    }

    handleResize() {
        // Debounce resize events
        clearTimeout(this.resizeTimer);
        this.resizeTimer = setTimeout(() => {
            // Redraw charts
            if (window.dashboardCharts) {
                window.dashboardCharts.resize();
            }
            
            // Adjust layout for mobile
            const isMobile = window.innerWidth < 768;
            document.body.classList.toggle('mobile', isMobile);
        }, 250);
    }

    // Event Listeners
    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshAllData();
            });
        }
        
        // Filter controls
        document.querySelectorAll('.filter-control').forEach(control => {
            control.addEventListener('change', (e) => {
                this.applyFilters();
            });
        });
        
        // Sort controls
        document.querySelectorAll('.sort-control').forEach(control => {
            control.addEventListener('click', (e) => {
                this.handleSort(e.target.dataset.sort);
            });
        });
        
        // Export buttons
        document.querySelectorAll('.export-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.exportData(e.target.dataset.format);
            });
        });
    }

    // Data Loading Methods
    async loadOverviewData() {
        try {
            const response = await fetch('/api/dashboard/overview');
            const data = await response.json();
            
            this.renderOverviewData(data);
        } catch (error) {
            console.error('Error loading overview data:', error);
            this.showNotification('Failed to load overview data', 'error');
        }
    }

    async loadAgentsData() {
        try {
            const response = await fetch('/api/agents');
            const agents = await response.json();
            
            this.renderAgentsData(agents);
        } catch (error) {
            console.error('Error loading agents data:', error);
            this.showNotification('Failed to load agents data', 'error');
        }
    }

    async loadTasksData() {
        try {
            const response = await fetch('/api/tasks');
            const tasks = await response.json();
            
            this.renderTasksData(tasks);
        } catch (error) {
            console.error('Error loading tasks data:', error);
            this.showNotification('Failed to load tasks data', 'error');
        }
    }

    async loadKnowledgeData() {
        try {
            const response = await fetch('/api/knowledge');
            const knowledge = await response.json();
            
            this.renderKnowledgeData(knowledge);
        } catch (error) {
            console.error('Error loading knowledge data:', error);
            this.showNotification('Failed to load knowledge data', 'error');
        }
    }

    async loadActivityData() {
        try {
            const response = await fetch('/api/activity');
            const activities = await response.json();
            
            this.activityFeed = activities;
            this.renderActivityData(activities);
        } catch (error) {
            console.error('Error loading activity data:', error);
            this.showNotification('Failed to load activity data', 'error');
        }
    }

    // Utility Methods
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) {
            return 'Just now';
        } else if (diff < 3600000) {
            return `${Math.floor(diff / 60000)} minutes ago`;
        } else if (diff < 86400000) {
            return `${Math.floor(diff / 3600000)} hours ago`;
        } else {
            return date.toLocaleDateString();
        }
    }

    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) {
            return `${days}d ${hours}h`;
        } else if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else {
            return `${minutes}m`;
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="notification-close">&times;</button>
        `;
        
        const container = document.getElementById('notification-container') || document.body;
        container.appendChild(notification);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
        
        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
    }

    getNotificationIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    refreshAllData() {
        this.showNotification('Refreshing all data...', 'info');
        
        // Reload current tab data
        this.loadTabData(this.activeTab);
        
        // Update system metrics
        this.updateSystemMetrics();
        
        // Refresh agent statuses
        this.refreshAgentStatuses();
        
        this.showNotification('Data refreshed', 'success');
    }

    async exportData(format) {
        try {
            const response = await fetch(`/api/export/${this.activeTab}?format=${format}`);
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `${this.activeTab}_export_${new Date().toISOString()}.${format}`;
            
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            this.showNotification('Export completed', 'success');
        } catch (error) {
            console.error('Export error:', error);
            this.showNotification('Failed to export data', 'error');
        }
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.unifiedDashboard = new UnifiedDashboard();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Reduce update frequency when page is hidden
        window.unifiedDashboard.pauseUpdates();
    } else {
        // Resume updates when page is visible
        window.unifiedDashboard.resumeUpdates();
    }
});