/**
 * TELIS CRM Dashboard JavaScript
 * Handles Chart.js initialization, auto-refresh, and interactivity
 */

// Chart instances
let leadTrendChart = null;
let statusDistChart = null;
let sourceDistChart = null;
let qualityTrendChart = null;

// Dark theme colors
const COLORS = {
    primary: '#06b6d4',
    green: '#10b981',
    blue: '#3b82f6',
    yellow: '#f59e0b',
    purple: '#a855f7',
    emerald: '#059669',
    red: '#ef4444',
    gray: '#6b7280',
    cyan: '#06b6d4',
    teal: '#14b8a6',
    indigo: '#6366f1',
    pink: '#ec4899',
};

const STATUS_COLORS = {
    'NEW': COLORS.green,
    'CONTACTED': COLORS.blue,
    'VOICEMAIL': COLORS.yellow,
    'INTERESTED': COLORS.yellow,
    'INTERVIEW': COLORS.purple,
    'HIRED': COLORS.emerald,
    'NOT_INTERESTED': COLORS.red,
    'INVALID': COLORS.gray,
};

/**
 * Initialize dashboard on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Load initial data
    loadDashboardStats();
    loadActivityFeed();
    loadTeamPerformance();
    
    // Auto-refresh every 30 seconds
    setInterval(loadDashboardStats, 30000);
    setInterval(loadActivityFeed, 30000);
    
    // Auto-refresh team performance every 60 seconds
    setInterval(loadTeamPerformance, 60000);
});

/**
 * Load dashboard statistics and update KPI cards
 */
async function loadDashboardStats() {
    try {
        const response = await fetch('/crm/api/dashboard-stats/');
        if (!response.ok) throw new Error('Failed to fetch stats');
        
        const data = await response.json();
        
        // Update KPI cards
        updateKPICard('total-leads', data.leads_total, `+${data.leads_today} heute`);
        updateKPICard('calls-today', data.calls_today, `Ø ${data.avg_calls_per_day}/Tag`);
        updateKPICard('conversion-rate', `${data.conversion_rate}%`, 
            `${data.conversion_change >= 0 ? '↑' : '↓'} ${Math.abs(data.conversion_change)}%`);
        updateKPICard('hot-leads', data.hot_leads, 'Score ≥ 80');
        
        // Update charts
        updateLeadTrendChart(data.trend_7_days);
        updateStatusDistChart(data.status_distribution);
        updateSourceDistChart(data.source_distribution);
        updateQualityTrendChart(data.quality_trend);
        
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

/**
 * Update a KPI card with new values
 */
function updateKPICard(id, mainValue, subValue) {
    const mainElement = document.getElementById(`${id}-value`);
    const subElement = document.getElementById(`${id}-sub`);
    
    if (mainElement) {
        mainElement.textContent = mainValue;
    }
    if (subElement) {
        subElement.innerHTML = subValue;
    }
}

/**
 * Initialize and update Lead Trend Chart (Line Chart)
 */
function updateLeadTrendChart(trendData) {
    const ctx = document.getElementById('leadTrendChart');
    if (!ctx) return;
    
    const labels = trendData.map(d => d.label);
    const newLeadsData = trendData.map(d => d.new_leads);
    const conversionsData = trendData.map(d => d.conversions);
    
    if (leadTrendChart) {
        // Update existing chart
        leadTrendChart.data.labels = labels;
        leadTrendChart.data.datasets[0].data = newLeadsData;
        leadTrendChart.data.datasets[1].data = conversionsData;
        leadTrendChart.update('none'); // No animation on update
    } else {
        // Create new chart
        leadTrendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Neue Leads',
                    data: newLeadsData,
                    borderColor: COLORS.cyan,
                    backgroundColor: COLORS.cyan + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                }, {
                    label: 'Conversions',
                    data: conversionsData,
                    borderColor: COLORS.emerald,
                    backgroundColor: COLORS.emerald + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { color: '#9ca3af', font: { size: 12 } }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: '#1e293b',
                        titleColor: '#f3f4f6',
                        bodyColor: '#d1d5db',
                        borderColor: '#334155',
                        borderWidth: 1,
                    }
                },
                scales: {
                    x: {
                        grid: { color: '#334155', drawBorder: false },
                        ticks: { color: '#9ca3af' }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: '#334155', drawBorder: false },
                        ticks: { color: '#9ca3af', precision: 0 }
                    }
                }
            }
        });
    }
}

