/**
 * Content Script
 * 
 * Runs in the context of web pages and handles:
 * - CSS injection for era styling
 * - CSS removal
 * - Communication with background script
 * - Page safety and isolation
 */

console.log('RetrOS-Web content script loaded');

// Store reference to injected style element
let injectedStyleElement = null;

/**
 * Inject CSS into the page
 * @param {string} css - CSS content to inject
 * @param {string} id - Unique identifier for the style element
 * @returns {boolean} - Success status
 */
function injectCSS(css, id = 'retros-web-style') {
  try {
    // Remove existing style if present
    removeCSS(id);

    // Create style element
    const style = document.createElement('style');
    style.id = id;
    style.textContent = css;
    style.type = 'text/css';

    // Inject into head
    document.head.appendChild(style);
    injectedStyleElement = style;

    console.log('CSS injected successfully');
    return true;
  } catch (error) {
    console.error('Error injecting CSS:', error);
    return false;
  }
}

/**
 * Remove injected CSS from the page
 * @param {string} id - Identifier of the style element to remove
 * @returns {boolean} - Success status
 */
function removeCSS(id = 'retros-web-style') {
  try {
    const styleElement = document.getElementById(id);
    if (styleElement) {
      styleElement.remove();
      if (injectedStyleElement === styleElement) {
        injectedStyleElement = null;
      }
      console.log('CSS removed successfully');
      return true;
    }
    return false;
  } catch (error) {
    console.error('Error removing CSS:', error);
    return false;
  }
}

/**
 * Handle messages from background script
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Content script received message:', message.type);

  if (message.type === 'INJECT_CSS') {
    const success = injectCSS(message.css, message.id);
    sendResponse({
      success,
      message: success ? 'CSS injected' : 'Failed to inject CSS'
    });
    return;
  }

  if (message.type === 'REMOVE_CSS') {
    const success = removeCSS(message.id);
    sendResponse({
      success,
      message: success ? 'CSS removed' : 'Failed to remove CSS'
    });
    return;
  }

  if (message.type === 'GET_PAGE_INFO') {
    sendResponse({
      success: true,
      data: {
        url: window.location.href,
        domain: window.location.hostname,
        title: document.title,
        readyState: document.readyState
      }
    });
    return;
  }

  sendResponse({
    success: false,
    error: `Unknown message type: ${message.type}`
  });
});

console.log('RetrOS-Web content script ready');
