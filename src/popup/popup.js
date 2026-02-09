/**
 * Popup Script
 * 
 * Handles the extension popup UI:
 * - Display current site and era
 * - Show status information
 * - Route to settings
 * - Manage approval workflow (US-1.2+)
 */

console.log('RetrOS-Web popup script loaded');

/**
 * Initialize popup on load
 */
document.addEventListener('DOMContentLoaded', () => {
  console.log('Popup DOM loaded');
  initializePopup();
});

/**
 * Initialize all popup functionality
 */
async function initializePopup() {
  try {
    // Get current tab info
    const currentTab = await sendMessage({ type: 'GET_CURRENT_TAB' });
    
    if (currentTab.success) {
      const domain = currentTab.data.domain;
      document.getElementById('current-domain').textContent = domain;
      console.log(`Current domain: ${domain}`);
    } else {
      document.getElementById('current-domain').textContent = 'Unknown';
    }

    // Get current era
    const settings = await sendMessage({ type: 'GET_SETTINGS' });
    if (settings.success) {
      const era = settings.data.selectedEra || 'Not selected';
      document.getElementById('current-era').textContent = era;
      console.log(`Current era: ${era}`);
    } else {
      document.getElementById('current-era').textContent = 'Error loading';
    }

  } catch (error) {
    console.error('Error initializing popup:', error);
    document.getElementById('current-domain').textContent = 'Error';
    document.getElementById('current-era').textContent = 'Error';
  }

  // Setup event listeners
  setupEventListeners();
}

/**
 * Setup event listeners for popup UI
 */
function setupEventListeners() {
  // Settings button
  const settingsBtn = document.getElementById('settings-btn');
  if (settingsBtn) {
    settingsBtn.addEventListener('click', () => {
      console.log('Settings clicked');
      // TODO: Open settings (will be implemented in US-1.3)
    });
  }

  // Keyboard accessibility
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      // Close popup
      window.close();
    }
  });
}

/**
 * Send message to background script
 * @param {object} message - Message to send
 * @returns {Promise} - Response from background script
 */
function sendMessage(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, (response) => {
      if (chrome.runtime.lastError) {
        console.error('Message error:', chrome.runtime.lastError);
        reject(chrome.runtime.lastError);
      } else {
        resolve(response || {});
      }
    });
  });
}

console.log('RetrOS-Web popup script ready');
