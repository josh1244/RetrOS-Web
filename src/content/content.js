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

    // Prefer head, but fallback if not available yet (document_start)
    const container = document.head || document.documentElement || document.body;
    if (!container) {
      // As a last resort, queue insertion on DOMContentLoaded
      document.addEventListener('DOMContentLoaded', () => {
        try {
          document.head.appendChild(style);
          injectedStyleElement = style;
          console.log('CSS injected after DOMContentLoaded');
        } catch (err) {
          console.error('Failed to inject CSS after DOMContentLoaded', err);
        }
      }, { once: true });
    } else {
      container.appendChild(style);
      injectedStyleElement = style;
      console.log('CSS injected successfully');
    }

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

  if (message.type === 'APPLY_STYLE') {
    // Backwards/alternate channel name used by background
    const css = message.payload && message.payload.css;
    const id = (message.payload && message.payload.id) || 'retros-web-style';
    const success = injectCSS(css, id);
    sendResponse({ success, message: success ? 'Style applied' : 'Failed to apply style' });
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

/* ---------------------- Approval banner (US-3.1) ---------------------- */

const ERA_THEMES = {
  '90s': {
    bg: '#f5efe1',
    panel: '#fff8e6',
    border: '#2f4f4f',
    accent: '#ff0066',
    text: '#1a1a1a',
    font: 'Verdana, Tahoma, Arial, sans-serif'
  },
  'windows95': {
    bg: '#c0c0c0',
    panel: '#e6e6e6',
    border: '#000000',
    accent: '#000080',
    text: '#000000',
    font: 'Tahoma, "MS Sans Serif", Arial, sans-serif'
  },
  'windows98': {
    bg: '#c0c0c0',
    panel: '#f3f3f3',
    border: '#000000',
    accent: '#0066cc',
    text: '#000000',
    font: 'Tahoma, "MS Sans Serif", Arial, sans-serif'
  },
  'windowsxp': {
    bg: '#e7f0ff',
    panel: '#ffffff',
    border: '#3a6ea5',
    accent: '#3a6ea5',
    text: '#1b1b1b',
    font: 'Tahoma, "Trebuchet MS", Arial, sans-serif'
  }
};

let approvalBannerHost = null;
let approvalBannerVisible = false;

function normalizeEra(era) {
  if (!era || typeof era !== 'string') return 'windows95';
  const cleaned = era.toLowerCase().replace(/\s+/g, '').replace(/-/g, '');
  if (cleaned.includes('90')) return '90s';
  if (cleaned.includes('win95') || cleaned.includes('windows95')) return 'windows95';
  if (cleaned.includes('win98') || cleaned.includes('windows98')) return 'windows98';
  if (cleaned.includes('winxp') || cleaned.includes('windowsxp')) return 'windowsxp';
  return 'windows95';
}

function getEraTheme(era) {
  const key = normalizeEra(era);
  return ERA_THEMES[key] || ERA_THEMES.windows95;
}

function sendRuntimeMessage(message) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(message, (response) => {
      resolve(response || {});
    });
  });
}

function getPreviewColors() {
  const bodyStyle = window.getComputedStyle(document.body);
  const rootStyle = window.getComputedStyle(document.documentElement);
  const bg = bodyStyle.backgroundColor !== 'rgba(0, 0, 0, 0)'
    ? bodyStyle.backgroundColor
    : rootStyle.backgroundColor || '#ffffff';
  const text = bodyStyle.color || '#000000';
  return { bg, text };
}

function shouldShowBanner(status) {
  if (status && status.approvalStatus === 'approved') return false;
  const hasStyle = Boolean(document.getElementById('retros-web-style'));
  const cacheStatus = status && status.cacheStatus;
  return hasStyle || (cacheStatus && cacheStatus !== 'unknown');
}

