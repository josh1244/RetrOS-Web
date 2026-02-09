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

  // Storage helper functions
  const getSettings = (cb) => {
    chrome.storage.local.get('settings', (result) => {
      console.log('Background: read settings', result.settings);
      cb(result.settings || {});
    });
  };

  const setSetting = (key, value, cb) => {
    chrome.storage.local.get('settings', (result) => {
      const settings = result.settings || {};
      settings[key] = value;
      chrome.storage.local.set({ settings }, () => {
        console.log(`Background: set settings.${key} =`, value);
        if (cb) cb(settings);
      });
    });
  };

  const getSite = (domain, cb) => {
    chrome.storage.local.get('sites', (result) => {
      const sites = result.sites || {};
      cb(sites[domain] || {});
    });
  };

  const setSite = (domain, data, cb) => {
    chrome.storage.local.get('sites', (result) => {
      const sites = result.sites || {};
      sites[domain] = Object.assign({}, sites[domain] || {}, data);
      chrome.storage.local.set({ sites }, () => {
        console.log(`Background: set site ${domain}`, data);
        if (cb) cb(sites[domain]);
      });
    });
  };

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
    getSettings((settings) => {
      sendResponse({ success: true, data: settings });
    });
    return true;
  }

  if (message.type === 'SET_SETTING') {
    setSetting(message.key, message.value, (settings) => {
      sendResponse({ success: true, data: settings });
    });
    return true;
  }

  if (message.type === 'APPROVE_STYLE') {
    console.log('Background: Approving style for', message.payload.domain);
    // Store approval in settings
    setSite(message.payload.domain, {
      approvalStatus: 'approved',
      approvedAt: new Date().toISOString()
    }, (site) => {
      sendResponse({ success: true, message: 'Style approved', data: site });
    });
    return true;
  }

  if (message.type === 'REJECT_STYLE') {
    console.log('Background: Rejecting style for', message.payload.domain);
    // Mark for regeneration
    setSite(message.payload.domain, {
      approvalStatus: 'rejected',
      rejectedAt: new Date().toISOString()
    }, (site) => {
      sendResponse({ success: true, message: 'Style rejected', data: site });
    });
    return true;
  }

  if (message.type === 'REGENERATE_STYLE') {
    console.log('Background: Regenerating style for', message.payload.domain);
    console.log('Feedback:', message.payload.feedback);
    
    // TODO: Send to proxy for regeneration
    // For now, just log the feedback
    // mark site as regenerating
    setSite(message.payload.domain, { cacheStatus: 'regenerating' }, (site) => {
      sendResponse({ success: true, message: 'Regeneration requested', data: { feedback: message.payload.feedback, site } });
    });
    return true;
  }

  // Provide current site status (cache/approval)
  if (message.type === 'GET_SITE_STATUS') {
    const domain = message.payload && message.payload.domain;
    if (!domain) {
      sendResponse({ success: false, error: 'Missing domain' });
      return true;
    }

    getSite(domain, (site) => {
      // Provide defaults
      const status = Object.assign({ cacheStatus: 'unknown', approvalStatus: 'unknown' }, site);
      sendResponse({ success: true, data: status });
    });
    return true;
  }
});

console.log('RetrOS-Web background service worker ready');
