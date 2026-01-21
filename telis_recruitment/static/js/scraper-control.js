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
        this.metricCpu = document.getElementById('metric-cpu');
        this.metricMemory = document.getElementById('metric-memory');
        this.metricLeads = document.getElementById('metric-leads');
        this.metricUpdated = document.getElementById('metric-updated');
        this.metricsSource = null;
        
        // Bind events
        this.bindEvents();
        
        // Initial status check
        this.updateStatus();
        
        // Poll status every 3 seconds
        this.statusInterval = setInterval(() => this.updateStatus(), 3000);
        this.startMetricsStream();
    }
    
    bindEvents() {
        this.btnStart.addEventListener('click', () => this.start());
        this.btnStop.addEventListener('click', () => this.stop());
        this.btnClearLogs.addEventListener('click', () => this.clearLogs());
        
        // Log level filter
        const logLevelFilter = document.getElementById('log-level-filter');
        if (logLevelFilter) {
            logLevelFilter.addEventListener('change', (e) => {
                this.filterLogs(e.target.value);
            });
        }
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
            
            // Show error type if available
            if (status.error_type) {
                const errorTypeMap = {
                    'SCRIPT_NOT_FOUND': 'Fehler: Skript nicht gefunden',
                    'SCRIPT_PERMISSION_DENIED': 'Fehler: Skript-Berechtigung verweigert',
                    'PERMISSION_DENIED': 'Fehler: Zugriff verweigert',
                    'CONFIG_ERROR': 'Fehler: Konfiguration',
                    'CONFIG_FILE_MISSING': 'Fehler: Konfiguration fehlt',
                    'CONFIG_INVALID': 'Fehler: Ungültige Konfiguration',
                    'PROCESS_START_FAILED': 'Fehler: Prozessstart fehlgeschlagen',
                    'PROCESS_CRASH': 'Fehler: Prozess abgestürzt',
                    'PROCESS_EARLY_EXIT': 'Fehler: Frühzeitiger Exit',
                    'MISSING_DEPENDENCY': 'Fehler: Fehlende Abhängigkeit',
                    'PYTHON_VERSION_ERROR': 'Fehler: Python-Version',
                    'RATE_LIMIT_ERROR': 'Fehler: Rate Limit',
                    'CONNECTION_ERROR': 'Fehler: Verbindung',
                    'TIMEOUT_ERROR': 'Fehler: Timeout',
                    'FILE_ACCESS_ERROR': 'Fehler: Dateizugriff',
                    'ALREADY_RUNNING': 'Läuft bereits',
                    'NOT_RUNNING': 'Läuft nicht',
                    'UNKNOWN_ERROR': 'Unbekannter Fehler'
                };
                this.statusText.textContent = errorTypeMap[status.error_type] || 'Fehler';
                this.statusText.title = status.error_message || '';
            } else {
                this.statusText.textContent = 'Fehler';
            }
            
            this.btnStart.disabled = false;
            this.btnStop.disabled = true;
        } else if (status.status === 'circuit_breaker_open') {
            this.statusDot.className = 'w-3 h-3 rounded-full bg-yellow-500';
            this.statusText.textContent = 'Circuit Breaker aktiv';
            if (status.remaining_penalty_seconds) {
                this.statusText.title = `Versuchen Sie es in ${Math.ceil(status.remaining_penalty_seconds)}s erneut`;
            }
            this.btnStart.disabled = true;
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
        
        // Use leads_found from API (not leads_saved)
        this.statLeads.textContent = status.leads_found || 0;
        
        if (status.cpu_percent !== undefined && status.memory_mb !== undefined) {
            this.statResources.textContent = `${status.cpu_percent.toFixed(1)}% / ${status.memory_mb.toFixed(0)}MB`;
        } else {
            this.statResources.textContent = '-';
        }
        
        // Update performance metrics if elements exist
        const metricLinksChecked = document.getElementById('metric-links-checked');
        const metricAcceptanceRate = document.getElementById('metric-acceptance-rate');
        const metricBlockRate = document.getElementById('metric-block-rate');
        const metricAvgTime = document.getElementById('metric-avg-time');
        
        if (metricLinksChecked) {
            metricLinksChecked.textContent = status.links_checked || 0;
        }
        if (metricAcceptanceRate) {
            metricAcceptanceRate.textContent = (status.lead_acceptance_rate || 0).toFixed(1) + '%';
        }
        if (metricBlockRate) {
            metricBlockRate.textContent = (status.block_rate || 0).toFixed(1) + '%';
        }
        if (metricAvgTime) {
            metricAvgTime.textContent = Math.round(status.avg_request_time_ms || 0) + 'ms';
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
    
    /**
     * Format error message with context and recovery actions
     */
    formatErrorMessage(result) {
        if (!result.error_type) {
            // Fallback for old-style errors
            return result.error || 'Unbekannter Fehler';
        }
        
        let message = result.error_message || result.error || 'Fehler';
        
        // Add error details if available
        if (result.error_details) {
            message += `\n\nDetails: ${result.error_details}`;
        }
        
        // Add failed component if available
        if (result.failed_component) {
            message += `\nBetroffene Komponente: ${result.failed_component}`;
        }
        
        // Add recovery action if available
        if (result.recovery_action) {
            message += `\n\n💡 Lösungsvorschlag:\n${result.recovery_action}`;
        }
        
        return message;
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
                const errorMsg = this.formatErrorMessage(result);
                
                this.appendLog('ERROR', `Fehler beim Starten: ${result.error_message || result.error}`);
                
                // Show detailed error in alert
                alert(`❌ Fehler beim Starten des Scrapers\n\n${errorMsg}`);
                
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
                const errorMsg = this.formatErrorMessage(result);
                
                this.appendLog('ERROR', `Fehler beim Stoppen: ${result.error_message || result.error}`);
                alert(`❌ Fehler beim Stoppen\n\n${errorMsg}`);
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
    
    startMetricsStream() {
        if (!this.config.metricsEndpoint || this.metricsSource) {
            return;
        }

        this.metricsSource = new EventSource(this.config.metricsEndpoint);
        this.metricsSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'metrics') {
                    this.updateMetrics(data.payload);
                }
            } catch (error) {
                console.error('Error parsing metrics event:', error);
            }
        };

        this.metricsSource.onerror = (error) => {
            console.error('Metrics EventSource error:', error);
            this.stopMetricsStream();
            setTimeout(() => this.startMetricsStream(), 5000);
        };
    }

    stopMetricsStream() {
        if (this.metricsSource) {
            this.metricsSource.close();
            this.metricsSource = null;
        }
    }

    updateMetrics(payload) {
        if (this.metricCpu) {
            this.metricCpu.textContent = payload.cpu_percent.toFixed(1) + '%';
        }
        if (this.metricMemory) {
            this.metricMemory.textContent = payload.memory_mb.toFixed(0) + 'MB';
        }
        if (this.metricLeads) {
            this.metricLeads.textContent = payload.leads_found || 0;
        }
        if (this.metricUpdated) {
            const ts = new Date().toLocaleTimeString();
            this.metricUpdated.textContent = ts;
        }
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
        logEntry.className = 'py-1 log-entry';
        logEntry.dataset.level = level;  // For filter
        
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
        
        // Create timestamp span
        const tsSpan = document.createElement('span');
        tsSpan.className = 'text-gray-500';
        tsSpan.textContent = `[${ts}] `;
        
        // Create message span
        const msgSpan = document.createElement('span');
        msgSpan.className = color;
        msgSpan.textContent = message;
        
        logEntry.appendChild(tsSpan);
        logEntry.appendChild(msgSpan);
        
        this.logContainer.appendChild(logEntry);
        
        // Auto-scroll to bottom
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
        
        // Keep only last 500 log entries
        while (this.logContainer.children.length > 500) {
            this.logContainer.removeChild(this.logContainer.firstChild);
        }
    }
    
    filterLogs(level) {
        const entries = this.logContainer.querySelectorAll('.log-entry');
        entries.forEach(entry => {
            if (!level || entry.dataset.level === level || entry.dataset.level === 'LOG') {
                entry.style.display = '';
            } else {
                entry.style.display = 'none';
            }
        });
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
        this.stopMetricsStream();
    }
}

// Export for global use
window.ScraperControl = ScraperControl;