function createApprovalBanner(era) {
  if (approvalBannerVisible || approvalBannerHost) return;

  const theme = getEraTheme(era);
  const previewColors = getPreviewColors();

  approvalBannerHost = document.createElement('div');
  approvalBannerHost.id = 'retros-approval-banner';
  approvalBannerHost.style.position = 'fixed';
  approvalBannerHost.style.top = '0';
  approvalBannerHost.style.left = '0';
  approvalBannerHost.style.right = '0';
  approvalBannerHost.style.zIndex = '2147483647';

  const shadow = approvalBannerHost.attachShadow({ mode: 'open' });
  const style = document.createElement('style');
  style.textContent = `
    :host {
      --retro-bg: ${theme.bg};
      --retro-panel: ${theme.panel};
      --retro-border: ${theme.border};
      --retro-accent: ${theme.accent};
      --retro-text: ${theme.text};
      --retro-font: ${theme.font};
      --preview-bg: ${previewColors.bg};
      --preview-text: ${previewColors.text};
    }
    .banner {
      width: 100%;
      box-sizing: border-box;
      border-bottom: 2px solid var(--retro-border);
      background: var(--retro-bg);
      color: var(--retro-text);
      font-family: var(--retro-font);
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    }
    .banner-inner {
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 16px;
      align-items: center;
      padding: 12px 16px;
      max-width: 1200px;
      margin: 0 auto;
    }
    .preview {
      width: 96px;
      height: 64px;
      border: 2px solid var(--retro-border);
      background: var(--retro-panel);
      box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.6);
      border-radius: 4px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .preview-bar {
      height: 14px;
      background: var(--retro-accent);
    }
    .preview-body {
      flex: 1;
      background: var(--preview-bg);
      padding: 6px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .preview-line {
      height: 4px;
      background: var(--preview-text);
      opacity: 0.7;
      border-radius: 2px;
    }
    .preview-line.short {
      width: 60%;
    }
    .content {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .title {
      font-weight: 700;
      font-size: 15px;
    }
    .subtitle {
      font-size: 12px;
      opacity: 0.8;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .btn {
      font-family: var(--retro-font);
      font-size: 12px;
      padding: 6px 12px;
      border: 2px solid var(--retro-border);
      background: var(--retro-panel);
      color: var(--retro-text);
      cursor: pointer;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.7);
    }
    .btn.primary {
      background: var(--retro-accent);
      color: #ffffff;
    }
    .btn:focus-visible {
      outline: 2px solid #000000;
      outline-offset: 2px;
    }
    .close {
      width: 28px;
      height: 28px;
      border-radius: 4px;
      border: 2px solid var(--retro-border);
      background: var(--retro-panel);
      font-size: 16px;
      cursor: pointer;
      color: var(--retro-text);
    }
    .feedback {
      margin-top: 8px;
      padding: 8px;
      border: 2px dashed var(--retro-border);
      background: rgba(255, 255, 255, 0.6);
      font-size: 12px;
    }
    .feedback[hidden] {
      display: none;
    }
    @media (max-width: 640px) {
      .banner-inner {
        grid-template-columns: 1fr auto;
      }
      .preview {
        display: none;
      }
    }
  `;

  const container = document.createElement('div');
  container.className = 'banner';
  container.setAttribute('role', 'region');
  container.setAttribute('aria-label', 'RetrOS style approval banner');
  container.innerHTML = `
    <div class="banner-inner">
      <div class="preview" aria-hidden="true">
        <div class="preview-bar"></div>
        <div class="preview-body">
          <div class="preview-line"></div>
          <div class="preview-line short"></div>
          <div class="preview-line"></div>
        </div>
      </div>
      <div class="content">
        <div class="title">Styling applied for <span class="era-name">${era}</span></div>
        <div class="subtitle">Approve to keep this style on future visits.</div>
        <div class="actions">
          <button class="btn primary" id="retros-approve">Approve</button>
          <button class="btn" id="retros-reject">Reject</button>
          <button class="btn" id="retros-feedback" aria-expanded="false" aria-controls="retros-feedback-panel">Feedback</button>
        </div>
        <div class="feedback" id="retros-feedback-panel" hidden>
          Feedback options will appear here after the next update.
        </div>
      </div>
      <button class="close" id="retros-close" aria-label="Close approval banner">×</button>
    </div>
  `;

  shadow.appendChild(style);
  shadow.appendChild(container);

  const approveBtn = shadow.getElementById('retros-approve');
  const rejectBtn = shadow.getElementById('retros-reject');
  const feedbackBtn = shadow.getElementById('retros-feedback');
  const closeBtn = shadow.getElementById('retros-close');
  const feedbackPanel = shadow.getElementById('retros-feedback-panel');

  approveBtn.addEventListener('click', async () => {
    const domain = window.location.hostname;
    await sendRuntimeMessage({
      type: 'APPROVE_STYLE',
      payload: { domain, era }
    });
    hideApprovalBanner();
  });

  rejectBtn.addEventListener('click', async () => {
    const domain = window.location.hostname;
    await sendRuntimeMessage({
      type: 'REJECT_STYLE',
      payload: { domain, era }
    });
    feedbackPanel.hidden = false;
    feedbackBtn.setAttribute('aria-expanded', 'true');
  });

  feedbackBtn.addEventListener('click', () => {
    const nextState = !feedbackPanel.hidden;
    feedbackPanel.hidden = nextState;
    feedbackBtn.setAttribute('aria-expanded', String(!nextState));
  });

  closeBtn.addEventListener('click', () => {
    hideApprovalBanner();
  });

  container.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      hideApprovalBanner();
    }
  });

  document.documentElement.appendChild(approvalBannerHost);
  approvalBannerVisible = true;
}

function hideApprovalBanner() {
  if (!approvalBannerHost) return;
  approvalBannerHost.remove();
  approvalBannerHost = null;
  approvalBannerVisible = false;
}

async function initApprovalBanner() {
  try {
    const domain = window.location.hostname;
    const [settings, siteStatus] = await Promise.all([
      sendRuntimeMessage({ type: 'GET_SETTINGS' }),
      sendRuntimeMessage({ type: 'GET_SITE_STATUS', payload: { domain } })
    ]);

    const era = (settings && settings.data && settings.data.selectedEra) || 'Windows 95';
    const status = siteStatus && siteStatus.data ? siteStatus.data : {};

    if (shouldShowBanner(status)) {
      createApprovalBanner(era);
      return;
    }

    if (status.approvalStatus !== 'approved') {
      const observer = new MutationObserver(() => {
        if (approvalBannerVisible) return;
        if (shouldShowBanner(status)) {
          createApprovalBanner(era);
          observer.disconnect();
        }
      });
      observer.observe(document.documentElement, { childList: true, subtree: true });
      setTimeout(() => observer.disconnect(), 15000);
    }
  } catch (error) {
    console.warn('Failed to initialize approval banner', error);
  }
}

if (document.readyState === 'complete' || document.readyState === 'interactive') {
  initApprovalBanner();
} else {
  document.addEventListener('DOMContentLoaded', initApprovalBanner, { once: true });
}

/* ---------------------- End approval banner ---------------------- */
