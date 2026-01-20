/**
 * TELIS CRM Lead Management JavaScript
 * Handles filtering, sorting, pagination, and lead detail views
 */

// State
let allLeads = [];
let filteredLeads = [];
let currentPage = 1;
let perPage = 25;
let sortField = 'created_at';
let sortDirection = 'desc';
let selectedLeads = new Set();
let totalCount = 0;  // Total number of leads from server
let useServerPagination = true;  // Use server-side pagination

// Status badges
const STATUS_BADGES = {
    'NEW': { label: '🟢 Neu', class: 'bg-green-500/20 text-green-400' },
    'CONTACTED': { label: '🔵 Kontaktiert', class: 'bg-blue-500/20 text-blue-400' },
    'VOICEMAIL': { label: '🟡 Voicemail', class: 'bg-yellow-500/20 text-yellow-400' },
    'INTERESTED': { label: '🟡 Interessiert', class: 'bg-yellow-500/20 text-yellow-400' },
    'INTERVIEW': { label: '🟣 Interview', class: 'bg-purple-500/20 text-purple-400' },
    'HIRED': { label: '🟢 Eingestellt', class: 'bg-emerald-500/20 text-emerald-400' },
    'NOT_INTERESTED': { label: '🔴 Kein Interesse', class: 'bg-red-500/20 text-red-400' },
    'INVALID': { label: '⚫ Ungültig', class: 'bg-gray-500/20 text-gray-400' },
};

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    loadLeads();
    initializeFilters();
    initializePagination();
    initializeSelectionHandlers();
});

/**
 * Load leads from API with server-side pagination and filtering
 */
