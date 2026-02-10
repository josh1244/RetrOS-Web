/**
 * Background Service Worker
 * 
 * Coordinates between the extension components:
 * - Manages tab tracking and state
 * - Handles messages from popup and content scripts
 * - Routes commands to content scripts for CSS injection
 * - Manages communication with local proxy
 */

// Import proxy communication module
// Note: In Firefox extension context, this loads via script tags in manifest
// We access it as a global after the background script loads

console.log('RetrOS-Web background service worker loaded');

// Track current active tab
let currentTabId = null;

const APPROVAL_STATES = Object.freeze({
  pending: 'pending',
  approved: 'approved',
  rejected: 'rejected',
  processing: 'processing'
});

const APPROVAL_TRANSITIONS = Object.freeze({
  [APPROVAL_STATES.pending]: [APPROVAL_STATES.approved, APPROVAL_STATES.rejected, APPROVAL_STATES.processing],
  [APPROVAL_STATES.rejected]: [APPROVAL_STATES.processing, APPROVAL_STATES.pending],
  [APPROVAL_STATES.processing]: [APPROVAL_STATES.pending, APPROVAL_STATES.rejected],
  [APPROVAL_STATES.approved]: []
});

const normalizeApprovalState = (state) => {
  if (!state) return APPROVAL_STATES.pending;
  if (Object.values(APPROVAL_STATES).includes(state)) return state;
  if (state === 'unknown') return APPROVAL_STATES.pending;
  return APPROVAL_STATES.pending;
};

const canTransitionApproval = (fromState, toState) => {
  const from = normalizeApprovalState(fromState);
  if (from === toState) return false;
  const allowed = APPROVAL_TRANSITIONS[from] || [];
  return allowed.includes(toState);
};

// Lightweight logger helper
const log = (level, ...args) => {
  if (level === 'error') console.error('[BG]', ...args);
  else if (level === 'warn') console.warn('[BG]', ...args);
  else console.log('[BG]', ...args);
};

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
  log('info', `Tab removed: ${tabId}`);
});

const normalizeStoredStates = () => {
  chrome.storage.local.get('sites', (result) => {
    const sites = result.sites || {};
    let mutated = false;
    Object.keys(sites).forEach((domain) => {
      const state = normalizeApprovalState(sites[domain].approvalStatus);
      if (sites[domain].approvalStatus !== state) {
        sites[domain].approvalStatus = state;
        mutated = true;
      }
    });
    if (mutated) {
      chrome.storage.local.set({ sites }, () => {
        log('info', 'Normalized approval states on startup');
      });
    }
  });
};

chrome.runtime.onStartup.addListener(() => {
  normalizeStoredStates();
});

chrome.runtime.onInstalled.addListener(() => {
  normalizeStoredStates();
});

/**
 * Send a message to a specific tab's content script, resolving the response.
 * Falls back to querying the active tab if tabId is not provided.
 */
