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

  // Fallback response
  sendResponse({
    success: false,
    error: `Unknown message type: ${message.type}`
  });
});

console.log('RetrOS-Web background service worker ready');
