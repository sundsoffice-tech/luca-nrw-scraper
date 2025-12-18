/**
 * Enhanced Leads Manager JavaScript
 * Handles lead listing, filtering, sorting, selection, and bulk operations
 */

// State management
let currentPage = 1;
let perPage = 50;
let currentFilters = {
    search: '',
    phone: 'all',
    email: 'all',
    source: 'all',
    date: 'all',
    date_from: '',
    date_to: '',
    industry: 'all',
    quality: 'all',
    lead_type: 'all',
    status: 'all'
};
let currentSort = { 
    column: 'created_at', 
    direction: 'desc' 
};
let selectedLeads = new Set();

/**
 * Initialize leads manager
 */
function initLeadsManager() {
    setupEventListeners();
    loadLeads();
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Search input with debouncing
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentFilters.search = e.target.value;
                currentPage = 1;
                loadLeads();
            }, 300);
        });
    }
    
    // All filter dropdowns
    const filterIds = ['filter-phone', 'filter-email', 'filter-source', 'filter-date', 
                       'filter-industry', 'filter-quality', 'filter-lead-type', 'filter-status'];
    
    filterIds.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', (e) => {
                const filterName = id.replace('filter-', '').replace('-', '_');
                currentFilters[filterName] = e.target.value;
                
                // Show/hide custom date range
                if (id === 'filter-date') {
                    const customRange = document.getElementById('custom-date-range');
                    if (e.target.value === 'custom') {
                        customRange.classList.remove('hidden');
                    } else {
                        customRange.classList.add('hidden');
                    }
                }
                
                currentPage = 1;
                loadLeads();
            });
        }
    });
    
    // Custom date range
    const dateFrom = document.getElementById('date-from');
    const dateTo = document.getElementById('date-to');
    if (dateFrom && dateTo) {
        dateFrom.addEventListener('change', (e) => {
            currentFilters.date_from = e.target.value;
            currentPage = 1;
            loadLeads();
        });
        dateTo.addEventListener('change', (e) => {
            currentFilters.date_to = e.target.value;
            currentPage = 1;
            loadLeads();
        });
    }
    
    // Clear filters button
    const clearBtn = document.getElementById('filter-clear');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            currentFilters = {
                search: '',
                phone: 'all',
                email: 'all',
                source: 'all',
                date: 'all',
                date_from: '',
                date_to: '',
                industry: 'all',
                quality: 'all',
                lead_type: 'all',
                status: 'all'
            };
            
            // Reset all form elements
            document.getElementById('search-input').value = '';
            filterIds.forEach(id => {
                const element = document.getElementById(id);
                if (element) element.value = 'all';
            });
            document.getElementById('date-from').value = '';
            document.getElementById('date-to').value = '';
            document.getElementById('custom-date-range').classList.add('hidden');
            
            currentPage = 1;
            loadLeads();
        });
    }
}

/**
 * Load leads from API with filters and sorting
 */
async function loadLeads() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            per_page: perPage,
            sort: currentSort.column,
            dir: currentSort.direction,
            ...currentFilters
        });
        
        const response = await fetch(`/api/leads?${params}`);
        const data = await response.json();
        
        if (data.error) {
            showError('Fehler beim Laden der Leads: ' + data.error);
            return;
        }
        
        renderLeads(data.leads);
        renderPagination(data.pagination);
        updateSortIndicators();
        
    } catch (error) {
        console.error('Error loading leads:', error);
        showError('Fehler beim Laden der Leads');
    }
}

/**
 * Render leads table with checkboxes
 */
