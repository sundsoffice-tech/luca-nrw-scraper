/**
 * Scraper Control JavaScript
 * Handles scraper start/stop, status updates, and live log streaming
 */

class ScraperControl {
    constructor(config) {
        this.config = config;
        this.statusInterval = null;
        this.eventSource = null;
        this.isRunning = false;
        
        // Get DOM elements
        this.statusDot = document.getElementById('status-dot');
        this.statusText = document.getElementById('status-text');
        this.statPid = document.getElementById('stat-pid');
        this.statUptime = document.getElementById('stat-uptime');
        this.statLeads = document.getElementById('stat-leads');
        this.statResources = document.getElementById('stat-resources');
        this.logContainer = document.getElementById('log-container');
        this.btnStart = document.getElementById('btn-start');
        this.btnStop = document.getElementById('btn-stop');
        this.btnClearLogs = document.getElementById('btn-clear-logs');
        this.form = document.getElementById('scraper-form');
        
        // Bind events
        this.bindEvents();
        
        // Initial status check
        this.updateStatus();
        
        // Poll status every 3 seconds
        this.statusInterval = setInterval(() => this.updateStatus(), 3000);
    }
    
    bindEvents() {
        this.btnStart.addEventListener('click', () => this.start());
        this.btnStop.addEventListener('click', () => this.stop());
        this.btnClearLogs.addEventListener('click', () => this.clearLogs());
    }
    
    async updateStatus() {
        try {
            const response = await fetch(this.config.statusEndpoint, {
                headers: {
                    'X-CSRFToken': this.config.csrfToken
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch status');
            }
            
            const data = await response.json();
            this.updateUI(data);
            
        } catch (error) {
            console.error('Error updating status:', error);
        }
    }
    
    updateUI(status) {
        // Update status indicator
        this.isRunning = status.status === 'running';
        
        if (this.isRunning) {
            this.statusDot.className = 'w-3 h-3 rounded-full bg-green-500 animate-pulse';
            this.statusText.textContent = 'Läuft';
            this.btnStart.disabled = true;
            this.btnStop.disabled = false;
        } else if (status.status === 'error') {
            this.statusDot.className = 'w-3 h-3 rounded-full bg-red-500';
            this.statusText.textContent = 'Fehler';
            this.btnStart.disabled = false;
            this.btnStop.disabled = true;
        } else {
            this.statusDot.className = 'w-3 h-3 rounded-full bg-gray-500';
            this.statusText.textContent = 'Gestoppt';
            this.btnStart.disabled = false;
            this.btnStop.disabled = true;
        }
        
        // Update stats
        this.statPid.textContent = status.pid || '-';
        
        if (status.uptime_seconds) {
            const minutes = Math.floor(status.uptime_seconds / 60);
            const seconds = status.uptime_seconds % 60;
            this.statUptime.textContent = `${minutes}m ${seconds}s`;
        } else {
            this.statUptime.textContent = '-';
        }
        
        this.statLeads.textContent = status.leads_saved || 0;
        
        if (status.cpu_percent !== undefined && status.memory_mb !== undefined) {
            this.statResources.textContent = `${status.cpu_percent.toFixed(1)}% / ${status.memory_mb.toFixed(0)}MB`;
        } else {
            this.statResources.textContent = '-';
        }
        
        // Start/stop log streaming based on status
        if (this.isRunning && !this.eventSource) {
            this.startLogStream();
        } else if (!this.isRunning && this.eventSource) {
            this.stopLogStream();
        }
    }
    
    getFormData() {
        const formData = new FormData(this.form);
        const data = {
            industry: formData.get('industry'),
            qpi: parseInt(formData.get('qpi')),
            mode: formData.get('mode'),
            smart: formData.get('smart') === 'on',
            once: formData.get('once') === 'on',
            force: formData.get('force') === 'on',
            dry_run: formData.get('dry_run') === 'on'
        };
        return data;
    }
    
    async start() {
        try {
            this.btnStart.disabled = true;
            this.btnStart.textContent = '⏳ Starte...';
            
            const data = this.getFormData();
            
            const response = await fetch(this.config.startEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.config.csrfToken
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.appendLog('INFO', 'Scraper erfolgreich gestartet');
                await this.updateStatus();
            } else {
                this.appendLog('ERROR', `Fehler beim Starten: ${result.error}`);
                alert(`Fehler: ${result.error}`);
                this.btnStart.disabled = false;
            }
            
            this.btnStart.textContent = '▶️ Scraper starten';
            
        } catch (error) {
            console.error('Error starting scraper:', error);
            this.appendLog('ERROR', `Fehler: ${error.message}`);
            alert(`Fehler beim Starten: ${error.message}`);
            this.btnStart.disabled = false;
            this.btnStart.textContent = '▶️ Scraper starten';
        }
    }
    
    async stop() {
        try {
            this.btnStop.disabled = true;
            this.btnStop.textContent = '⏳ Stoppe...';
            
            const response = await fetch(this.config.stopEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.config.csrfToken
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.appendLog('INFO', 'Scraper gestoppt');
                await this.updateStatus();
            } else {
                this.appendLog('ERROR', `Fehler beim Stoppen: ${result.error}`);
                alert(`Fehler: ${result.error}`);
            }
            
            this.btnStop.textContent = '⏹️ Scraper stoppen';
            
        } catch (error) {
            console.error('Error stopping scraper:', error);
            this.appendLog('ERROR', `Fehler: ${error.message}`);
            alert(`Fehler beim Stoppen: ${error.message}`);
            this.btnStop.disabled = false;
            this.btnStop.textContent = '⏹️ Scraper stoppen';
        }
    }
    
    startLogStream() {
        if (this.eventSource) {
            return;
        }
        
        this.eventSource = new EventSource(this.config.logsEndpoint);
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'log') {
                    this.appendLog('LOG', data.message, data.timestamp);
                } else if (data.type === 'connected') {
                    this.appendLog('INFO', data.message);
                } else if (data.type === 'stopped') {
                    this.appendLog('INFO', data.message);
                    this.stopLogStream();
                } else if (data.type === 'error') {
                    this.appendLog('ERROR', data.message);
                }
            } catch (error) {
                console.error('Error parsing log event:', error);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
            this.stopLogStream();
        };
    }
    
    stopLogStream() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
    
    appendLog(level, message, timestamp = null) {
        // Remove placeholder if present
        if (this.logContainer.querySelector('.text-gray-500')) {
            this.logContainer.innerHTML = '';
        }
        
        const logEntry = document.createElement('div');
        logEntry.className = 'py-1';
        
        // Color code by level
        let color = 'text-gray-300';
        if (level === 'ERROR' || level === 'FATAL') {
            color = 'text-red-400';
        } else if (level === 'WARN') {
            color = 'text-yellow-400';
        } else if (level === 'INFO') {
            color = 'text-primary';
        }
        
        const ts = timestamp || new Date().toLocaleTimeString();
        logEntry.innerHTML = `<span class="text-gray-500">[${ts}]</span> <span class="${color}">${message}</span>`;
        
        this.logContainer.appendChild(logEntry);
        
        // Auto-scroll to bottom
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
        
        // Keep only last 500 log entries
        while (this.logContainer.children.length > 500) {
            this.logContainer.removeChild(this.logContainer.firstChild);
        }
    }
    
    clearLogs() {
        this.logContainer.innerHTML = '<div class="text-gray-500">Logs gelöscht</div>';
    }
    
    destroy() {
        // Clean up
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }
        this.stopLogStream();
    }
}

// Export for global use
window.ScraperControl = ScraperControl;