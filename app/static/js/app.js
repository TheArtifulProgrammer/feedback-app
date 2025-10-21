/**
 * Feedback App - Client-side JavaScript
 * Handles all API interactions and UI updatess
 */

// ============================================================================
// Global State
// ============================================================================
let feedbackToDelete = null;

// ============================================================================
// API Client Functions
// ============================================================================
const API = {
    baseURL: window.location.origin,

    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    // Health check
    async checkHealth() {
        return await this.request('/health');
    },

    // Get all feedback
    async getAllFeedback() {
        return await this.request('/feedback');
    },

    // Create feedback
    async createFeedback(message) {
        return await this.request('/feedback', {
            method: 'POST',
            body: JSON.stringify({ message })
        });
    },

    // Update feedback
    async updateFeedback(id, message) {
        return await this.request(`/feedback/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ message })
        });
    },

    // Delete feedback
    async deleteFeedback(id) {
        return await this.request(`/feedback/${id}`, {
            method: 'DELETE'
        });
    }
};

// ============================================================================
// UI Functions
// ============================================================================

/**
 * Initialize the application
 */
async function init() {
    // Check health status
    updateHealthStatus();

    // Load feedback
    await loadFeedback();

    // Setup event listeners
    setupEventListeners();

    // Refresh health status every 30 seconds
    setInterval(updateHealthStatus, 30000);
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Add feedback button
    document.getElementById('add-feedback-btn').addEventListener('click', openAddModal);

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', loadFeedback);

    // Feedback form submission
    document.getElementById('feedback-form').addEventListener('submit', handleFormSubmit);

    // Character counter for textarea
    document.getElementById('feedback-message').addEventListener('input', updateCharCount);

    // Close modals on background click
    document.getElementById('feedback-modal').addEventListener('click', (e) => {
        if (e.target.id === 'feedback-modal') closeModal();
    });

    document.getElementById('delete-modal').addEventListener('click', (e) => {
        if (e.target.id === 'delete-modal') closeDeleteModal();
    });
}

/**
 * Update health status badge
 */
async function updateHealthStatus() {
    const badge = document.getElementById('health-status');
    const statusText = badge.querySelector('.status-text');

    try {
        const health = await API.checkHealth();
        badge.classList.remove('unhealthy');
        badge.classList.add('healthy');
        statusText.textContent = 'Healthy';
    } catch (error) {
        badge.classList.remove('healthy');
        badge.classList.add('unhealthy');
        statusText.textContent = 'Unhealthy';
    }
}

/**
 * Load and display all feedback
 */
async function loadFeedback() {
    const feedbackList = document.getElementById('feedback-list');
    const emptyState = document.getElementById('empty-state');
    const loadingState = document.getElementById('loading-state');
    const countElement = document.getElementById('feedback-count');

    // Show loading state
    feedbackList.style.display = 'none';
    emptyState.style.display = 'none';
    loadingState.style.display = 'block';

    try {
        const feedbacks = await API.getAllFeedback();

        // Hide loading state
        loadingState.style.display = 'none';

        // Update count
        countElement.textContent = feedbacks.length;

        if (feedbacks.length === 0) {
            // Show empty state
            emptyState.style.display = 'block';
        } else {
            // Display feedback cards
            feedbackList.innerHTML = feedbacks.map(createFeedbackCard).join('');
            feedbackList.style.display = 'grid';
        }
    } catch (error) {
        loadingState.style.display = 'none';
        showToast('Failed to load feedback', 'error');
    }
}

/**
 * Create HTML for a feedback card
 */
function createFeedbackCard(feedback) {
    const createdDate = new Date(feedback.created_at).toLocaleString();
    const updatedDate = new Date(feedback.updated_at).toLocaleString();

    return `
        <div class="feedback-card">
            <div class="feedback-header">
                <div class="feedback-id">#${feedback.id}</div>
                <div class="feedback-actions">
                    <button class="btn btn-secondary btn-small" onclick="openEditModal(${feedback.id}, '${escapeHtml(feedback.message)}')">
                        Edit
                    </button>
                    <button class="btn btn-danger btn-small" onclick="openDeleteModal(${feedback.id})">
                        Delete
                    </button>
                </div>
            </div>
            <div class="feedback-message">${escapeHtml(feedback.message)}</div>
            <div class="feedback-meta">
                <div>Created: ${createdDate}</div>
                ${feedback.created_at !== feedback.updated_at ? `<div>Updated: ${updatedDate}</div>` : ''}
            </div>
        </div>
    `;
}

/**
 * Open modal to add new feedback
 */
function openAddModal() {
    const modal = document.getElementById('feedback-modal');
    const title = document.getElementById('modal-title');
    const form = document.getElementById('feedback-form');

    title.textContent = 'Add Feedback';
    form.reset();
    document.getElementById('feedback-id').value = '';

    modal.classList.add('active');
    document.getElementById('feedback-message').focus();
}

/**
 * Open modal to edit feedback
 */
function openEditModal(id, message) {
    const modal = document.getElementById('feedback-modal');
    const title = document.getElementById('modal-title');

    title.textContent = 'Edit Feedback';
    document.getElementById('feedback-id').value = id;
    document.getElementById('feedback-message').value = unescapeHtml(message);
    updateCharCount();

    modal.classList.add('active');
    document.getElementById('feedback-message').focus();
}

/**
 * Close feedback modal
 */
function closeModal() {
    const modal = document.getElementById('feedback-modal');
    modal.classList.remove('active');
}

/**
 * Handle form submission (create or update)
 */
async function handleFormSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('feedback-id').value;
    const message = document.getElementById('feedback-message').value.trim();

    if (!message) {
        showToast('Please enter a message', 'error');
        return;
    }

    try {
        if (id) {
            // Update existing feedback
            await API.updateFeedback(id, message);
            showToast('Feedback updated successfully', 'success');
        } else {
            // Create new feedback
            await API.createFeedback(message);
            showToast('Feedback created successfully', 'success');
        }

        closeModal();
        await loadFeedback();
    } catch (error) {
        showToast(error.message || 'Operation failed', 'error');
    }
}

/**
 * Open delete confirmation modal
 */
function openDeleteModal(id) {
    feedbackToDelete = id;
    document.getElementById('delete-modal').classList.add('active');
}

/**
 * Close delete confirmation modal
 */
function closeDeleteModal() {
    feedbackToDelete = null;
    document.getElementById('delete-modal').classList.remove('active');
}

/**
 * Confirm and execute delete
 */
async function confirmDelete() {
    if (!feedbackToDelete) return;

    try {
        await API.deleteFeedback(feedbackToDelete);
        showToast('Feedback deleted successfully', 'success');
        closeDeleteModal();
        await loadFeedback();
    } catch (error) {
        showToast(error.message || 'Delete failed', 'error');
    }
}

/**
 * Update character counter
 */
function updateCharCount() {
    const textarea = document.getElementById('feedback-message');
    const counter = document.getElementById('char-count');
    counter.textContent = textarea.value.length;
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');

    toastMessage.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Unescape HTML for editing
 */
function unescapeHtml(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    return div.textContent;
}

// ============================================================================
// Initialize on page load
// ============================================================================
document.addEventListener('DOMContentLoaded', init);
