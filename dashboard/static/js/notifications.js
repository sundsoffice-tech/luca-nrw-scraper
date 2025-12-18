/**
 * Browser Notifications
 * Handles desktop notifications for important events
 */

let notificationsEnabled = false;

/**
 * Request notification permission
 */
async function requestNotificationPermission() {
    if (!('Notification' in window)) {
        console.log('This browser does not support notifications');
        return false;
    }
    
    if (Notification.permission === 'granted') {
        notificationsEnabled = true;
        return true;
    }
    
    if (Notification.permission !== 'denied') {
        const permission = await Notification.requestPermission();
        notificationsEnabled = permission === 'granted';
        return notificationsEnabled;
    }
    
    return false;
}

/**
 * Show desktop notification
 */
function showDesktopNotification(title, body, icon = '/static/img/logo.png') {
    if (!notificationsEnabled) {
        return;
    }
    
    try {
        const notification = new Notification(title, {
            body: body,
            icon: icon,
            badge: icon,
            tag: 'luca-notification',
            requireInteraction: false
        });
        
        notification.onclick = () => {
            window.focus();
            notification.close();
        };
        
        // Auto-close after 5 seconds
        setTimeout(() => {
            notification.close();
        }, 5000);
        
    } catch (error) {
        console.error('Error showing notification:', error);
    }
}

/**
 * Notify on new lead
 */
function notifyNewLead(leadData) {
    if (!notificationsEnabled) return;
    
    let body = leadData.name || 'Neuer Lead';
    if (leadData.company) {
        body += ` - ${leadData.company}`;
    }
    if (leadData.telefon) {
        body += `\n📱 ${leadData.telefon}`;
    }
    
    showDesktopNotification('🎯 Neuer Lead!', body);
}

/**
 * Notify on scraper event
 */
function notifyScraperEvent(event, message) {
    if (!notificationsEnabled) return;
    
    let title = '🎯 LUCA Scraper';
    let icon = '/static/img/logo.png';
    
    switch (event) {
        case 'started':
            title = '▶️ Scraper gestartet';
            break;
        case 'stopped':
            title = '⏹️ Scraper gestoppt';
            break;
        case 'error':
            title = '❌ Scraper Fehler';
            break;
        case 'completed':
            title = '✅ Scraper abgeschlossen';
            break;
    }
    
    showDesktopNotification(title, message, icon);
}

/**
 * Check if notifications are supported and setup button
 */
function setupNotificationButton() {
    const button = document.getElementById('enable-notifications-btn');
    if (!button) return;
    
    if (!('Notification' in window)) {
        button.style.display = 'none';
        return;
    }
    
    if (Notification.permission === 'granted') {
        notificationsEnabled = true;
        button.textContent = '🔔 Benachrichtigungen aktiv';
        button.disabled = true;
        button.classList.add('bg-green-600');
        button.classList.remove('bg-blue-600', 'hover:bg-blue-700');
    } else {
        button.addEventListener('click', async () => {
            const granted = await requestNotificationPermission();
            if (granted) {
                button.textContent = '🔔 Benachrichtigungen aktiv';
                button.disabled = true;
                button.classList.add('bg-green-600');
                button.classList.remove('bg-blue-600', 'hover:bg-blue-700');
                showDesktopNotification('✅ Benachrichtigungen aktiviert', 'Sie erhalten jetzt Desktop-Benachrichtigungen für wichtige Events');
            } else {
                alert('Benachrichtigungen wurden abgelehnt oder werden nicht unterstützt');
            }
        });
    }
}

// Auto-setup on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupNotificationButton);
} else {
    setupNotificationButton();
}

// Check if already granted
if ('Notification' in window && Notification.permission === 'granted') {
    notificationsEnabled = true;
}
