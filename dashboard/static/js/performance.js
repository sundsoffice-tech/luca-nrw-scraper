// Performance Monitor JavaScript
let perfUpdateInterval = null;

async function loadPerformanceMetrics() {
    try {
        const response = await fetch('/api/performance');
        const data = await response.json();
        
        if (data.error) return;
        
        // Update bars and values
        updateMetric('cpu', data.system.cpu_percent);
        updateMetric('ram', data.system.ram_percent);
        updateMetric('scraper', data.scraper.cpu_percent);
        
        // Network (estimate percentage based on typical max ~100MB/s)
        const netPercent = Math.min(100, (data.system.net_recv_mb / 100) * 100);
        document.getElementById('perf-network-value').textContent = 
            `${(data.system.net_recv_mb / 1024).toFixed(1)} MB/s`;
        document.getElementById('perf-network-bar').style.width = `${netPercent}%`;
        
        // Update throttle indicator
        if (data.throttled) {
            document.getElementById('perf-cpu-bar').classList.add('bg-yellow-500');
            document.getElementById('perf-cpu-bar').classList.remove('bg-blue-500');
        } else {
            document.getElementById('perf-cpu-bar').classList.remove('bg-yellow-500');
            document.getElementById('perf-cpu-bar').classList.add('bg-blue-500');
        }
        
    } catch (error) {
        console.error('Error loading performance metrics:', error);
    }
}

function updateMetric(name, percent) {
    const bar = document.getElementById(`perf-${name}-bar`);
    const value = document.getElementById(`perf-${name}-value`);
    
    if (bar) bar.style.width = `${percent}%`;
    if (value) value.textContent = `${percent.toFixed(1)}%`;
    
    // Color coding based on usage
    if (bar) {
        bar.classList.remove('bg-green-500', 'bg-yellow-500', 'bg-red-500');
        if (percent < 50) {
            bar.classList.add('bg-green-500');
        } else if (percent < 80) {
            bar.classList.add('bg-yellow-500');
        } else {
            bar.classList.add('bg-red-500');
        }
    }
}

function setPerformanceMode(mode) {
    // Update UI
    document.querySelectorAll('.perf-mode-btn').forEach(btn => {
        btn.classList.remove('bg-blue-600', 'bg-green-600', 'bg-red-600', 'bg-purple-600');
        btn.classList.add('bg-gray-700');
    });
    
    const activeBtn = document.getElementById(`mode-${mode}`);
    if (activeBtn) {
        activeBtn.classList.remove('bg-gray-700');
        if (mode === 'eco') activeBtn.classList.add('bg-green-600');
        else if (mode === 'balanced') activeBtn.classList.add('bg-blue-600');
        else if (mode === 'power') activeBtn.classList.add('bg-red-600');
        else if (mode === 'custom') activeBtn.classList.add('bg-purple-600');
    }
    
    // Show/hide custom settings
    const customSettings = document.getElementById('custom-settings');
    if (customSettings) {
        customSettings.classList.toggle('hidden', mode !== 'custom');
    }
    
    // Save to server
    savePerformanceSettings({ mode });
}

async function savePerformanceSettings(settings = {}) {
    try {
        // Gather all settings if not provided
        if (Object.keys(settings).length === 0) {
            settings = {
                mode: document.querySelector('.perf-mode-btn.bg-blue-600, .perf-mode-btn.bg-green-600, .perf-mode-btn.bg-red-600, .perf-mode-btn.bg-purple-600')?.id.replace('mode-', '') || 'balanced',
                cpu_limit: parseInt(document.getElementById('limit-cpu')?.value || 80),
                ram_limit: parseInt(document.getElementById('limit-ram')?.value || 85),
                auto_throttle: document.getElementById('opt-auto-throttle')?.checked ?? true,
                auto_pause: document.getElementById('opt-auto-pause')?.checked ?? true,
                night_mode: document.getElementById('opt-night-mode')?.checked ?? false,
                custom: {
                    threads: parseInt(document.getElementById('custom-threads')?.value || 4),
                    async_limit: parseInt(document.getElementById('custom-async')?.value || 35),
                    batch_size: parseInt(document.getElementById('custom-batch')?.value || 20),
                    request_delay: parseFloat(document.getElementById('custom-delay')?.value || 2.5)
                }
            };
        }
        
        const response = await fetch('/api/performance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        const data = await response.json();
        if (data.success) {
            showNotification('Performance settings saved!', 'success');
        }
    } catch (error) {
        console.error('Error saving performance settings:', error);
        showNotification('Error saving settings', 'error');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Mode buttons
    document.querySelectorAll('.perf-mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.id.replace('mode-', '');
            setPerformanceMode(mode);
        });
    });
    
    // Save button
    document.getElementById('save-perf-settings')?.addEventListener('click', () => {
        savePerformanceSettings();
    });
    
    // Start update interval
    loadPerformanceMetrics();
    perfUpdateInterval = setInterval(loadPerformanceMetrics, 2000);
});