/**
 * Initialize and update Status Distribution Chart (Donut Chart)
 */
function updateStatusDistChart(statusDist) {
    const ctx = document.getElementById('statusDistChart');
    if (!ctx) return;
    
    const statusKeys = Object.keys(statusDist);
    const labels = statusKeys.map(key => statusDist[key].label);
    const data = statusKeys.map(key => statusDist[key].count);
    const colors = statusKeys.map(key => STATUS_COLORS[key] || COLORS.gray);
    
    if (statusDistChart) {
        // Update existing chart
        statusDistChart.data.labels = labels;
        statusDistChart.data.datasets[0].data = data;
        statusDistChart.data.datasets[0].backgroundColor = colors;
        statusDistChart.update('none');
    } else {
        // Create new chart
        statusDistChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderColor: '#1e293b',
                    borderWidth: 2,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'right',
                        labels: { 
                            color: '#9ca3af', 
                            font: { size: 11 },
                            padding: 10,
                            boxWidth: 12,
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f3f4f6',
                        bodyColor: '#d1d5db',
                        borderColor: '#334155',
                        borderWidth: 1,
                    }
                }
            }
        });
    }
}

/**
 * Initialize and update Source Distribution Chart (Horizontal Bar Chart)
 */
function updateSourceDistChart(sourceDist) {
    const ctx = document.getElementById('sourceDistChart');
    if (!ctx) return;
    
    const sourceKeys = Object.keys(sourceDist);
    const labels = sourceKeys.map(key => sourceDist[key].label);
    const data = sourceKeys.map(key => sourceDist[key].count);
    const percentages = sourceKeys.map(key => sourceDist[key].percentage);
    
    if (sourceDistChart) {
        // Update existing chart
        sourceDistChart.data.labels = labels;
        sourceDistChart.data.datasets[0].data = data;
        sourceDistChart.update('none');
    } else {
        // Create new chart
        sourceDistChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Anzahl Leads',
                    data: data,
                    backgroundColor: COLORS.teal + '80',
                    borderColor: COLORS.teal,
                    borderWidth: 1,
                }]
            },
            options: {
                indexAxis: 'y', // Horizontal bars
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f3f4f6',
                        bodyColor: '#d1d5db',
                        borderColor: '#334155',
                        borderWidth: 1,
                        callbacks: {
                            afterLabel: function(context) {
                                const idx = context.dataIndex;
                                return `${percentages[idx]}% aller Leads`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: { color: '#334155', drawBorder: false },
                        ticks: { color: '#9ca3af', precision: 0 }
                    },
                    y: {
                        grid: { display: false, drawBorder: false },
                        ticks: { color: '#9ca3af', font: { size: 11 } }
                    }
                }
            }
        });
    }
}

/**
 * Initialize and update Quality Trend Chart (Line Chart)
 */
function updateQualityTrendChart(qualityData) {
    const ctx = document.getElementById('qualityTrendChart');
    if (!ctx) return;
    
    const labels = qualityData.map(d => d.label);
    const qualityScores = qualityData.map(d => d.avg_quality);
    
    if (qualityTrendChart) {
        // Update existing chart
        qualityTrendChart.data.labels = labels;
        qualityTrendChart.data.datasets[0].data = qualityScores;
        qualityTrendChart.update('none');
    } else {
        // Create new chart
        qualityTrendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Ø Qualitäts-Score',
                    data: qualityScores,
                    borderColor: COLORS.purple,
                    backgroundColor: COLORS.purple + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { color: '#9ca3af', font: { size: 12 } }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: '#1e293b',
                        titleColor: '#f3f4f6',
                        bodyColor: '#d1d5db',
                        borderColor: '#334155',
                        borderWidth: 1,
                    }
                },
                scales: {
                    x: {
                        grid: { color: '#334155', drawBorder: false },
                        ticks: { color: '#9ca3af' }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: '#334155', drawBorder: false },
                        ticks: { color: '#9ca3af', precision: 0 }
                    }
                }
            }
        });
    }
}