function renderLeads(leads) {
    const tbody = document.getElementById('leads-tbody');
    if (!tbody) return;
    
    if (leads.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="px-6 py-8 text-center text-gray-500">
                    Keine Leads gefunden
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = leads.map(lead => {
        const mobile = lead.telefon || '';
        const company = lead.company_name || '';
        const source = lead.quelle || '';
        const confidence = lead.confidence_score || 0;
        
        return `
            <tr class="border-b border-gray-700 hover:bg-gray-750">
                <td class="p-3">
                    <input type="checkbox" 
                           class="lead-checkbox rounded" 
                           data-id="${lead.id}"
                           ${selectedLeads.has(lead.id) ? 'checked' : ''}
                           onchange="toggleLeadSelection(${lead.id})">
                </td>
                <td class="p-3 font-medium">${escapeHtml(lead.name || '-')}</td>
                <td class="p-3">
                    ${mobile ? `<span class="text-green-400">${escapeHtml(mobile)}</span>` : '<span class="text-gray-500">-</span>'}
                </td>
                <td class="p-3">${escapeHtml(lead.email || '-')}</td>
                <td class="p-3">${escapeHtml(company || '-')}</td>
                <td class="p-3">
                    <span class="px-2 py-1 rounded text-xs ${getSourceBadgeClass(source)}">
                        ${getSourceName(source)}
                    </span>
                </td>
                <td class="p-3 text-gray-400 text-sm">${formatDate(lead.last_updated)}</td>
                <td class="p-3">
                    <div class="flex items-center gap-2">
                        <div class="w-16 bg-gray-700 rounded-full h-2">
                            <div class="bg-green-500 h-2 rounded-full" style="width: ${confidence}%"></div>
                        </div>
                        <span class="text-xs text-gray-400">${confidence}%</span>
                    </div>
                </td>
                <td class="p-3">
                    <div class="flex gap-1">
                        <button onclick="exportSingleLead(${lead.id})" class="p-1 hover:bg-gray-600 rounded text-sm" title="Exportieren">
                            📤
                        </button>
                        <button onclick="deleteSingleLead(${lead.id})" class="p-1 hover:bg-red-600 rounded text-sm" title="Löschen">
                            🗑️
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Render pagination
 */
function renderPagination(pagination) {
    const paginationDiv = document.getElementById('pagination');
    if (!paginationDiv) return;
    
    const infoDiv = document.getElementById('leads-info');
    if (infoDiv) {
        infoDiv.textContent = `Zeige Seite ${pagination.page} von ${pagination.total_pages} (${pagination.total} Leads gesamt)`;
    }
    
    if (pagination.total_pages <= 1) {
        paginationDiv.innerHTML = '';
        return;
    }
    
    let html = '<div class="flex gap-2 items-center">';
    
    // Previous button
    if (pagination.page > 1) {
        html += `<button onclick="changePage(${pagination.page - 1})" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded">◀ Zurück</button>`;
    }
    
    // Page numbers
    const maxButtons = 5;
    let startPage = Math.max(1, pagination.page - Math.floor(maxButtons / 2));
    let endPage = Math.min(pagination.total_pages, startPage + maxButtons - 1);
    
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
        if (i === pagination.page) {
            html += `<button class="px-3 py-1 bg-blue-600 rounded">${i}</button>`;
        } else {
            html += `<button onclick="changePage(${i})" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded">${i}</button>`;
        }
    }
    
    if (endPage < pagination.total_pages) {
        if (endPage < pagination.total_pages - 1) {
            html += `<span class="px-2">...</span>`;
        }
        html += `<button onclick="changePage(${pagination.total_pages})" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded">${pagination.total_pages}</button>`;
    }
    
    // Next button
    if (pagination.page < pagination.total_pages) {
        html += `<button onclick="changePage(${pagination.page + 1})" class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded">Weiter ▶</button>`;
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
 * Sort by column
 */
function sortBy(column) {
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'asc';
    }
    loadLeads();
}

/**
 * Update sort indicators in table headers
 */
function updateSortIndicators() {
    document.querySelectorAll('.sortable').forEach(th => {
        const sortColumn = th.getAttribute('data-sort');
        const icon = th.querySelector('.sort-icon');
        if (icon) {
            if (sortColumn === currentSort.column) {
                icon.textContent = currentSort.direction === 'asc' ? '↑' : '↓';
            } else {
                icon.textContent = '↕';
            }
        }
    });
}

/**
 * Toggle lead selection
 */
function toggleLeadSelection(id) {
    if (selectedLeads.has(id)) {
        selectedLeads.delete(id);
    } else {
        selectedLeads.add(id);
    }
    updateSelectionBar();
}

/**
 * Select all leads on current page
 */
function selectAll(checked) {
    const checkboxes = document.querySelectorAll('.lead-checkbox');
    checkboxes.forEach(cb => {
        const id = parseInt(cb.dataset.id);
        cb.checked = checked;
        if (checked) {
            selectedLeads.add(id);
        } else {
            selectedLeads.delete(id);
        }
    });
    updateSelectionBar();
}

/**
 * Clear selection
 */
function clearSelection() {
    selectedLeads.clear();
    document.querySelectorAll('.lead-checkbox').forEach(cb => cb.checked = false);
    document.getElementById('select-all').checked = false;
    updateSelectionBar();
}

/**
 * Update selection bar visibility and count
 */
function updateSelectionBar() {
    const bar = document.getElementById('selection-bar');
    const count = document.getElementById('selection-count');
    
    if (selectedLeads.size > 0) {
        bar.classList.remove('hidden');
        count.textContent = selectedLeads.size;
    } else {
        bar.classList.add('hidden');
    }
}

/**
 * Export selected leads
 */
async function exportSelected(format) {
    if (selectedLeads.size === 0) {
        showNotification('Keine Leads ausgewählt', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/leads/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ids: Array.from(selectedLeads),
                format: format
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const contentDisposition = response.headers.get('Content-Disposition');
            const filename = contentDisposition ? 
                contentDisposition.split('filename=')[1]?.replace(/"/g, '') : 
                `export.${format}`;
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            window.URL.revokeObjectURL(url);
            
            showNotification(`${selectedLeads.size} Leads exportiert`, 'success');
        } else {
            const error = await response.json();
            showNotification(error.error || 'Fehler beim Exportieren', 'error');
        }
    } catch (error) {
        console.error('Export error:', error);
        showNotification('Fehler beim Exportieren', 'error');
    }
}

/**
 * Export all leads with current filters
 */
async function exportAll(format) {
    try {
        const response = await fetch('/api/leads/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filters: currentFilters,
                format: format
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const contentDisposition = response.headers.get('Content-Disposition');
            const filename = contentDisposition ? 
                contentDisposition.split('filename=')[1]?.replace(/"/g, '') : 
                `export.${format}`;
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            window.URL.revokeObjectURL(url);
            
            showNotification('Export erstellt', 'success');
        } else {
            const error = await response.json();
            showNotification(error.error || 'Fehler beim Exportieren', 'error');
        }
    } catch (error) {
        console.error('Export error:', error);
        showNotification('Fehler beim Exportieren', 'error');
    }
}

/**
 * Export single lead
 */
async function exportSingleLead(id) {
    try {
        const response = await fetch('/api/leads/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ids: [id],
                format: 'vcard'
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `lead_${id}.vcf`;
            a.click();
            window.URL.revokeObjectURL(url);
            
            showNotification('Lead exportiert', 'success');
        } else {
            showNotification('Fehler beim Exportieren', 'error');
        }
    } catch (error) {
        console.error('Export error:', error);
        showNotification('Fehler beim Exportieren', 'error');
    }
}

/**
 * Delete selected leads
 */
async function deleteSelected() {
    if (selectedLeads.size === 0) {
        showNotification('Keine Leads ausgewählt', 'error');
        return;
    }
    
    if (!confirm(`${selectedLeads.size} Leads wirklich löschen?`)) return;
    
    try {
        const response = await fetch('/api/leads/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids: Array.from(selectedLeads) })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message, 'success');
            selectedLeads.clear();
            updateSelectionBar();
            loadLeads();
        } else {
            showNotification(data.error || 'Fehler beim Löschen', 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('Fehler beim Löschen', 'error');
    }
}

/**
 * Delete single lead
 */
async function deleteSingleLead(id) {
    if (!confirm('Lead wirklich löschen?')) return;
    
    try {
        const response = await fetch(`/api/leads/${id}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (data.success) {
            showNotification('Lead gelöscht', 'success');
            selectedLeads.delete(id);
            loadLeads();
        } else {
            showNotification(data.error || 'Fehler beim Löschen', 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('Fehler beim Löschen', 'error');
    }
}

/**
 * Helper: Get source badge class
 */
function getSourceBadgeClass(source) {
    if (!source) return 'bg-gray-700 text-gray-300';
    const lower = source.toLowerCase();
    if (lower.includes('linkedin')) return 'bg-blue-900 text-blue-200';
    if (lower.includes('xing')) return 'bg-green-900 text-green-200';
    if (lower.includes('google')) return 'bg-red-900 text-red-200';
    if (lower.includes('facebook')) return 'bg-indigo-900 text-indigo-200';
    if (lower.includes('kleinanzeigen')) return 'bg-yellow-900 text-yellow-200';
    if (lower.includes('perplexity')) return 'bg-purple-900 text-purple-200';
    return 'bg-gray-700 text-gray-300';
}

/**
 * Helper: Get source name
 */
function getSourceName(source) {
    if (!source) return 'Unbekannt';
    const lower = source.toLowerCase();
    if (lower.includes('linkedin')) return 'LinkedIn';
    if (lower.includes('xing')) return 'Xing';
    if (lower.includes('google')) return 'Google';
    if (lower.includes('facebook')) return 'Facebook';
    if (lower.includes('kleinanzeigen')) return 'Kleinanzeigen';
    if (lower.includes('perplexity')) return 'Perplexity';
    return getDomain(source);
}

/**
 * Show error
 */
function showError(message) {
    const tbody = document.getElementById('leads-tbody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="px-6 py-8 text-center text-red-400">
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
