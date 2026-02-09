/**
 * Background Service Worker
 * 
 * Coordinates between the extension components:
 * - Manages tab tracking and state
 * - Handles messages from popup and content scripts
 * - Routes commands to content scripts for CSS injection
 * - Manages communication with local proxy
 */

console.log('RetrOS-Web background service worker loaded');

// Track current active tab
let currentTabId = null;

/**
 * Handle tab activation
 */
chrome.tabs.onActivated.addListener((activeInfo) => {
  currentTabId = activeInfo.tabId;
  console.log(`Tab activated: ${currentTabId}`);
});

/**
 * Handle tab removal cleanup
 */
chrome.tabs.onRemoved.addListener((tabId) => {
  if (currentTabId === tabId) {
    currentTabId = null;
  }
  console.log(`Tab removed: ${tabId}`);
});

/**
 * Handle messages from popup and content scripts
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Background received message:', message.type, message);

  if (message.type === 'GET_CURRENT_TAB') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs.length > 0) {
        const tab = tabs[0];
        const url = new URL(tab.url);
        sendResponse({
          success: true,
          data: {
            url: tab.url,
            domain: url.hostname,
            tabId: tab.id
          }
        });
      } else {
        sendResponse({
          success: false,
          error: 'No active tab found'
        });
      }
    });
    return true; // Keep channel open for async response
  }

  if (message.type === 'GET_SETTINGS') {
    chrome.storage.local.get('settings', (result) => {
      sendResponse({
        success: true,
        data: result.settings || {}
      });
    });
    return true;
  }

  if (message.type === 'SET_SETTING') {
    chrome.storage.local.get('settings', (result) => {
      const settings = result.settings || {};
      settings[message.key] = message.value;
      chrome.storage.local.set({ settings }, () => {
        sendResponse({
          success: true,
          data: settings
        });
      });
    });
    return true;
  }

  if (message.type === 'APPROVE_STYLE') {
    console.log('Background: Approving style for', message.payload.domain);
    // Store approval in settings
    chrome.storage.local.get('sites', (result) => {
      const sites = result.sites || {};
      if (!sites[message.payload.domain]) {
        sites[message.payload.domain] = {};
      }
      sites[message.payload.domain].approvalStatus = 'approved';
      sites[message.payload.domain].approvedAt = new Date().toISOString();
      
      chrome.storage.local.set({ sites }, () => {
        sendResponse({
          success: true,
          message: 'Style approved'
        });
      });
    });
    return true;
  }

  if (message.type === 'REJECT_STYLE') {
    console.log('Background: Rejecting style for', message.payload.domain);
    // Mark for regeneration
    chrome.storage.local.get('sites', (result) => {
      const sites = result.sites || {};
      if (!sites[message.payload.domain]) {
        sites[message.payload.domain] = {};
      }
      sites[message.payload.domain].approvalStatus = 'rejected';
      sites[message.payload.domain].rejectedAt = new Date().toISOString();
      
      chrome.storage.local.set({ sites }, () => {
        sendResponse({
          success: true,
          message: 'Style rejected'
        });
      });
    });
    return true;
  }

  if (message.type === 'REGENERATE_STYLE') {
    console.log('Background: Regenerating style for', message.payload.domain);
    console.log('Feedback:', message.payload.feedback);
    
    // TODO: Send to proxy for regeneration
    // For now, just log the feedback
    sendResponse({
      success: true,
      message: 'Regeneration requested',
      data: {
        feedback: message.payload.feedback
      }
    });
    return true;
  }
});

console.log('RetrOS-Web background service worker ready');
