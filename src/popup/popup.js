/**
 * Popup Script
 * 
 * Handles the extension popup UI:
 * - Display current site and era
 * - Show status information
 * - Route to settings
 * - Manage approval workflow
 * - Handle feedback submission
 */

console.log('RetrOS-Web popup script loaded');

// Track state
let currentDomain = '';
let currentEra = '';
let feedbackOpen = false;
let selectedFeedback = null;

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
      currentDomain = domain;
      document.getElementById('current-domain').textContent = domain;
      console.log(`Current domain: ${domain}`);
      // Query site status (cache + approval)
      try {
        const siteStatus = await sendMessage({ type: 'GET_SITE_STATUS', payload: { domain } });
        if (siteStatus && siteStatus.success) {
          const data = siteStatus.data || {};
          if (data.approvalStatus === 'approved') {
            document.getElementById('status-indicator').textContent = 'Approved ✓';
            document.getElementById('status-indicator').className = 'info-value status approved';
          } else if (data.cacheStatus === 'cached') {
            document.getElementById('status-indicator').textContent = 'Cached';
          } else if (data.cacheStatus === 'regenerating') {
            document.getElementById('status-indicator').textContent = 'Regenerating...';
          } else {
            document.getElementById('status-indicator').textContent = 'Ready';
          }
          console.log('Site status:', data);
        }
      } catch (err) {
        console.warn('Failed to get site status', err);
      }
    } else {
      document.getElementById('current-domain').textContent = 'Unknown';
    }

    // Get current era
    const settings = await sendMessage({ type: 'GET_SETTINGS' });
    if (settings.success) {
      const era = settings.data.selectedEra || 'Not selected';
      currentEra = era;
      document.getElementById('current-era').textContent = era;
      document.getElementById('approval-era').textContent = era;
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
  // Approval buttons
  document.getElementById('approve-btn').addEventListener('click', approveStyle);
  document.getElementById('reject-btn').addEventListener('click', rejectStyle);
  document.getElementById('feedback-btn').addEventListener('click', toggleFeedback);
  document.getElementById('close-approval-btn').addEventListener('click', closeApproval);

  // Feedback preset buttons
  document.querySelectorAll('.feedback-preset').forEach(btn => {
    btn.addEventListener('click', (e) => handleFeedbackPreset(e.target));
  });

  // Feedback textarea
  document.getElementById('feedback-text').addEventListener('input', updateCharCounter);

  // Regenerate button
  document.getElementById('regenerate-btn').addEventListener('click', regenerateStyle);

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
      if (feedbackOpen) {
        closeFeedback();
      } else {
        // Optionally close popup
        // window.close();
      }
    }
  });

  console.log('Event listeners setup complete');
}

/* ---------------------- Era selection (US-1.3) ---------------------- */

function initEraSelection() {
  const eraOptions = Array.from(document.querySelectorAll('.era-card'));

  // Initialize selection from settings (provided during popup init) or default
  let initial = (currentEra && currentEra.toLowerCase()) || '90s';

  eraOptions.forEach((btn) => {
    const era = btn.getAttribute('data-era').toLowerCase();
    if (era === initial) {
      setEraSelected(btn, true);
      btn.tabIndex = 0;
    } else {
      setEraSelected(btn, false);
      btn.tabIndex = -1;
    }

    btn.addEventListener('click', () => {
      eraOptions.forEach(b => setEraSelected(b, false));
      setEraSelected(btn, true);
      // update currentEra display
      currentEra = btn.getAttribute('data-era');
      document.getElementById('current-era').textContent = currentEra;
      document.getElementById('approval-era').textContent = currentEra;
    });

    // Keyboard navigation within the grid
    btn.addEventListener('keydown', (e) => handleEraKeydown(e, eraOptions));
  });

  // Set as default button
  const setBtn = document.getElementById('set-default-era');
  if (setBtn) {
    setBtn.addEventListener('click', () => {
      const selected = document.querySelector('.era-card[aria-checked="true"]');
      if (selected) {
        const era = selected.getAttribute('data-era');
        // Persist via background storage helper
        sendMessage({ type: 'SET_SETTING', key: 'selectedEra', value: era }).then(() => {
          console.log('Popup: persisted selectedEra ->', era);
        }).catch((err) => console.warn('Popup: failed to persist era', err));
        document.getElementById('status-indicator').textContent = 'Default set ✓';
        setTimeout(() => { document.getElementById('status-indicator').textContent = 'Ready'; }, 1200);
      }
    });
  }
}

function setEraSelected(button, selected) {
  button.setAttribute('aria-checked', selected ? 'true' : 'false');
  if (selected) {
    button.classList.add('selected');
    button.tabIndex = 0;
    button.focus();
  } else {
    button.classList.remove('selected');
    button.tabIndex = -1;
  }
}

function handleEraKeydown(e, eraOptions) {
  const key = e.key;
  const current = e.currentTarget;
  const idx = eraOptions.indexOf(current);

  if (key === 'ArrowRight' || key === 'ArrowDown') {
    e.preventDefault();
    const next = eraOptions[(idx + 1) % eraOptions.length];
    eraOptions.forEach(b => setEraSelected(b, false));
    setEraSelected(next, true);
  } else if (key === 'ArrowLeft' || key === 'ArrowUp') {
    e.preventDefault();
    const prev = eraOptions[(idx - 1 + eraOptions.length) % eraOptions.length];
    eraOptions.forEach(b => setEraSelected(b, false));
    setEraSelected(prev, true);
  } else if (key === 'Enter' || key === ' ') {
    e.preventDefault();
    // Treat as click
    current.click();
  }
}

