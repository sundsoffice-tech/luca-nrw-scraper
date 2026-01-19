/**
 * Flow Builder JavaScript
 * Handles interactive flow creation and editing
 */

let currentFlow = null;
let currentSteps = [];
let availableTemplates = [];
let currentEditingStep = null;

// Action type icons
const ACTION_ICONS = {
    'send_email': '📧',
    'wait': '⏱️',
    'condition': '🔀',
    'update_lead': '✏️',
    'add_tag': '🏷️',
    'remove_tag': '🏷️',
    'webhook': '🌐',
    'notify_team': '🔔',
    'update_score': '⭐'
};

/**
 * Initialize flow builder
 */
function initFlowBuilder(flowData, templates) {
    currentFlow = flowData;
    currentSteps = flowData.steps || [];
    availableTemplates = templates;
    
    // Setup toggle switch
    const toggle = document.getElementById('flow-active');
    if (toggle) {
        toggle.addEventListener('change', function() {
            const toggleBg = this.nextElementSibling;
            const toggleDot = toggleBg.querySelector('.toggle-dot');
            if (this.checked) {
                toggleBg.classList.remove('bg-dark-700');
                toggleBg.classList.add('bg-primary');
                toggleDot.classList.remove('bg-gray-400', 'left-1');
                toggleDot.classList.add('bg-white', 'left-7');
            } else {
                toggleBg.classList.remove('bg-primary');
                toggleBg.classList.add('bg-dark-700');
                toggleDot.classList.remove('bg-white', 'left-7');
                toggleDot.classList.add('bg-gray-400', 'left-1');
            }
        });
        
        // Trigger initial state
        if (toggle.checked) {
            toggle.dispatchEvent(new Event('change'));
        }
    }
    
    // Setup trigger type change handler
    const triggerType = document.getElementById('trigger-type');
    if (triggerType) {
        triggerType.addEventListener('change', updateTriggerConfig);
        updateTriggerConfig();
    }
    
    // Render existing steps
    renderSteps();
}

/**
 * Update trigger configuration UI based on selected trigger type
 */
function updateTriggerConfig() {
    const triggerType = document.getElementById('trigger-type').value;
    const configDiv = document.getElementById('trigger-config');
    
    let html = '';
    
    switch(triggerType) {
        case 'lead_status_changed':
            html = `
                <div>
                    <label class="text-sm text-gray-400 mb-2 block">Von Status</label>
                    <select id="trigger-from-status" class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                        <option value="">Beliebig</option>
                        <option value="NEW">Neu</option>
                        <option value="CONTACTED">Kontaktiert</option>
                        <option value="INTERESTED">Interessiert</option>
                    </select>
                </div>
                <div>
                    <label class="text-sm text-gray-400 mb-2 block">Zu Status</label>
                    <select id="trigger-to-status" class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                        <option value="CONTACTED">Kontaktiert</option>
                        <option value="INTERESTED">Interessiert</option>
                        <option value="INTERVIEW">Interview</option>
                    </select>
                </div>
            `;
            break;
        case 'lead_score_reached':
            html = `
                <div>
                    <label class="text-sm text-gray-400 mb-2 block">Mindest-Score</label>
                    <input type="number" id="trigger-score" min="0" max="100" value="70"
                           class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                </div>
            `;
            break;
        case 'tag_added':
            html = `
                <div>
                    <label class="text-sm text-gray-400 mb-2 block">Tag-Name</label>
                    <input type="text" id="trigger-tag" placeholder="z.B. Interessiert"
                           class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                </div>
            `;
            break;
        case 'time_based':
            html = `
                <div>
                    <label class="text-sm text-gray-400 mb-2 block">Zeitplan</label>
                    <input type="text" id="trigger-cron" placeholder="0 9 * * *"
                           class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                    <p class="text-xs text-gray-500 mt-1">Cron-Expression (täglich 9:00 Uhr)</p>
                </div>
            `;
            break;
        default:
            html = '<p class="text-sm text-gray-500">Keine zusätzliche Konfiguration erforderlich</p>';
    }
    
    configDiv.innerHTML = html;
}