async function loadLeads() {
    try {
        // Build query parameters for server-side filtering and pagination
        const params = new URLSearchParams();
        params.append('page', currentPage);
        params.append('page_size', perPage);
        
        // Add filter parameters
        const searchTerm = document.getElementById('search-input')?.value || '';
        const statusValue = document.getElementById('status-filter')?.value || '';
        const sourceValue = document.getElementById('source-filter')?.value || '';
        const scoreValue = document.getElementById('score-filter')?.value || '';
        
        if (searchTerm) {
            params.append('search', searchTerm);
        }
        if (statusValue) {
            params.append('status', statusValue);
        }
        if (sourceValue) {
            params.append('source', sourceValue);
        }
        if (scoreValue) {
            // Convert score filter to min_score parameter
            if (scoreValue === 'hot') {
                params.append('min_score', '80');
            } else if (scoreValue === 'medium') {
                params.append('min_score', '50');
            }
            // For 'low' we don't filter by min_score, handled client-side if needed
        }
        
        const response = await fetch(`/api/leads/?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to load leads');
        
        const data = await response.json();
        
        // Handle both paginated response and direct array response
        if (Array.isArray(data)) {
            // Direct array response (backward compatibility)
            allLeads = data;
            filteredLeads = [...allLeads];
            totalCount = allLeads.length;
            useServerPagination = false;
        } else if (data && typeof data === 'object' && Array.isArray(data.results)) {
            // Paginated response
            allLeads = data.results;
            filteredLeads = [...allLeads];
            totalCount = data.count || 0;
            useServerPagination = true;
        } else {
            // Unexpected format, use empty array
            allLeads = [];
            filteredLeads = [];
            totalCount = 0;
            useServerPagination = false;
        }
        
        // Apply additional client-side filtering for 'low' score if needed
        if (scoreValue === 'low') {
            filteredLeads = filteredLeads.filter(lead => {
                const score = lead.quality_score || 0;
                return score < 50;
            });
        }
        
        applySorting();
        renderLeads();
        updatePagination();
    } catch (error) {
        console.error('Error loading leads:', error);
        document.getElementById('leads-tbody').innerHTML = `
            <tr><td colspan="8" class="px-4 py-8 text-center text-red-400">
                Fehler beim Laden der Leads. Bitte versuchen Sie es später erneut.
            </td></tr>
        `;
    }
}

/**
 * Initialize filter inputs
 */
function initializeFilters() {
    const searchInput = document.getElementById('search-input');
    const statusFilter = document.getElementById('status-filter');
    const sourceFilter = document.getElementById('source-filter');
    const scoreFilter = document.getElementById('score-filter');
    
    // Debounce search input
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            applyFilters();
        }, 300);
    });
    
    statusFilter.addEventListener('change', applyFilters);
    sourceFilter.addEventListener('change', applyFilters);
    scoreFilter.addEventListener('change', applyFilters);
    
    // Sort headers
    document.querySelectorAll('[data-sort]').forEach(header => {
        header.addEventListener('click', function() {
            const field = this.dataset.sort;
            if (sortField === field) {
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                sortField = field;
                sortDirection = 'desc';
            }
            applySorting();
            renderLeads();
        });
    });
    
    // Export button
    document.getElementById('export-btn').addEventListener('click', exportLeads);
}

/**
 * Apply filters to leads by reloading from server
 */
function applyFilters() {
    // Reset to page 1 when filters change
    currentPage = 1;
    
    // Reload leads with new filters from server
    loadLeads();
}

/**
 * Apply sorting to filtered leads
 */
function applySorting() {
    filteredLeads.sort((a, b) => {
        let valA, valB;
        
        switch (sortField) {
            case 'name':
                valA = (a.name || '').toLowerCase();
                valB = (b.name || '').toLowerCase();
                break;
            case 'status':
                valA = a.status || '';
                valB = b.status || '';
                break;
            case 'score':
                valA = a.quality_score || 0;
                valB = b.quality_score || 0;
                break;
            case 'created':
                valA = new Date(a.created_at);
                valB = new Date(b.created_at);
                break;
            default:
                valA = a.created_at;
                valB = b.created_at;
        }
        
        if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
        if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
        return 0;
    });
}

/**
 * Render leads in table
 */
function renderLeads() {
    const tbody = document.getElementById('leads-tbody');
    
    // For server-side pagination, all leads are already the correct page
    const leadsToShow = useServerPagination ? filteredLeads : filteredLeads.slice((currentPage - 1) * perPage, currentPage * perPage);
    
    if (leadsToShow.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="8" class="px-4 py-8 text-center text-gray-500">
                Keine Leads gefunden. Versuchen Sie andere Filter.
            </td></tr>
        `;
        return;
    }
    
    tbody.innerHTML = leadsToShow.map(lead => {
        const statusBadge = STATUS_BADGES[lead.status] || STATUS_BADGES['NEW'];
        const scoreStars = Math.min(5, Math.floor(lead.quality_score / 20));
        const scoreColor = lead.quality_score >= 80 ? 'text-primary' : 
                          lead.quality_score >= 50 ? 'text-yellow-400' : 'text-gray-500';
        
        return `
            <tr class="hover:bg-dark-700/30 transition">
                <td class="px-4 py-3">
                    <input type="checkbox" class="lead-checkbox rounded" data-lead-id="${lead.id}">
                </td>
                <td class="px-4 py-3">
                    <div class="text-gray-300 font-medium">${escapeHtml(lead.name)}</div>
                    ${lead.company ? `<div class="text-xs text-gray-500">${escapeHtml(lead.company)}</div>` : ''}
                </td>
                <td class="px-4 py-3">
                    ${lead.telefon ? `<div class="text-sm text-gray-300">📞 ${escapeHtml(lead.telefon)}</div>` : ''}
                    ${lead.email ? `<div class="text-xs text-gray-500">📧 ${escapeHtml(lead.email)}</div>` : ''}
                </td>
                <td class="px-4 py-3 text-center">
                    <span class="inline-block px-2 py-1 rounded text-xs ${statusBadge.class}">
                        ${statusBadge.label}
                    </span>
                </td>
                <td class="px-4 py-3 text-center">
                    <div class="${scoreColor}">
                        ${'⭐'.repeat(scoreStars)}${'☆'.repeat(5 - scoreStars)}
                    </div>
                    <div class="text-xs text-gray-500">${lead.quality_score}</div>
                </td>
                <td class="px-4 py-3 text-center text-gray-400 text-sm">
                    ${getSourceLabel(lead.source)}
                </td>
                <td class="px-4 py-3 text-center text-gray-400 text-xs">
                    ${formatDate(lead.created_at)}
                </td>
                <td class="px-4 py-3 text-center">
                    <div class="flex items-center justify-center space-x-2">
                        <button onclick="viewLeadDetail(${lead.id})" class="text-primary hover:text-primary/80 text-lg" title="Details anzeigen">
                            👁️
                        </button>
                        <button onclick="editLead(${lead.id})" class="text-gray-400 hover:text-gray-300 text-lg" title="Bearbeiten">
                            ✏️
                        </button>
                        <button onclick="callLead(${lead.id})" class="text-cyan-400 hover:text-cyan-300 text-lg" title="Anrufen">
                            📞
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    // Reinitialize checkboxes
    document.querySelectorAll('.lead-checkbox').forEach(cb => {
        cb.checked = selectedLeads.has(parseInt(cb.dataset.leadId));
        cb.addEventListener('change', handleLeadSelection);
    });
}

/**
 * Initialize pagination controls
 */
function initializePagination() {
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            if (useServerPagination) {
                loadLeads();
            } else {
                renderLeads();
                updatePagination();
            }
        }
    });
    
    document.getElementById('next-page').addEventListener('click', () => {
        const totalPages = useServerPagination 
            ? Math.ceil(totalCount / perPage)
            : Math.ceil(filteredLeads.length / perPage);
        if (currentPage < totalPages) {
            currentPage++;
            if (useServerPagination) {
                loadLeads();
            } else {
                renderLeads();
                updatePagination();
            }
        }
    });
    
    document.getElementById('per-page').addEventListener('change', function() {
        perPage = parseInt(this.value);
        currentPage = 1;
        if (useServerPagination) {
            loadLeads();
        } else {
            renderLeads();
            updatePagination();
        }
    });
}

/**
 * Update pagination display
 */
function updatePagination() {
    const total = useServerPagination ? totalCount : filteredLeads.length;
    const totalPages = Math.ceil(total / perPage);
    const start = Math.min((currentPage - 1) * perPage + 1, total);
    const end = Math.min(currentPage * perPage, total);
    
    document.getElementById('showing-from').textContent = start;
    document.getElementById('showing-to').textContent = end;
    document.getElementById('total-leads').textContent = total;
    
    // Enable/disable buttons
    document.getElementById('prev-page').disabled = currentPage === 1;
    document.getElementById('next-page').disabled = currentPage === totalPages || totalPages === 0;
    
    // Page numbers
    const pageNumbers = document.getElementById('page-numbers');
    pageNumbers.innerHTML = '';
    
    // Show max 5 page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage + 1 < maxVisible) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.className = `px-3 py-1 rounded transition ${
            i === currentPage 
                ? 'bg-primary text-white' 
                : 'bg-dark-800 hover:bg-dark-700 text-gray-300'
        }`;
        btn.onclick = () => {
            currentPage = i;
            if (useServerPagination) {
                loadLeads();
            } else {
                renderLeads();
                updatePagination();
            }
        };
        pageNumbers.appendChild(btn);
    }
}

/**
 * Initialize selection handlers
 */
function initializeSelectionHandlers() {
    document.getElementById('select-all').addEventListener('change', function() {
        const isChecked = this.checked;
        document.querySelectorAll('.lead-checkbox').forEach(cb => {
            cb.checked = isChecked;
            const leadId = parseInt(cb.dataset.leadId);
            if (isChecked) {
                selectedLeads.add(leadId);
            } else {
                selectedLeads.delete(leadId);
            }
        });
        updateBulkActions();
    });
}

/**
 * Handle individual lead selection
 */
function handleLeadSelection(event) {
    const leadId = parseInt(event.target.dataset.leadId);
    if (event.target.checked) {
        selectedLeads.add(leadId);
    } else {
        selectedLeads.delete(leadId);
    }
    updateBulkActions();
}

/**
 * Update bulk actions display
 */
function updateBulkActions() {
    const bulkActions = document.getElementById('bulk-actions');
    const count = selectedLeads.size;
    
    if (count > 0) {
        bulkActions.classList.remove('hidden');
        document.getElementById('selected-count').textContent = count;
    } else {
        bulkActions.classList.add('hidden');
    }
}

/**
 * View lead detail in slide-over
 */
async function viewLeadDetail(leadId) {
    const overlay = document.getElementById('lead-detail-overlay');
    const panel = document.getElementById('lead-detail-panel');
    
    overlay.classList.remove('hidden');
    setTimeout(() => {
        panel.classList.remove('translate-x-full');
    }, 10);
    
    // Load lead details
    try {
        const response = await fetch(`/api/leads/${leadId}/`);
        if (!response.ok) throw new Error('Failed to load lead');
        
        const lead = await response.json();
        
        const statusBadge = STATUS_BADGES[lead.status] || STATUS_BADGES['NEW'];
        const scorePercent = lead.quality_score;
        const scoreBarWidth = `${scorePercent}%`;
        
        panel.innerHTML = `
            <div class="p-6">
                <!-- Header -->
                <div class="flex items-center justify-between mb-6">
                    <button onclick="closeLeadDetail()" class="text-gray-400 hover:text-gray-300">
                        ← Zurück
                    </button>
                    <button onclick="editLead(${lead.id})" class="text-primary hover:text-primary/80">
                        ✏️ Bearbeiten
                    </button>
                </div>
                
                <!-- Lead Info -->
                <h2 class="text-2xl font-bold text-gray-100 mb-4">${escapeHtml(lead.name)}</h2>
                
                <!-- Score Bar -->
                <div class="mb-4">
                    <div class="flex items-center justify-between text-sm text-gray-400 mb-2">
                        <span>📊 Score</span>
                        <span class="font-bold text-primary">${lead.quality_score}</span>
                    </div>
                    <div class="w-full bg-dark-700 rounded-full h-2">
                        <div class="bg-primary h-2 rounded-full transition-all" style="width: ${scoreBarWidth}"></div>
                    </div>
                </div>
                
                <!-- Status -->
                <div class="mb-6">
                    <span class="text-sm text-gray-400">📌 Status:</span>
                    <span class="inline-block ml-2 px-3 py-1 rounded ${statusBadge.class}">
                        ${statusBadge.label}
                    </span>
                </div>
                
                <!-- Contact Info -->
                <div class="space-y-3 mb-6 pb-6 border-b border-dark-700">
                    ${lead.telefon ? `
                    <div class="flex items-center justify-between">
                        <span class="text-gray-300">📞 ${escapeHtml(lead.telefon)}</span>
                        <button onclick="callLead(${lead.id})" class="px-3 py-1 bg-primary/20 hover:bg-primary/30 text-primary rounded text-sm">
                            Anrufen
                        </button>
                    </div>
                    ` : ''}
                    ${lead.email ? `
                    <div class="flex items-center justify-between">
                        <span class="text-gray-300">📧 ${escapeHtml(lead.email)}</span>
                        <button class="px-3 py-1 bg-primary/20 hover:bg-primary/30 text-primary rounded text-sm">
                            Email
                        </button>
                    </div>
                    ` : ''}
                    ${lead.company ? `<div class="text-gray-300">🏢 ${escapeHtml(lead.company)}</div>` : ''}
                    ${lead.location ? `<div class="text-gray-300">📍 ${escapeHtml(lead.location)}</div>` : ''}
                    ${lead.linkedin_url ? `<div><a href="${escapeHtml(lead.linkedin_url)}" target="_blank" class="text-primary hover:underline">🔗 LinkedIn</a></div>` : ''}
                    ${lead.xing_url ? `<div><a href="${escapeHtml(lead.xing_url)}" target="_blank" class="text-primary hover:underline">🔗 XING</a></div>` : ''}
                </div>
                
                <!-- Timeline -->
                <div class="mb-6">
                    <h3 class="text-lg font-bold text-gray-100 mb-3">📋 TIMELINE</h3>
                    <div class="space-y-3 text-sm">
                        <div class="p-3 bg-dark-900 rounded">
                            <div class="text-gray-300">🆕 Lead erstellt</div>
                            <div class="text-xs text-gray-500 mt-1">${formatDateTime(lead.created_at)}</div>
                        </div>
                        ${lead.last_called_at ? `
                        <div class="p-3 bg-dark-900 rounded">
                            <div class="text-gray-300">📞 Letzter Anruf</div>
                            <div class="text-xs text-gray-500 mt-1">${formatDateTime(lead.last_called_at)}</div>
                        </div>
                        ` : ''}
                    </div>
                </div>
                
                <!-- Notes -->
                <div>
                    <h3 class="text-lg font-bold text-gray-100 mb-3">📝 NOTIZEN</h3>
                    ${lead.notes ? `
                    <div class="p-3 bg-dark-900 rounded text-gray-300 text-sm mb-3">
                        ${escapeHtml(lead.notes)}
                    </div>
                    ` : ''}
                    <textarea 
                        placeholder="Notiz hinzufügen..." 
                        class="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded text-gray-300 text-sm"
                        rows="3"
                    ></textarea>
                    <button class="mt-2 px-4 py-2 bg-primary/20 hover:bg-primary/30 text-primary rounded text-sm">
                        Notiz speichern
                    </button>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading lead detail:', error);
        panel.innerHTML = `
            <div class="p-6">
                <div class="text-red-400">Fehler beim Laden der Lead-Details</div>
                <button onclick="closeLeadDetail()" class="mt-4 px-4 py-2 bg-dark-700 text-gray-300 rounded">
                    Schließen
                </button>
            </div>
        `;
    }
}

/**
 * Close lead detail slide-over
 */
function closeLeadDetail() {
    const overlay = document.getElementById('lead-detail-overlay');
    const panel = document.getElementById('lead-detail-panel');
    
    panel.classList.add('translate-x-full');
    setTimeout(() => {
        overlay.classList.add('hidden');
    }, 300);
}

/**
 * Edit lead (placeholder)
 */
function editLead(leadId) {
    alert(`Lead ${leadId} bearbeiten - Coming Soon`);
}

/**
 * Call lead (placeholder)
 */
function callLead(leadId) {
    alert(`Lead ${leadId} anrufen - Coming Soon (öffnet Telefon-Dashboard)`);
}

/**
 * Export leads to CSV
 */
async function exportLeads() {
    try {
        // If using server pagination, fetch all filtered leads for export
        let leadsToExport = filteredLeads;
        
        if (useServerPagination && totalCount > filteredLeads.length) {
            // Fetch all pages for export
            const params = new URLSearchParams();
            params.append('page_size', totalCount); // Get all results in one page
            
            // Add current filter parameters
            const searchTerm = document.getElementById('search-input')?.value || '';
            const statusValue = document.getElementById('status-filter')?.value || '';
            const sourceValue = document.getElementById('source-filter')?.value || '';
            const scoreValue = document.getElementById('score-filter')?.value || '';
            
            if (searchTerm) params.append('search', searchTerm);
            if (statusValue) params.append('status', statusValue);
            if (sourceValue) params.append('source', sourceValue);
            if (scoreValue === 'hot') params.append('min_score', '80');
            else if (scoreValue === 'medium') params.append('min_score', '50');
            
            const response = await fetch(`/api/leads/?${params.toString()}`);
            if (response.ok) {
                const data = await response.json();
                leadsToExport = Array.isArray(data) ? data : (data.results || []);
                
                // Apply client-side 'low' filter if needed
                if (scoreValue === 'low') {
                    leadsToExport = leadsToExport.filter(lead => (lead.quality_score || 0) < 50);
                }
            }
        }
        
        // Create CSV content
        const headers = ['Name', 'Email', 'Telefon', 'Firma', 'Status', 'Score', 'Quelle', 'Erstellt'];
        const rows = leadsToExport.map(lead => [
            lead.name,
            lead.email || '',
            lead.telefon || '',
            lead.company || '',
            lead.status,
            lead.quality_score,
            lead.source,
            lead.created_at
        ]);
        
        let csv = headers.join(',') + '\n';
        rows.forEach(row => {
            csv += row.map(cell => `"${cell}"`).join(',') + '\n';
        });
        
        // Download
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `telis_leads_${new Date().toISOString().split('T')[0]}.csv`);
        link.click();
    } catch (error) {
        console.error('Error exporting leads:', error);
        alert('Fehler beim Exportieren der Leads');
    }
}

// Helper functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('de-DE', { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function getSourceLabel(source) {
    const labels = {
        'scraper': 'Scraper',
        'landing_page': 'Landing',
        'manual': 'Manuell',
        'referral': 'Empfehlung'
    };
    return labels[source] || source;
}