function sendMessageToTab(tabId, message) {
  return new Promise((resolve, reject) => {
    const doSend = (id) => {
      chrome.tabs.sendMessage(id, message, (response) => {
        if (chrome.runtime.lastError) {
          log('warn', 'sendMessageToTab lastError', chrome.runtime.lastError.message);
          return reject(chrome.runtime.lastError);
        }
        resolve(response || {});
      });
    };

    if (tabId) return doSend(tabId);

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs && tabs.length) return doSend(tabs[0].id);
      reject(new Error('No active tab to send message to'));
    });
  });
}

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

  const transitionApprovalState = (domain, nextState, cb) => {
    getSite(domain, (site) => {
      const currentState = normalizeApprovalState(site.approvalStatus);
      if (!canTransitionApproval(currentState, nextState)) {
        log('warn', `Invalid approval transition ${currentState} -> ${nextState} for ${domain}`);
        if (cb) cb({
          success: false,
          error: `Invalid approval transition ${currentState} -> ${nextState}`,
          data: site
        });
        return;
      }
      const update = {
        approvalStatus: nextState,
        approvalUpdatedAt: new Date().toISOString()
      };
      setSite(domain, update, (updated) => {
        log('info', `Approval transition ${currentState} -> ${nextState} for ${domain}`);
        if (cb) cb({ success: true, data: updated });
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
    transitionApprovalState(message.payload.domain, APPROVAL_STATES.approved, (result) => {
      if (!result.success) {
        sendResponse({ success: false, error: result.error, data: result.data });
        return;
      }
      setSite(message.payload.domain, { approvedAt: new Date().toISOString() }, (site) => {
        sendResponse({ success: true, message: 'Style approved', data: site });
      });
    });
    return true;
  }

  if (message.type === 'REJECT_STYLE') {
    console.log('Background: Rejecting style for', message.payload.domain);
    transitionApprovalState(message.payload.domain, APPROVAL_STATES.rejected, (result) => {
      if (!result.success) {
        sendResponse({ success: false, error: result.error, data: result.data });
        return;
      }
      setSite(message.payload.domain, { rejectedAt: new Date().toISOString() }, (site) => {
        sendResponse({ success: true, message: 'Style rejected', data: site });
      });
    });
    return true;
  }

  if (message.type === 'REGENERATE_STYLE') {
    console.log('Background: Regenerating style for', message.payload.domain);
    console.log('Feedback:', message.payload.feedback);
    
    // Mark site as regenerating and send to proxy if available
    transitionApprovalState(message.payload.domain, APPROVAL_STATES.processing, (transitionResult) => {
      if (!transitionResult.success) {
        sendResponse({ success: false, error: transitionResult.error, data: transitionResult.data });
        return;
      }

      setSite(message.payload.domain, { cacheStatus: 'regenerating' }, (site) => {
      // Attempt to send to proxy asynchronously
      if (typeof generateStyle !== 'undefined') {
        const request = {
          domain: message.payload.domain,
          era: message.payload.era || 'Windows 95',
          domDigest: message.payload.domDigest || 'unknown',
          feedback: message.payload.feedback
        };
        
        generateStyle(request)
          .then((response) => {
            if (response.success) {
              console.log('[BG] Style generated successfully from proxy');
              // Apply the generated CSS
              sendMessageToTab(currentTabId, { 
                type: 'APPLY_STYLE', 
                payload: { css: response.css, domain: message.payload.domain } 
              }).catch(err => console.error('[BG] Failed to apply proxy-generated CSS:', err));
            } else {
              console.error('[BG] Proxy generation failed:', response.error);
            }
          })
          .catch(err => console.error('[BG] Error calling generateStyle:', err));
      }
      
      sendResponse({ success: true, message: 'Regeneration requested', data: { feedback: message.payload.feedback, site } });
      });
    });
    return true;
  }

  // Generate style via proxy (new message type for explicit generation requests)
  if (message.type === 'GENERATE_STYLE') {
    const domain = message.payload && message.payload.domain;
    const era = message.payload && message.payload.era;
    const domDigest = message.payload && message.payload.domDigest;

    if (!domain || !era || !domDigest) {
      sendResponse({ 
        success: false, 
        error: 'Missing required fields: domain, era, domDigest' 
      });
      return true;
    }

    if (typeof generateStyle === 'undefined') {
      sendResponse({
        success: false,
        error: 'Proxy client module not loaded'
      });
      return true;
    }

    // Mark as processing
    transitionApprovalState(domain, APPROVAL_STATES.processing, (transitionResult) => {
      if (!transitionResult.success) {
        sendResponse({ success: false, error: transitionResult.error, data: transitionResult.data });
        return;
      }

      setSite(domain, { cacheStatus: 'processing' }, () => {
      const request = {
        domain,
        era,
        domDigest,
        feedback: message.payload.feedback
      };

      generateStyle(request)
        .then((response) => {
          if (response.success) {
            log('info', `Generated CSS for ${domain} (${response.css.length} bytes)`);
            sendResponse(response);
          } else {
            log('warn', `Proxy generation failed for ${domain}:`, response.error);
            sendResponse(response);
          }
        })
        .catch((error) => {
          log('error', 'Unexpected error during generation:', error);
          sendResponse({
            success: false,
            error: error.message || 'Unknown error during generation',
            errorCode: 'GENERATION_ERROR'
          });
        });
      });
    });

    return true; // Keep channel open for async response
  }

  // Apply CSS to page via content script
  if (message.type === 'APPLY_STYLE') {
    const domain = message.payload && message.payload.domain;
    const css = message.payload && message.payload.css;
    if (!css) {
      sendResponse({ success: false, error: 'Missing css in payload' });
      return true;
    }

    // Send to tab (use provided tabId or active tab)
    const tabId = (message.payload && message.payload.tabId) || currentTabId;
    sendMessageToTab(tabId, { type: 'APPLY_STYLE', payload: { css } })
      .then((resp) => {
        log('info', 'APPLY_STYLE delivered', resp);
        // mark site cache as applied
        if (domain) {
          setSite(domain, { cacheStatus: 'applied' }, () => {});
          transitionApprovalState(domain, APPROVAL_STATES.pending, () => {});
        }
        sendResponse({ success: true, message: 'Style applied', data: resp });
      })
      .catch((err) => {
        log('warn', 'Failed to apply style to tab', err);
        sendResponse({ success: false, error: err.message || String(err) });
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
      const normalizedState = normalizeApprovalState(site.approvalStatus);
      if (site.approvalStatus !== normalizedState) {
        site.approvalStatus = normalizedState;
        setSite(domain, { approvalStatus: normalizedState }, () => {});
      }
      // Provide defaults
      const status = Object.assign({ cacheStatus: 'unknown', approvalStatus: APPROVAL_STATES.pending }, site);
      sendResponse({ success: true, data: status });
    });
    return true;
  }
});

console.log('RetrOS-Web background service worker ready');
