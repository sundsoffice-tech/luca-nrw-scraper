/**
 * Leads Manager JavaScript
 * Handles lead listing, filtering, sorting, and exporting
 */

let currentPage = 1;
let currentFilters = {
    search: '',
    status: '',
    date_from: '',
    lead_type: ''
};

/**
 * Initialize leads manager
 */
function initLeadsManager() {
    loadLeads();
    setupEventListeners();
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById('leads-search');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentFilters.search = e.target.value;
                currentPage = 1;
                loadLeads();
            }, 500);
        });
    }
    
    // Lead type filter
    const leadTypeFilter = document.getElementById('filter-lead-type');
    if (leadTypeFilter) {
        leadTypeFilter.addEventListener('change', (e) => {
            currentFilters.lead_type = e.target.value;
            currentPage = 1;
            loadLeads();
        });
    }
    
    // Status filter
    const statusFilter = document.getElementById('filter-status');
    if (statusFilter) {
        statusFilter.addEventListener('change', (e) => {
            currentFilters.status = e.target.value;
            currentPage = 1;
            loadLeads();
        });
    }
    
    // Date filter
    const dateFilter = document.getElementById('filter-date');
    if (dateFilter) {
        dateFilter.addEventListener('change', (e) => {
            currentFilters.date_from = e.target.value;
            currentPage = 1;
            loadLeads();
        });
    }
    
    // Quick filters
    const todayBtn = document.getElementById('filter-today');
    if (todayBtn) {
        todayBtn.addEventListener('click', () => {
            const today = new Date().toISOString().split('T')[0];
            currentFilters.date_from = today;
            document.getElementById('filter-date').value = today;
            currentPage = 1;
            loadLeads();
        });
    }
    
    const weekBtn = document.getElementById('filter-week');
    if (weekBtn) {
        weekBtn.addEventListener('click', () => {
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            const dateStr = weekAgo.toISOString().split('T')[0];
            currentFilters.date_from = dateStr;
            document.getElementById('filter-date').value = dateStr;
            currentPage = 1;
            loadLeads();
        });
    }
    
    const clearBtn = document.getElementById('filter-clear');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            currentFilters = { search: '', status: '', date_from: '', lead_type: '' };
            document.getElementById('leads-search').value = '';
            document.getElementById('filter-status').value = '';
            document.getElementById('filter-date').value = '';
            document.getElementById('filter-lead-type').value = '';
            currentPage = 1;
            loadLeads();
        });
    }
}

/**
 * Load leads from API
 */
async function loadLeads() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            per_page: 50,
            ...currentFilters
        });
        
        const response = await fetch(`/api/leads?${params}`);
        const data = await response.json();
        
        if (data.error) {
            showError('Fehler beim Laden der Leads: ' + data.error);
            return;
        }
        
        renderLeads(data.leads);
        renderPagination(data.page, data.pages, data.total);
        
    } catch (error) {
        console.error('Error loading leads:', error);
        showError('Fehler beim Laden der Leads');
    }
}

/**
 * Render leads table
 */