// ==========================================
// BATCH OPERATIONS
// ==========================================

/**
 * Batch update status for selected leads
 */
async function batchUpdateStatus(newStatus) {
    const leadIds = Array.from(selectedLeads);
    if (leadIds.length === 0) {
        alert('Bitte wählen Sie mindestens einen Lead aus');
        return;
    }
    
    if (!confirm(`Möchten Sie den Status von ${leadIds.length} Lead(s) ändern?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/leads/batch_update_status/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                lead_ids: leadIds,
                status: newStatus
            })
        });
        
        const data = await response.json();
        if (data.success) {
            alert(`${data.updated_count} Lead(s) erfolgreich aktualisiert`);
            selectedLeads.clear();
            loadLeads();
        } else {
            alert('Fehler: ' + data.error);
        }
    } catch (error) {
        console.error('Error updating status:', error);
        alert('Fehler beim Aktualisieren des Status');
    }
    
    // Hide dropdown
    document.getElementById('status-dropdown').classList.add('hidden');
}

/**
 * Show add tags modal
 */
function showAddTagsModal() {
    if (selectedLeads.size === 0) {
        alert('Bitte wählen Sie mindestens einen Lead aus');
        return;
    }
    document.getElementById('add-tags-modal').classList.remove('hidden');
}

function closeAddTagsModal() {
    document.getElementById('add-tags-modal').classList.add('hidden');
    document.getElementById('tags-input').value = '';
}

/**
 * Confirm add tags
 */
async function confirmAddTags() {
    const tagsInput = document.getElementById('tags-input').value.trim();
    if (!tagsInput) {
        alert('Bitte geben Sie mindestens ein Tag ein');
        return;
    }
    
    const tags = tagsInput.split(',').map(t => t.trim()).filter(t => t);
    const leadIds = Array.from(selectedLeads);
    
    try {
        const response = await fetch('/api/leads/batch_add_tags/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                lead_ids: leadIds,
                tags: tags
            })
        });
        
        const data = await response.json();
        if (data.success) {
            alert(`Tags erfolgreich zu ${data.updated_count} Lead(s) hinzugefügt`);
            closeAddTagsModal();
            selectedLeads.clear();
            loadLeads();
        } else {
            alert('Fehler: ' + data.error);
        }
    } catch (error) {
        console.error('Error adding tags:', error);
        alert('Fehler beim Hinzufügen der Tags');
    }
}

/**
 * Show assign modal
 */
async function showAssignModal() {
    if (selectedLeads.size === 0) {
        alert('Bitte wählen Sie mindestens einen Lead aus');
        return;
    }
    
    // Load users for assignment
    try {
        const response = await fetch('/api/users/');
        if (response.ok) {
            const users = await response.json();
            const select = document.getElementById('assign-user-select');
            select.innerHTML = '<option value="">Bitte wählen...</option>';
            users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = user.full_name || user.username;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
    
    document.getElementById('assign-modal').classList.remove('hidden');
}

function closeAssignModal() {
    document.getElementById('assign-modal').classList.add('hidden');
}

/**
 * Confirm assignment
 */
async function confirmAssign() {
    const userId = document.getElementById('assign-user-select').value;
    if (!userId) {
        alert('Bitte wählen Sie einen Benutzer aus');
        return;
    }
    
    const leadIds = Array.from(selectedLeads);
    
    try {
        const response = await fetch('/api/leads/batch_assign/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                lead_ids: leadIds,
                user_id: parseInt(userId)
            })
        });
        
        const data = await response.json();
        if (data.success) {
            alert(`${data.updated_count} Lead(s) erfolgreich zugewiesen an ${data.assigned_to}`);
            closeAssignModal();
            selectedLeads.clear();
            loadLeads();
        } else {
            alert('Fehler: ' + data.error);
        }
    } catch (error) {
        console.error('Error assigning leads:', error);
        alert('Fehler beim Zuweisen der Leads');
    }
}

/**
 * Batch delete selected leads
 */
async function batchDelete() {
    const leadIds = Array.from(selectedLeads);
    if (leadIds.length === 0) {
        alert('Bitte wählen Sie mindestens einen Lead aus');
        return;
    }
    
    if (!confirm(`Möchten Sie wirklich ${leadIds.length} Lead(s) löschen? Diese Aktion kann nicht rückgängig gemacht werden.`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/leads/batch_delete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                lead_ids: leadIds
            })
        });
        
        const data = await response.json();
        if (data.success) {
            alert(`${data.deleted_count} Lead(s) erfolgreich gelöscht`);
            selectedLeads.clear();
            loadLeads();
        } else {
            alert('Fehler: ' + data.error);
        }
    } catch (error) {
        console.error('Error deleting leads:', error);
        alert('Fehler beim Löschen der Leads');
    }
}

// ==========================================
// SAVED FILTERS
// ==========================================

/**
 * Load saved filters
 */
async function loadSavedFilters() {
    try {
        const response = await fetch('/crm/api/saved-filters/');
        if (response.ok) {
            const filters = await response.json();
            renderSavedFilters(filters);
        }
    } catch (error) {
        console.error('Error loading saved filters:', error);
    }
}

/**
 * Render saved filters in dropdown
 */
function renderSavedFilters(filters) {
    const container = document.getElementById('filters-list');
    if (!container) return;
    
    if (filters.length === 0) {
        container.innerHTML = '<div class="px-4 py-2 text-sm text-gray-500">Keine Filter gespeichert</div>';
        return;
    }
    
    container.innerHTML = '';
    filters.forEach(filter => {
        const item = document.createElement('button');
        item.className = 'block w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-dark-600';
        
        // Safely escape HTML content
        const escapedName = escapeHtml(filter.name);
        const escapedDescription = filter.description ? escapeHtml(filter.description) : '';
        
        item.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${escapedName}</span>
                ${filter.is_owner ? '<button onclick="deleteFilter(event, ' + parseInt(filter.id) + ')" class="text-red-400 hover:text-red-300 ml-2">🗑️</button>' : ''}
            </div>
            ${escapedDescription ? '<div class="text-xs text-gray-500 mt-1">' + escapedDescription + '</div>' : ''}
        `;
        item.onclick = (e) => {
            if (e.target.tagName !== 'BUTTON') {
                applyFilter(filter);
            }
        };
        container.appendChild(item);
    });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Apply a saved filter
 */
function applyFilter(filter) {
    const params = filter.filter_params;
    
    // Apply filter parameters to the UI
    if (params.search) {
        document.getElementById('search-input').value = params.search;
    }
    if (params.status) {
        document.getElementById('status-filter').value = params.status;
    }
    if (params.source) {
        document.getElementById('source-filter').value = params.source;
    }
    if (params.score) {
        document.getElementById('score-filter').value = params.score;
    }
    
    // Apply filters
    applyFilters();
    
    // Hide dropdown
    document.getElementById('filters-dropdown').classList.add('hidden');
}

/**
 * Show save filter modal
 */
function saveCurrentFilter() {
    // Get current filter state
    const filterParams = {
        search: document.getElementById('search-input').value,
        status: document.getElementById('status-filter').value,
        source: document.getElementById('source-filter').value,
        score: document.getElementById('score-filter').value
    };
    
    // Check if any filters are active
    if (!filterParams.search && !filterParams.status && !filterParams.source && !filterParams.score) {
        alert('Bitte wenden Sie zuerst Filter an, bevor Sie sie speichern');
        return;
    }
    
    document.getElementById('save-filter-modal').classList.remove('hidden');
}

function closeSaveFilterModal() {
    document.getElementById('save-filter-modal').classList.add('hidden');
    document.getElementById('filter-name-input').value = '';
    document.getElementById('filter-description-input').value = '';
    document.getElementById('filter-shared-checkbox').checked = false;
}

/**
 * Confirm save filter
 */
async function confirmSaveFilter() {
    const name = document.getElementById('filter-name-input').value.trim();
    if (!name) {
        alert('Bitte geben Sie einen Filter-Namen ein');
        return;
    }
    
    const description = document.getElementById('filter-description-input').value.trim();
    const isShared = document.getElementById('filter-shared-checkbox').checked;
    
    const filterParams = {
        search: document.getElementById('search-input').value,
        status: document.getElementById('status-filter').value,
        source: document.getElementById('source-filter').value,
        score: document.getElementById('score-filter').value
    };
    
    try {
        const response = await fetch('/crm/api/saved-filters/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                name: name,
                description: description,
                filter_params: filterParams,
                is_shared: isShared
            })
        });
        
        const data = await response.json();
        if (data.success) {
            alert('Filter erfolgreich gespeichert');
            closeSaveFilterModal();
            loadSavedFilters();
        } else {
            alert('Fehler: ' + data.error);
        }
    } catch (error) {
        console.error('Error saving filter:', error);
        alert('Fehler beim Speichern des Filters');
    }
}