/**
 * Load and display activity feed
 */
async function loadActivityFeed() {
    try {
        const response = await fetch('/crm/api/activity-feed/');
        if (!response.ok) throw new Error('Failed to fetch activity feed');
        
        const activities = await response.json();
        const feedContainer = document.getElementById('activity-feed');
        
        if (!feedContainer) return;
        
        // Generate HTML for activities
        let html = '';
        activities.forEach(activity => {
            html += `
                <div class="p-3 bg-dark-900 rounded-lg hover:bg-dark-700 transition duration-150 cursor-pointer" 
                     onclick="viewLead(${activity.lead_id})">
                    <div class="flex items-start">
                        <span class="text-xl mr-3">${activity.icon}</span>
                        <div class="flex-1 min-w-0">
                            <p class="text-sm text-gray-300">${activity.message}</p>
                            <p class="text-xs text-gray-500 mt-1">${activity.detail}</p>
                            <p class="text-xs text-gray-600 mt-1">${activity.time_ago}</p>
                        </div>
                    </div>
                </div>
            `;
        });
        
        if (html === '') {
            html = '<div class="p-3 bg-dark-900 rounded-lg text-center text-gray-500 text-sm">Keine Aktivitäten</div>';
        }
        
        feedContainer.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading activity feed:', error);
    }
}

/**
 * Load and display team performance (Manager/Admin only)
 */
async function loadTeamPerformance() {
    const perfContainer = document.getElementById('team-performance');
    if (!perfContainer) return; // Not visible for this user
    
    try {
        const response = await fetch('/crm/api/team-performance/');
        if (!response.ok) {
            if (response.status === 403) return; // Not authorized, skip silently
            throw new Error('Failed to fetch team performance');
        }
        
        const performers = await response.json();
        
        // Generate HTML for team performance table
        let html = `
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b border-dark-700">
                            <th class="text-left py-2 px-3 text-gray-400 font-medium">Name</th>
                            <th class="text-center py-2 px-3 text-gray-400 font-medium">Anrufe heute</th>
                            <th class="text-center py-2 px-3 text-gray-400 font-medium">Conversions (7d)</th>
                            <th class="text-center py-2 px-3 text-gray-400 font-medium">Ø Dauer</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        performers.forEach((perf, idx) => {
            const isTop = idx === 0 && perf.calls_today > 0;
            html += `
                <tr class="border-b border-dark-700/50 hover:bg-dark-700/30 transition">
                    <td class="py-2 px-3 text-gray-300">
                        ${isTop ? '🏆 ' : ''}${perf.full_name}
                    </td>
                    <td class="text-center py-2 px-3">
                        <span class="inline-block px-2 py-1 rounded ${perf.calls_today > 0 ? 'bg-cyan-500/20 text-cyan-400' : 'text-gray-500'}">
                            ${perf.calls_today}
                        </span>
                    </td>
                    <td class="text-center py-2 px-3">
                        <span class="inline-block px-2 py-1 rounded ${perf.conversions_week > 0 ? 'bg-green-500/20 text-green-400' : 'text-gray-500'}">
                            ${perf.conversions_week}
                        </span>
                    </td>
                    <td class="text-center py-2 px-3 text-gray-400">
                        ${perf.avg_duration_formatted}
                    </td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        if (performers.length === 0) {
            html = '<div class="p-4 text-center text-gray-500 text-sm">Keine Daten verfügbar</div>';
        }
        
        perfContainer.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading team performance:', error);
    }
}

/**
 * Navigate to lead detail view
 */
function viewLead(leadId) {
    if (leadId) {
        window.location.href = `/crm/leads/${leadId}/`;
    }
}

/**
 * Skeleton loading for charts
 */
function showChartSkeleton(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#1e293b';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
}