// Initialize era UI after DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // small timeout to ensure existing init runs first
  setTimeout(() => initEraSelection(), 0);
});

/* ---------------------- End Era selection ---------------------- */

/**
 * Approve the current style
 */
async function approveStyle() {
  console.log('Approving style for:', currentDomain);
  
  try {
    const response = await sendMessage({
      type: 'APPROVE_STYLE',
      payload: {
        domain: currentDomain,
        era: currentEra
      }
    });

    if (response.success) {
      console.log('Style approved');
      document.getElementById('status-indicator').textContent = 'Approved ✓';
      document.getElementById('status-indicator').className = 'info-value status approved';
      
      // Hide approval section after short delay
      setTimeout(() => {
        document.getElementById('approval-section').style.display = 'none';
      }, 500);
    } else {
      console.error('Approval failed:', response.error);
      alert('Failed to approve style: ' + response.error);
    }
  } catch (error) {
    console.error('Error approving style:', error);
    alert('Error approving style');
  }
}

/**
 * Reject the current style and show feedback form
 */
function rejectStyle() {
  console.log('Rejecting style for:', currentDomain);
  openFeedback();
}

/**
 * Toggle feedback form visibility
 */
function toggleFeedback() {
  if (feedbackOpen) {
    closeFeedback();
  } else {
    openFeedback();
  }
}

/**
 * Open feedback form
 */
function openFeedback() {
  feedbackOpen = true;
  document.getElementById('feedback-section').hidden = false;
  document.getElementById('feedback-btn').classList.add('active');
  document.getElementById('feedback-text').focus();
  console.log('Feedback form opened');
}

/**
 * Close feedback form
 */
function closeFeedback() {
  feedbackOpen = false;
  document.getElementById('feedback-section').hidden = true;
  document.getElementById('feedback-btn').classList.remove('active');
  
  // Clear form
  document.querySelectorAll('.feedback-preset').forEach(btn => {
    btn.classList.remove('selected');
  });
  document.getElementById('feedback-text').value = '';
  updateCharCounter();
  selectedFeedback = null;
  
  console.log('Feedback form closed');
}

/**
 * Close approval section
 */
function closeApproval() {
  console.log('Closing approval section');
  document.getElementById('approval-section').style.display = 'none';
}

/**
 * Handle feedback preset button click
 */
function handleFeedbackPreset(button) {
  const feedbackType = button.getAttribute('data-feedback');
  
  // Toggle selection
  if (button.classList.contains('selected')) {
    button.classList.remove('selected');
    selectedFeedback = null;
  } else {
    // Remove selection from other buttons (single select)
    document.querySelectorAll('.feedback-preset').forEach(btn => {
      btn.classList.remove('selected');
    });
    
    // Select this button
    button.classList.add('selected');
    selectedFeedback = feedbackType;
  }
  
  console.log('Feedback selected:', selectedFeedback);
}

/**
 * Update character counter for feedback textarea
 */
function updateCharCounter() {
  const textarea = document.getElementById('feedback-text');
  const counter = document.getElementById('char-count');
  const counterEl = document.querySelector('.char-counter');
  
  const remaining = textarea.value.length;
  counter.textContent = remaining;
  
  // Update class based on remaining characters
  if (remaining > 180) {
    counterEl.classList.add('warning');
    counterEl.classList.remove('error');
  } else if (remaining === 200) {
    counterEl.classList.add('error');
    counterEl.classList.remove('warning');
  } else {
    counterEl.classList.remove('warning', 'error');
  }
}

/**
 * Regenerate style with feedback
 */
async function regenerateStyle() {
  const feedbackText = document.getElementById('feedback-text').value.trim();
  
  // Validation
  if (!selectedFeedback && !feedbackText) {
    alert('Please select a feedback option or provide additional feedback');
    return;
  }

  console.log('Regenerating style with feedback:', {
    preset: selectedFeedback,
    text: feedbackText
  });

  try {
    // Show loading state
    const btn = document.getElementById('regenerate-btn');
    const originalText = btn.textContent;
    btn.textContent = '⏳ Regenerating...';
    btn.disabled = true;

    const response = await sendMessage({
      type: 'REGENERATE_STYLE',
      payload: {
        domain: currentDomain,
        feedback: {
          preset: selectedFeedback,
          text: feedbackText
        }
      }
    });

    // Restore button
    btn.textContent = originalText;
    btn.disabled = false;

    if (response.success) {
      console.log('Style regenerated');
      document.getElementById('status-indicator').textContent = 'Generating...';
      
      // Close feedback form
      closeFeedback();
      
      // Show success message
      setTimeout(() => {
        document.getElementById('status-indicator').textContent = 'Regenerated ✓';
      }, 1000);
    } else {
      console.error('Regeneration failed:', response.error);
      alert('Failed to regenerate style: ' + response.error);
    }
  } catch (error) {
    console.error('Error regenerating style:', error);
    alert('Error regenerating style');
    
    // Restore button
    const btn = document.getElementById('regenerate-btn');
    btn.textContent = '🔄 Regenerate & Apply';
    btn.disabled = false;
  }
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