/**
 * Render all steps
 */
function renderSteps() {
    const container = document.getElementById('steps-container');
    const emptyState = document.getElementById('steps-empty');
    
    if (currentSteps.length === 0) {
        emptyState.classList.remove('hidden');
        return;
    }
    
    emptyState.classList.add('hidden');
    
    // Clear existing steps (except empty state)
    const existingSteps = container.querySelectorAll('.step-card');
    existingSteps.forEach(step => step.remove());
    
    // Sort steps by order
    currentSteps.sort((a, b) => a.order - b.order);
    
    // Render each step
    currentSteps.forEach((step, index) => {
        const stepEl = createStepElement(step, index);
        container.insertBefore(stepEl, emptyState);
    });
}

/**
 * Create step element
 */
function createStepElement(step, index) {
    const div = document.createElement('div');
    div.className = 'step-card bg-dark-700 rounded-lg p-4 border border-dark-600';
    div.dataset.order = index;
    
    const icon = ACTION_ICONS[step.action_type] || '📋';
    
    let configSummary = 'Konfiguriert';
    if (step.action_type === 'send_email' && step.email_template) {
        const template = availableTemplates.find(t => t.id === step.email_template);
        configSummary = `Template: ${template ? template.name : 'Unbekannt'}`;
    } else if (step.action_type === 'wait' && step.action_config.duration) {
        configSummary = `Wartezeit: ${step.action_config.duration}`;
    }
    
    div.innerHTML = `
        <div class="flex items-start space-x-4">
            <div class="action-icon bg-primary/20 text-primary shrink-0">
                <span>${icon}</span>
            </div>
            <div class="flex-1 min-w-0">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <h4 class="font-semibold text-gray-200">${getActionTypeDisplay(step.action_type)}</h4>
                        ${step.name ? `<p class="text-sm text-gray-400">${step.name}</p>` : ''}
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="editStep(${index})" class="text-gray-400 hover:text-primary transition duration-150 p-1">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                            </svg>
                        </button>
                        <button onclick="deleteStep(${index})" class="text-gray-400 hover:text-red-400 transition duration-150 p-1">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="text-sm text-gray-500">
                    ${configSummary}
                </div>
            </div>
        </div>
    `;
    
    return div;
}

/**
 * Get action type display name
 */
function getActionTypeDisplay(actionType) {
    const displays = {
        'send_email': 'Email senden',
        'wait': 'Warten',
        'condition': 'Bedingung prüfen',
        'update_lead': 'Lead aktualisieren',
        'add_tag': 'Tag hinzufügen',
        'remove_tag': 'Tag entfernen',
        'webhook': 'Webhook aufrufen',
        'notify_team': 'Team benachrichtigen',
        'update_score': 'Score anpassen'
    };
    return displays[actionType] || actionType;
}

/**
 * Add new step
 */
function addStep() {
    currentEditingStep = null;
    document.getElementById('modal-step-order').value = currentSteps.length;
    document.getElementById('modal-action-type').value = 'send_email';
    document.getElementById('modal-step-name').value = '';
    
    updateStepConfig();
    openStepModal();
}

/**
 * Edit existing step
 */
function editStep(index) {
    const step = currentSteps[index];
    currentEditingStep = index;
    
    document.getElementById('modal-step-order').value = index;
    document.getElementById('modal-action-type').value = step.action_type;
    document.getElementById('modal-step-name').value = step.name || '';
    
    updateStepConfig();
    
    // Populate config fields
    if (step.action_type === 'send_email' && step.email_template) {
        const templateSelect = document.getElementById('config-email-template');
        if (templateSelect) templateSelect.value = step.email_template;
    } else if (step.action_type === 'wait' && step.action_config.duration) {
        const durationInput = document.getElementById('config-wait-duration');
        if (durationInput) durationInput.value = step.action_config.duration;
    }
    
    openStepModal();
}

/**
 * Delete step
 */
function deleteStep(index) {
    if (confirm('Schritt wirklich löschen?')) {
        currentSteps.splice(index, 1);
        // Reorder remaining steps
        currentSteps.forEach((step, i) => {
            step.order = i;
        });
        renderSteps();
    }
}

