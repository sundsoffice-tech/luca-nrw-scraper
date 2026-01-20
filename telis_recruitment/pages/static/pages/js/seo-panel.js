/**
 * SEO Panel for Page Builder
 * 
 * This module provides SEO tools and analysis in the page builder interface:
 * - SEO metadata editor
 * - Real-time SEO analysis
 * - Google/Facebook preview
 * - Slug editor
 */

class SEOPanel {
    constructor(pageSlug) {
        this.pageSlug = pageSlug;
        this.analysisData = null;
        this.init();
    }

    init() {
        this.createPanel();
        this.attachEventListeners();
        this.loadSEOData();
    }

    createPanel() {
        const panel = document.createElement('div');
        panel.id = 'seo-panel';
        panel.className = 'seo-panel';
        panel.innerHTML = `
            <div class="seo-panel-header">
                <h3>SEO Tools</h3>
                <button class="seo-panel-toggle" title="Toggle SEO Panel">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                </button>
            </div>

            <div class="seo-panel-content">
                <!-- Tabs -->
                <div class="seo-tabs">
                    <button class="seo-tab active" data-tab="editor">Editor</button>
                    <button class="seo-tab" data-tab="analysis">Analysis</button>
                    <button class="seo-tab" data-tab="preview">Preview</button>
                </div>

                <!-- Editor Tab -->
                <div class="seo-tab-content" data-tab="editor">
                    <div class="seo-section">
                        <label for="seo-slug">URL Slug</label>
                        <div class="seo-slug-wrapper">
                            <input type="text" id="seo-slug" class="seo-input" placeholder="page-url-slug">
                            <button class="seo-slug-update btn-sm">Update</button>
                        </div>
                        <small class="seo-hint">URL: <span id="slug-preview">/p/...</span></small>
                    </div>

                    <div class="seo-section">
                        <label for="seo-title">SEO Title</label>
                        <input type="text" id="seo-title" class="seo-input" maxlength="60" placeholder="Page Title">
                        <div class="seo-char-count">
                            <span id="title-count">0</span>/60 characters
                            <span id="title-status" class="status-indicator"></span>
                        </div>
                    </div>

                    <div class="seo-section">
                        <label for="seo-description">Meta Description</label>
                        <textarea id="seo-description" class="seo-textarea" maxlength="160" rows="3" placeholder="Brief description of the page"></textarea>
                        <div class="seo-char-count">
                            <span id="desc-count">0</span>/160 characters
                            <span id="desc-status" class="status-indicator"></span>
                        </div>
                    </div>

                    <div class="seo-section">
                        <label for="seo-keywords">Keywords (comma-separated)</label>
                        <input type="text" id="seo-keywords" class="seo-input" placeholder="keyword1, keyword2, keyword3">
                    </div>

                    <div class="seo-section">
                        <label for="seo-image">Social Image URL</label>
                        <input type="url" id="seo-image" class="seo-input" placeholder="https://...">
                    </div>

                    <div class="seo-section seo-section-collapse">
                        <button class="seo-collapse-toggle">Advanced Settings ▼</button>
                        <div class="seo-collapse-content">
                            <label for="canonical-url">Canonical URL</label>
                            <input type="url" id="canonical-url" class="seo-input" placeholder="https://...">

                            <label for="robots-meta">Robots Meta</label>
                            <select id="robots-meta" class="seo-select">
                                <option value="index, follow">Index, Follow</option>
                                <option value="noindex, follow">No Index, Follow</option>
                                <option value="index, nofollow">Index, No Follow</option>
                                <option value="noindex, nofollow">No Index, No Follow</option>
                            </select>

                            <label for="og-type">Open Graph Type</label>
                            <select id="og-type" class="seo-select">
                                <option value="website">Website</option>
                                <option value="article">Article</option>
                                <option value="product">Product</option>
                            </select>

                            <label for="twitter-card">Twitter Card Type</label>
                            <select id="twitter-card" class="seo-select">
                                <option value="summary_large_image">Summary Large Image</option>
                                <option value="summary">Summary</option>
                                <option value="app">App</option>
                                <option value="player">Player</option>
                            </select>

                            <label for="sitemap-priority">Sitemap Priority</label>
                            <input type="range" id="sitemap-priority" min="0" max="1" step="0.1" value="0.5">
                            <span id="priority-value">0.5</span>

                            <label for="sitemap-changefreq">Change Frequency</label>
                            <select id="sitemap-changefreq" class="seo-select">
                                <option value="daily">Daily</option>
                                <option value="weekly" selected>Weekly</option>
                                <option value="monthly">Monthly</option>
                                <option value="yearly">Yearly</option>
                            </select>
                        </div>
                    </div>

                    <button class="seo-save-btn btn-primary">Save SEO Settings</button>
                </div>

                <!-- Analysis Tab -->
                <div class="seo-tab-content hidden" data-tab="analysis">
                    <div class="seo-score-section">
                        <div class="seo-score-circle">
                            <div class="score-value">--</div>
                            <div class="score-grade">-</div>
                        </div>
                        <button class="seo-analyze-btn btn-primary">Analyze Page</button>
                    </div>

                    <div id="seo-analysis-results" class="seo-results hidden">
                        <div class="seo-issues"></div>
                        <div class="seo-warnings"></div>
                        <div class="seo-suggestions"></div>
                    </div>
                </div>

                <!-- Preview Tab -->
                <div class="seo-tab-content hidden" data-tab="preview">
                    <h4>Google Search Preview</h4>
                    <div class="google-preview">
                        <div class="google-url"></div>
                        <div class="google-title"></div>
                        <div class="google-description"></div>
                    </div>

                    <h4>Facebook Preview</h4>
                    <div class="facebook-preview">
                        <div class="fb-image"></div>
                        <div class="fb-content">
                            <div class="fb-title"></div>
                            <div class="fb-description"></div>
                            <div class="fb-url"></div>
                        </div>
                    </div>

                    <h4>Twitter Card Preview</h4>
                    <div class="twitter-preview">
                        <div class="tw-image"></div>
                        <div class="tw-content">
                            <div class="tw-title"></div>
                            <div class="tw-description"></div>
                            <div class="tw-url"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Append to builder interface
        const builderContent = document.querySelector('.builder-content');
        if (builderContent) {
            builderContent.appendChild(panel);
        }
    }

    attachEventListeners() {
        // Tab switching
        document.querySelectorAll('.seo-tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Panel toggle
        document.querySelector('.seo-panel-toggle')?.addEventListener('click', () => {
            document.querySelector('#seo-panel').classList.toggle('collapsed');
        });

        // Collapse toggle
        document.querySelector('.seo-collapse-toggle')?.addEventListener('click', (e) => {
            e.target.parentElement.classList.toggle('expanded');
        });

        // Character counters
        const titleInput = document.getElementById('seo-title');
        const descInput = document.getElementById('seo-description');

        titleInput?.addEventListener('input', () => {
            this.updateCharCount('title', titleInput.value.length, 60);
            this.updatePreviews();
        });

        descInput?.addEventListener('input', () => {
            this.updateCharCount('desc', descInput.value.length, 160);
            this.updatePreviews();
        });

        // Slug update
        document.querySelector('.seo-slug-update')?.addEventListener('click', () => {
            this.updateSlug();
        });

        // Save SEO settings
        document.querySelector('.seo-save-btn')?.addEventListener('click', () => {
            this.saveSEOSettings();
        });

        // Analyze button
        document.querySelector('.seo-analyze-btn')?.addEventListener('click', () => {
            this.analyzePage();
        });

        // Priority slider
        document.getElementById('sitemap-priority')?.addEventListener('input', (e) => {
            document.getElementById('priority-value').textContent = e.target.value;
        });

        // Update previews on any input change
        document.querySelectorAll('.seo-input, .seo-textarea, .seo-select').forEach(el => {
            el.addEventListener('input', () => this.updatePreviews());
        });
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.seo-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });

        // Update tab contents
        document.querySelectorAll('.seo-tab-content').forEach(content => {
            content.classList.toggle('hidden', content.dataset.tab !== tabName);
        });
    }

    updateCharCount(field, count, max) {
        const countEl = document.getElementById(`${field}-count`);
        const statusEl = document.getElementById(`${field}-status`);
        
        countEl.textContent = count;

        // Update status indicator
        if (count === 0) {
            statusEl.className = 'status-indicator status-error';
            statusEl.textContent = '⚠️ Required';
        } else if (count < max * 0.5) {
            statusEl.className = 'status-indicator status-warning';
            statusEl.textContent = '⚠️ Too short';
        } else if (count > max) {
            statusEl.className = 'status-indicator status-error';
            statusEl.textContent = '⚠️ Too long';
        } else {
            statusEl.className = 'status-indicator status-good';
            statusEl.textContent = '✓ Good';
        }
    }

    async loadSEOData() {
        try {
            const response = await fetch(`/crm/pages/api/${this.pageSlug}/load/`);
            const data = await response.json();

            // Populate form fields
            document.getElementById('seo-slug').value = this.pageSlug;
            document.getElementById('seo-title').value = data.seo_title || '';
            document.getElementById('seo-description').value = data.seo_description || '';
            document.getElementById('seo-keywords').value = data.seo_keywords || '';
            document.getElementById('seo-image').value = data.seo_image || '';
            document.getElementById('canonical-url').value = data.canonical_url || '';
            document.getElementById('robots-meta').value = data.robots_meta || 'index, follow';
            document.getElementById('og-type').value = data.og_type || 'website';
            document.getElementById('twitter-card').value = data.twitter_card || 'summary_large_image';
            document.getElementById('sitemap-priority').value = data.sitemap_priority || 0.5;
            document.getElementById('priority-value').textContent = data.sitemap_priority || 0.5;
            document.getElementById('sitemap-changefreq').value = data.sitemap_changefreq || 'weekly';

            // Update char counts
            this.updateCharCount('title', data.seo_title?.length || 0, 60);
            this.updateCharCount('desc', data.seo_description?.length || 0, 160);

            // Update slug preview
            document.getElementById('slug-preview').textContent = `/p/${this.pageSlug}/`;

            // Update previews
            this.updatePreviews();
        } catch (error) {
            console.error('Failed to load SEO data:', error);
        }
    }

    async saveSEOSettings() {
        const data = {
            seo_title: document.getElementById('seo-title').value,
            seo_description: document.getElementById('seo-description').value,
            seo_keywords: document.getElementById('seo-keywords').value,
            seo_image: document.getElementById('seo-image').value,
            canonical_url: document.getElementById('canonical-url').value,
            robots_meta: document.getElementById('robots-meta').value,
            og_type: document.getElementById('og-type').value,
            twitter_card: document.getElementById('twitter-card').value,
            sitemap_priority: parseFloat(document.getElementById('sitemap-priority').value),
            sitemap_changefreq: document.getElementById('sitemap-changefreq').value
        };

        try {
            const response = await fetch(`/crm/pages/api/${this.pageSlug}/seo/update/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('SEO settings saved successfully!', 'success');
            } else {
                this.showNotification('Failed to save SEO settings: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Failed to save SEO settings:', error);
            this.showNotification('Failed to save SEO settings', 'error');
        }
    }

    async updateSlug() {
        const newSlug = document.getElementById('seo-slug').value;

        try {
            const response = await fetch(`/crm/pages/api/${this.pageSlug}/slug/update/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ new_slug: newSlug })
            });

            const result = await response.json();

            if (result.success) {
                this.pageSlug = result.new_slug;
                document.getElementById('slug-preview').textContent = result.new_url;
                this.showNotification('Slug updated successfully!', 'success');
                
                // Update URL if needed
                window.history.replaceState({}, '', `/crm/pages/builder/${result.new_slug}/`);
            } else {
                this.showNotification('Failed to update slug: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Failed to update slug:', error);
            this.showNotification('Failed to update slug', 'error');
        }
    }

    async analyzePage() {
        const analyzeBtn = document.querySelector('.seo-analyze-btn');
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Analyzing...';

        try {
            const response = await fetch(`/crm/pages/api/${this.pageSlug}/seo/analyze/`);
            const result = await response.json();

            if (result.success) {
                this.analysisData = result.analysis;
                this.displayAnalysis();
            } else {
                this.showNotification('Failed to analyze page: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Failed to analyze page:', error);
            this.showNotification('Failed to analyze page', 'error');
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Page';
        }
    }

    displayAnalysis() {
        if (!this.analysisData) return;

        // Update score circle
        document.querySelector('.score-value').textContent = this.analysisData.score;
        document.querySelector('.score-grade').textContent = this.analysisData.grade;

        // Update score circle color
        const scoreCircle = document.querySelector('.seo-score-circle');
        scoreCircle.className = 'seo-score-circle score-' + this.analysisData.grade.toLowerCase();

        // Display issues, warnings, suggestions
        const resultsContainer = document.getElementById('seo-analysis-results');
        resultsContainer.classList.remove('hidden');

        this.displayList('.seo-issues', 'Issues', this.analysisData.issues, 'error');
        this.displayList('.seo-warnings', 'Warnings', this.analysisData.warnings, 'warning');
        this.displayList('.seo-suggestions', 'Suggestions', this.analysisData.suggestions, 'info');
    }

    displayList(selector, title, items, type) {
        const container = document.querySelector(selector);
        if (!items || items.length === 0) {
            container.innerHTML = '';
            return;
        }

        container.innerHTML = `
            <h4>${title} (${items.length})</h4>
            <ul class="seo-list seo-list-${type}">
                ${items.map(item => `<li>${item}</li>`).join('')}
            </ul>
        `;
    }

    updatePreviews() {
        const title = document.getElementById('seo-title').value || 'Page Title';
        const description = document.getElementById('seo-description').value || 'Page description...';
        const image = document.getElementById('seo-image').value;
        const url = `/p/${this.pageSlug}/`;

        // Google Preview
        document.querySelector('.google-url').textContent = window.location.origin + url;
        document.querySelector('.google-title').textContent = title;
        document.querySelector('.google-description').textContent = description;

        // Facebook Preview
        if (image) {
            document.querySelector('.fb-image').style.backgroundImage = `url(${image})`;
            document.querySelector('.fb-image').style.display = 'block';
        } else {
            document.querySelector('.fb-image').style.display = 'none';
        }
        document.querySelector('.fb-title').textContent = title;
        document.querySelector('.fb-description').textContent = description;
        document.querySelector('.fb-url').textContent = window.location.host;

        // Twitter Preview
        if (image) {
            document.querySelector('.tw-image').style.backgroundImage = `url(${image})`;
            document.querySelector('.tw-image').style.display = 'block';
        } else {
            document.querySelector('.tw-image').style.display = 'none';
        }
        document.querySelector('.tw-title').textContent = title;
        document.querySelector('.tw-description').textContent = description;
        document.querySelector('.tw-url').textContent = window.location.host;
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `seo-notification seo-notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
}

// Initialize SEO Panel when builder loads
document.addEventListener('DOMContentLoaded', () => {
    const pageSlug = window.location.pathname.split('/').filter(p => p).pop();
    if (pageSlug && document.querySelector('.builder-content')) {
        window.seoPanel = new SEOPanel(pageSlug);
    }
});
