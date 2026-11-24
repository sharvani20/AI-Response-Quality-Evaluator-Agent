/* ======================================================
   App.js — Core Application Logic
   Tab navigation, API client, toasts, utilities
   ====================================================== */

// ---- API Client ----
const API_BASE = '';

async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    };

    // Don't set Content-Type for FormData
    if (options.body instanceof FormData) {
        delete config.headers['Content-Type'];
    }

    try {
        const response = await fetch(url, config);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Request failed (${response.status})`);
        }
        // Handle CSV download
        if (response.headers.get('content-type')?.includes('text/csv')) {
            return await response.blob();
        }
        return await response.json();
    } catch (error) {
        if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
            throw new Error('Unable to connect to the server. Please ensure it is running.');
        }
        throw error;
    }
}

// ---- Toast Notifications ----
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ---- Tab Navigation ----
function initTabs() {
    const tabs = document.querySelectorAll('.nav-tab');
    const panels = document.querySelectorAll('.tab-panel');
    const indicator = document.getElementById('nav-indicator');

    function activateTab(tabName) {
        tabs.forEach(t => t.classList.remove('active'));
        panels.forEach(p => p.classList.remove('active'));

        const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
        const activePanel = document.getElementById(`panel-${tabName}`);

        if (activeTab && activePanel) {
            activeTab.classList.add('active');
            activePanel.classList.add('active');
            updateIndicator(activeTab);

            // Trigger tab-specific initialization
            if (tabName === 'dashboard') {
                if (typeof loadDashboard === 'function') loadDashboard();
            } else if (tabName === 'batch') {
                if (typeof loadBatchHistory === 'function') loadBatchHistory();
            }
        }
    }

    function updateIndicator(tab) {
        if (!indicator || !tab) return;
        const tabRect = tab.getBoundingClientRect();
        const navRect = tab.parentElement.getBoundingClientRect();
        indicator.style.width = `${tabRect.width}px`;
        indicator.style.left = `${tabRect.left - navRect.left}px`;
    }

    tabs.forEach(tab => {
        tab.addEventListener('click', () => activateTab(tab.dataset.tab));
    });

    // Initialize first tab
    const firstActive = document.querySelector('.nav-tab.active');
    if (firstActive) {
        // Small delay to ensure layout is computed
        requestAnimationFrame(() => updateIndicator(firstActive));
    }

    // Handle resize
    window.addEventListener('resize', () => {
        const active = document.querySelector('.nav-tab.active');
        if (active) updateIndicator(active);
    });
}

// ---- Utility Functions ----
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function truncateText(text, maxLen = 60) {
    if (!text) return '';
    return text.length > maxLen ? text.substring(0, maxLen) + '...' : text;
}

function getScoreColor(score) {
    if (score >= 9) return 'var(--score-excellent)';
    if (score >= 7) return 'var(--score-good)';
    if (score >= 5) return 'var(--score-fair)';
    if (score >= 3) return 'var(--score-poor)';
    return 'var(--score-failing)';
}

function getTierClass(tier) {
    if (!tier) return 'tier-fair';
    const t = tier.toLowerCase();
    if (t === 'excellent') return 'tier-excellent';
    if (t === 'good') return 'tier-good';
    if (t === 'fair') return 'tier-fair';
    if (t === 'poor') return 'tier-poor';
    return 'tier-failing';
}

function getScoreBg(score) {
    const color = getScoreColor(score);
    return color.replace(')', ', 0.15)').replace('var(--score-', 'rgba(');
}

// ---- Character Count ----
function initCharCounts() {
    const textareas = [
        { el: 'eval-question', counter: 'question-count' },
        { el: 'eval-response', counter: 'response-count' },
        { el: 'eval-reference', counter: 'reference-count' },
    ];

    textareas.forEach(({ el, counter }) => {
        const textarea = document.getElementById(el);
        const count = document.getElementById(counter);
        if (textarea && count) {
            textarea.addEventListener('input', () => {
                count.textContent = `${textarea.value.length} characters`;
            });
        }
    });
}

// ---- Initialize App ----
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initCharCounts();

    // Load initial data
    if (typeof loadEvalHistory === 'function') loadEvalHistory();
});