function renderLeads(leads) {
    const tbody = document.getElementById('leads-tbody');
    if (!tbody) return;
    
    if (leads.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="px-6 py-8 text-center text-gray-500">
                    Keine Leads gefunden
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = leads.map(lead => {
        const isCandidate = lead.lead_type === 'candidate';
        const typeEmoji = isCandidate ? '👤' : '🏢';
        const typeLabel = isCandidate ? 'Kandidat' : 'Firma';
        
        // For candidates, show location instead of company
        const companyOrLocation = isCandidate ? 
            (lead.location || lead.region || 'N/A') : 
            (lead.company || lead.company_name || 'N/A');
        
        // For candidates, show experience; for companies, show role
        const experienceOrRole = isCandidate ?
            (lead.experience_years ? `${lead.experience_years} Jahre` : '-') :
            (lead.role || lead.rolle || '-');
        
        return `
            <tr class="border-b border-gray-700 hover:bg-gray-750">
                <td class="px-4 py-3 text-sm">${lead.id}</td>
                <td class="px-4 py-3 text-sm">
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs ${isCandidate ? 'bg-purple-900 text-purple-200' : 'bg-blue-900 text-blue-200'}">
                        ${typeEmoji} ${typeLabel}
                    </span>
                </td>
                <td class="px-4 py-3 text-sm">
                    <div class="font-medium">${escapeHtml(lead.name || 'N/A')}</div>
                    ${isCandidate && lead.current_status ? `<div class="text-gray-400 text-xs">${escapeHtml(lead.current_status)}</div>` : ''}
                </td>
                <td class="px-4 py-3 text-sm">${escapeHtml(companyOrLocation)}</td>
                <td class="px-4 py-3 text-sm">
                    ${lead.mobile_number || lead.telefon ? `<a href="tel:${lead.mobile_number || lead.telefon}" class="text-blue-400 hover:text-blue-300">${escapeHtml(lead.mobile_number || lead.telefon)}</a>` : '-'}
                </td>
                <td class="px-4 py-3 text-sm">
                    ${lead.email ? `<a href="mailto:${lead.email}" class="text-blue-400 hover:text-blue-300">${escapeHtml(lead.email)}</a>` : '-'}
                </td>
                <td class="px-4 py-3 text-sm">
                    <div class="font-medium">${escapeHtml(experienceOrRole)}</div>
                    ${isCandidate && lead.skills ? `<div class="text-gray-400 text-xs truncate max-w-xs">${escapeHtml(lead.skills)}</div>` : ''}
                </td>
                <td class="px-4 py-3 text-sm">
                    <a href="${lead.source_url || lead.quelle}" target="_blank" class="text-blue-400 hover:text-blue-300 truncate block max-w-xs" title="${escapeHtml(lead.source_url || lead.quelle)}">
                        ${escapeHtml(getDomain(lead.source_url || lead.quelle))}
                    </a>
                </td>
                <td class="px-4 py-3 text-sm text-gray-400">
                    ${formatDate(lead.created_at || lead.last_updated)}
                </td>
                <td class="px-4 py-3 text-sm">
                    <select 
                        class="bg-gray-700 rounded px-2 py-1 text-xs border border-gray-600"
                        onchange="updateLeadStatus(${lead.id}, this.value)"
                    >
                        <option value="new" ${lead.status === 'new' ? 'selected' : ''}>Neu</option>
                        <option value="contacted" ${lead.status === 'contacted' ? 'selected' : ''}>Kontaktiert</option>
                        <option value="interested" ${lead.status === 'interested' ? 'selected' : ''}>Interessiert</option>
                        <option value="rejected" ${lead.status === 'rejected' ? 'selected' : ''}>Abgelehnt</option>
                        <option value="completed" ${lead.status === 'completed' ? 'selected' : ''}>Abgeschlossen</option>
                    </select>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Render pagination
 */
function renderPagination(page, totalPages, totalLeads) {
    const paginationDiv = document.getElementById('pagination');
    if (!paginationDiv) return;
    
    const infoDiv = document.getElementById('leads-info');
    if (infoDiv) {
        infoDiv.textContent = `Zeige Seite ${page} von ${totalPages} (${totalLeads} Leads gesamt)`;
    }
    
    if (totalPages <= 1) {
        paginationDiv.innerHTML = '';
        return;
    }
    
    let html = '<div class="flex gap-2 items-center">';
    
    // Previous button
    if (page > 1) {
        html += `<button onclick="changePage(${page - 1})" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded">◀ Zurück</button>`;
    }
    
    // Page numbers
    const maxButtons = 5;
    let startPage = Math.max(1, page - Math.floor(maxButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);
    
    if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }
    
    if (startPage > 1) {
        html += `<button onclick="changePage(1)" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded">1</button>`;
        if (startPage > 2) {
            html += `<span class="px-2">...</span>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        if (i === page) {
            html += `<button class="px-3 py-1 bg-blue-600 rounded">${i}</button>`;
        } else {
            html += `<button onclick="changePage(${i})" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded">${i}</button>`;
        }
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `<span class="px-2">...</span>`;
        }
        html += `<button onclick="changePage(${totalPages})" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded">${totalPages}</button>`;
    }
    
    // Next button
    if (page < totalPages) {
        html += `<button onclick="changePage(${page + 1})" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded">Weiter ▶</button>`;
    }
    
    html += '</div>';
    paginationDiv.innerHTML = html;
}

/**
 * Change page
 */
function changePage(page) {
    currentPage = page;
    loadLeads();
    window.scrollTo(0, 0);
}

/**
 * Update lead status
 */
async function updateLeadStatus(leadId, newStatus) {
    try {
        const response = await fetch(`/api/leads/${leadId}/status`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({status: newStatus})
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Status aktualisiert', 'success');
        } else {
            showNotification('Fehler beim Aktualisieren', 'error');
            loadLeads(); // Reload to reset
        }
        
    } catch (error) {
        console.error('Error updating status:', error);
        showNotification('Fehler beim Aktualisieren', 'error');
        loadLeads();
    }
}

/**
 * Export leads
 */
async function exportLeads(format) {
    try {
        const params = new URLSearchParams(currentFilters);
        const url = `/api/leads/export/${format}?${params}`;
        
        // Open in new window to trigger download
        window.open(url, '_blank');
        
        showNotification(`Export als ${format.toUpperCase()} gestartet`, 'success');
        
    } catch (error) {
        console.error('Error exporting leads:', error);
        showNotification('Fehler beim Exportieren', 'error');
    }
}

// Note: Utility functions (escapeHtml, getDomain, formatDate, showNotification) are in utils.js

/**
 * Show error
 */
function showError(message) {
    const tbody = document.getElementById('leads-tbody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="px-6 py-8 text-center text-red-400">
                    ${escapeHtml(message)}
                </td>
            </tr>
        `;
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLeadsManager);
} else {
    initLeadsManager();
}