/**
 * Delete a saved filter
 */
async function deleteFilter(event, filterId) {
    event.stopPropagation();
    
    if (!confirm('Möchten Sie diesen Filter wirklich löschen?')) {
        return;
    }
    
    try {
        const response = await fetch(`/crm/api/saved-filters/${filterId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const data = await response.json();
        if (data.success) {
            loadSavedFilters();
        } else {
            alert('Fehler: ' + data.error);
        }
    } catch (error) {
        console.error('Error deleting filter:', error);
        alert('Fehler beim Löschen des Filters');
    }
}

// Toggle dropdowns
document.addEventListener('DOMContentLoaded', function() {
    // Status dropdown toggle
    const statusBtn = document.getElementById('status-change-btn');
    const statusDropdown = document.getElementById('status-dropdown');
    if (statusBtn) {
        statusBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            statusDropdown.classList.toggle('hidden');
        });
    }
    
    // Filters dropdown toggle
    const filtersBtn = document.getElementById('filters-btn');
    const filtersDropdown = document.getElementById('filters-dropdown');
    if (filtersBtn) {
        filtersBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            filtersDropdown.classList.toggle('hidden');
            if (!filtersDropdown.classList.contains('hidden')) {
                loadSavedFilters();
            }
        });
    }
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function() {
        if (statusDropdown) statusDropdown.classList.add('hidden');
        if (filtersDropdown) filtersDropdown.classList.add('hidden');
    });
});

/**
 * Get CSRF token from cookie
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