/**
 * Update step configuration UI
 */
function updateStepConfig() {
    const actionType = document.getElementById('modal-action-type').value;
    const configDiv = document.getElementById('modal-step-config');
    
    let html = '';
    
    switch(actionType) {
        case 'send_email':
            html = `
                <div>
                    <label class="text-sm text-gray-400 mb-2 block">Email-Template</label>
                    <select id="config-email-template" class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                        <option value="">Template wählen...</option>
                        ${availableTemplates.map(t => `<option value="${t.id}">${t.name}</option>`).join('')}
                    </select>
                </div>
            `;
            break;
        case 'wait':
            html = `
                <div>
                    <label class="text-sm text-gray-400 mb-2 block">Wartezeit</label>
                    <input type="text" id="config-wait-duration" placeholder="z.B. 1 Tag, 2 Stunden"
                           class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                    <p class="text-xs text-gray-500 mt-1">Format: "X Tage", "X Stunden", "X Minuten"</p>
                </div>
            `;
            break;
        case 'condition':
            html = `
                <div class="space-y-3">
                    <div>
                        <label class="text-sm text-gray-400 mb-2 block">Feld</label>
                        <select id="config-condition-field" class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                            <option value="status">Status</option>
                            <option value="quality_score">Quality Score</option>
                            <option value="interest_level">Interest Level</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-sm text-gray-400 mb-2 block">Operator</label>
                        <select id="config-condition-operator" class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                            <option value="equals">Ist gleich</option>
                            <option value="not_equals">Ist nicht gleich</option>
                            <option value="greater_than">Größer als</option>
                            <option value="less_than">Kleiner als</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-sm text-gray-400 mb-2 block">Wert</label>
                        <input type="text" id="config-condition-value"
                               class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                    </div>
                </div>
            `;
            break;
        case 'update_lead':
            html = `
                <div class="space-y-3">
                    <div>
                        <label class="text-sm text-gray-400 mb-2 block">Feld</label>
                        <select id="config-update-field" class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                            <option value="status">Status</option>
                            <option value="quality_score">Quality Score</option>
                            <option value="interest_level">Interest Level</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-sm text-gray-400 mb-2 block">Neuer Wert</label>
                        <input type="text" id="config-update-value"
                               class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                    </div>
                </div>
            `;
            break;
        case 'add_tag':
        case 'remove_tag':
            html = `
                <div>
                    <label class="text-sm text-gray-400 mb-2 block">Tag-Name</label>
                    <input type="text" id="config-tag-name" placeholder="z.B. Interessiert"
                           class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                </div>
            `;
            break;
        case 'webhook':
            html = `
                <div class="space-y-3">
                    <div>
                        <label class="text-sm text-gray-400 mb-2 block">URL</label>
                        <input type="url" id="config-webhook-url" placeholder="https://..."
                               class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                    </div>
                    <div>
                        <label class="text-sm text-gray-400 mb-2 block">Method</label>
                        <select id="config-webhook-method" class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                            <option value="POST">POST</option>
                            <option value="GET">GET</option>
                            <option value="PUT">PUT</option>
                        </select>
                    </div>
                </div>
            `;
            break;
        case 'notify_team':
            html = `
                <div>
                    <label class="text-sm text-gray-400 mb-2 block">Nachricht</label>
                    <textarea id="config-notify-message" rows="3"
                              class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                              placeholder="Team-Benachrichtigung..."></textarea>
                </div>
            `;
            break;
        case 'update_score':
            html = `
                <div>
                    <label class="text-sm text-gray-400 mb-2 block">Score-Änderung</label>
                    <input type="number" id="config-score-change" placeholder="+10 oder -5"
                           class="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary">
                    <p class="text-xs text-gray-500 mt-1">Positive oder negative Zahl</p>
                </div>
            `;
            break;
    }
    
    configDiv.innerHTML = html;
}

/**
 * Save step
 */
