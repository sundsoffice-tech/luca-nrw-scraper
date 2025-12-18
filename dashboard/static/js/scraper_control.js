/**
 * Scraper Control JavaScript
 * Handles scraper start/stop/pause/resume/reset functionality
 */

let scraperStatusInterval = null;

/**
 * Initialize scraper control
 */
function initScraperControl() {
    // Start polling status
    updateScraperStatus();
    scraperStatusInterval = setInterval(updateScraperStatus, 3000);
}

/**
 * Update scraper status display
 */
async function updateScraperStatus() {
    try {
        const response = await fetch('/api/scraper/status');
        const status = await response.json();
        
        updateStatusBadge(status);
        updateStatusInfo(status);
        
    } catch (error) {
        console.error('Error fetching scraper status:', error);
    }
}

/**
 * Update status badge
 */
function updateStatusBadge(status) {
    const badge = document.getElementById('scraper-status');
    if (!badge) return;
    
    badge.className = 'ml-auto px-3 py-1 rounded-full text-sm';
    
    switch (status.status) {
        case 'running':
            badge.className += ' bg-green-500';
            badge.textContent = status.paused ? '⏸ Paused' : '🟢 Running';
            break;
        case 'paused':
            badge.className += ' bg-yellow-500';
            badge.textContent = '⏸ Paused';
            break;
        case 'starting':
            badge.className += ' bg-blue-500 animate-pulse';
            badge.textContent = '🔄 Starting...';
            break;
        case 'stopped':
        default:
            badge.className += ' bg-red-500';
            badge.textContent = '🔴 Stopped';
            break;
    }
}

/**
 * Update status info section
 */
function updateStatusInfo(status) {
    const infoDiv = document.getElementById('scraper-status-info');
    if (!infoDiv) return;
    
    if (status.status === 'stopped') {
        infoDiv.innerHTML = '<p class="text-gray-500 text-sm">Scraper ist gestoppt</p>';
        return;
    }
    
    let html = '<div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">';
    
    if (status.pid) {
        html += `
            <div>
                <div class="text-gray-500 text-xs">PID</div>
                <div class="text-white">${status.pid}</div>
            </div>
        `;
    }
    
    if (status.uptime_seconds !== undefined) {
        const minutes = Math.floor(status.uptime_seconds / 60);
        const hours = Math.floor(minutes / 60);
        const displayMinutes = minutes % 60;
        html += `
            <div>
                <div class="text-gray-500 text-xs">Laufzeit</div>
                <div class="text-white">${hours}h ${displayMinutes}m</div>
            </div>
        `;
    }
    
    if (status.cpu_percent !== undefined) {
        html += `
            <div>
                <div class="text-gray-500 text-xs">CPU</div>
                <div class="text-white">${status.cpu_percent.toFixed(1)}%</div>
            </div>
        `;
    }
    
    if (status.memory_mb !== undefined) {
        html += `
            <div>
                <div class="text-gray-500 text-xs">RAM</div>
                <div class="text-white">${status.memory_mb.toFixed(0)} MB</div>
            </div>
        `;
    }
    
    html += '</div>';
    infoDiv.innerHTML = html;
}

/**
 * Get current parameters from form
 */
function getScraperParams() {
    return {
        industry: document.getElementById('param-industry')?.value || 'recruiter',
        qpi: parseInt(document.getElementById('param-qpi')?.value || '15'),
        mode: document.getElementById('param-mode')?.value || 'standard',
        smart: document.getElementById('param-smart')?.checked || false,
        force: document.getElementById('param-force')?.checked || false,
        once: document.getElementById('param-once')?.checked || false,
        dry_run: document.getElementById('param-dry-run')?.checked || false
    };
}

/**
 * Start scraper
 */
async function startScraper() {
    try {
        const params = getScraperParams();
        
        const response = await fetch('/api/scraper/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('✅ Scraper gestartet', 'success');
            updateScraperStatus();
        } else {
            showNotification('❌ Fehler: ' + (result.error || 'Unbekannter Fehler'), 'error');
        }
        
    } catch (error) {
        console.error('Error starting scraper:', error);
        showNotification('❌ Fehler beim Starten', 'error');
    }
}

/**
 * Stop scraper
 */
async function stopScraper() {
    try {
        const response = await fetch('/api/scraper/stop', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('⏹ Scraper gestoppt', 'info');
            updateScraperStatus();
        } else {
            showNotification('❌ Fehler: ' + (result.error || 'Unbekannter Fehler'), 'error');
        }
        
    } catch (error) {
        console.error('Error stopping scraper:', error);
        showNotification('❌ Fehler beim Stoppen', 'error');
    }
}

/**
 * Pause scraper
 */
async function pauseScraper() {
    try {
        const response = await fetch('/api/scraper/pause', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('⏸ Scraper pausiert', 'info');
            updateScraperStatus();
        } else {
            showNotification('❌ Fehler: ' + (result.error || 'Unbekannter Fehler'), 'error');
        }
        
    } catch (error) {
        console.error('Error pausing scraper:', error);
        showNotification('❌ Fehler beim Pausieren', 'error');
    }
}

/**
 * Resume scraper
 */
async function resumeScraper() {
    try {
        const response = await fetch('/api/scraper/resume', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('▶ Scraper fortgesetzt', 'success');
            updateScraperStatus();
        } else {
            showNotification('❌ Fehler: ' + (result.error || 'Unbekannter Fehler'), 'error');
        }
        
    } catch (error) {
        console.error('Error resuming scraper:', error);
        showNotification('❌ Fehler beim Fortsetzen', 'error');
    }
}

/**
 * Reset scraper cache and queries
 */
async function resetScraper() {
    if (!confirm('Cache und Queries wirklich zurücksetzen? Dies kann nicht rückgängig gemacht werden.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/scraper/reset', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('🔄 Cache zurückgesetzt', 'success');
        } else {
            showNotification('❌ Fehler: ' + (result.error || 'Unbekannter Fehler'), 'error');
        }
        
    } catch (error) {
        console.error('Error resetting scraper:', error);
        showNotification('❌ Fehler beim Zurücksetzen', 'error');
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white z-50 transition-opacity duration-300';
    
    switch (type) {
        case 'success':
            notification.className += ' bg-green-600';
            break;
        case 'error':
            notification.className += ' bg-red-600';
            break;
        case 'info':
        default:
            notification.className += ' bg-blue-600';
            break;
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initScraperControl);
} else {
    initScraperControl();
}