function saveStep() {
    const order = parseInt(document.getElementById('modal-step-order').value);
    const actionType = document.getElementById('modal-action-type').value;
    const name = document.getElementById('modal-step-name').value;
    
    // Build action_config based on action type
    let actionConfig = {};
    let emailTemplate = null;
    
    switch(actionType) {
        case 'send_email':
            emailTemplate = parseInt(document.getElementById('config-email-template').value) || null;
            break;
        case 'wait':
            actionConfig.duration = document.getElementById('config-wait-duration').value;
            break;
        case 'condition':
            actionConfig = {
                field: document.getElementById('config-condition-field').value,
                operator: document.getElementById('config-condition-operator').value,
                value: document.getElementById('config-condition-value').value
            };
            break;
        case 'update_lead':
            actionConfig = {
                field: document.getElementById('config-update-field').value,
                value: document.getElementById('config-update-value').value
            };
            break;
        case 'add_tag':
        case 'remove_tag':
            actionConfig.tag = document.getElementById('config-tag-name').value;
            break;
        case 'webhook':
            actionConfig = {
                url: document.getElementById('config-webhook-url').value,
                method: document.getElementById('config-webhook-method').value
            };
            break;
        case 'notify_team':
            actionConfig.message = document.getElementById('config-notify-message').value;
            break;
        case 'update_score':
            actionConfig.change = parseInt(document.getElementById('config-score-change').value);
            break;
    }
    
    const step = {
        order: order,
        name: name,
        action_type: actionType,
        action_config: actionConfig,
        email_template: emailTemplate,
        is_active: true
    };
    
    if (currentEditingStep !== null) {
        // Update existing step
        currentSteps[currentEditingStep] = step;
    } else {
        // Add new step
        currentSteps.push(step);
    }
    
    renderSteps();
    closeStepModal();
}

/**
 * Open step modal
 */
function openStepModal() {
    document.getElementById('step-modal').classList.remove('hidden');
}

/**
 * Close step modal
 */
function closeStepModal() {
    document.getElementById('step-modal').classList.add('hidden');
    currentEditingStep = null;
}

/**
 * Save flow
 */
async function saveFlow() {
    const name = document.getElementById('flow-name').value.trim();
    const description = document.getElementById('flow-description').value.trim();
    const isActive = document.getElementById('flow-active').checked;
    const triggerType = document.getElementById('trigger-type').value;
    
    if (!name) {
        alert('Bitte gib einen Flow-Namen ein');
        return;
    }
    
    // Build trigger_config
    let triggerConfig = {};
    switch(triggerType) {
        case 'lead_status_changed':
            triggerConfig = {
                from_status: document.getElementById('trigger-from-status')?.value || '',
                to_status: document.getElementById('trigger-to-status')?.value || ''
            };
            break;
        case 'lead_score_reached':
            triggerConfig.score = parseInt(document.getElementById('trigger-score')?.value) || 70;
            break;
        case 'tag_added':
            triggerConfig.tag = document.getElementById('trigger-tag')?.value || '';
            break;
        case 'time_based':
            triggerConfig.cron = document.getElementById('trigger-cron')?.value || '';
            break;
    }
    
    // Build flow data
    const flowData = {
        name: name,
        slug: currentFlow.slug || name.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
        description: description,
        trigger_type: triggerType,
        trigger_config: triggerConfig,
        is_active: isActive,
        steps: currentSteps
    };
    
    try {
        const url = currentFlow.slug 
            ? `/api/email-templates/flows/${currentFlow.slug}/`
            : '/api/email-templates/flows/';
        
        const method = currentFlow.slug ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(flowData)
        });
        
        if (response.ok) {
            const result = await response.json();
            alert('Flow erfolgreich gespeichert!');
            window.location.href = `/crm/email-templates/flows/${result.slug}/`;
        } else {
            const error = await response.json();
            alert('Fehler beim Speichern: ' + JSON.stringify(error));
        }
    } catch (error) {
        console.error('Error saving flow:', error);
        alert('Fehler beim Speichern: ' + error.message);
    }
}

/**
 * Get CSRF token
 */
function getCsrfToken() {
    const name = 'csrftoken';
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
