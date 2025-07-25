// Main JavaScript file for NEXAS application

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeTooltips();
    initializeAlerts();
    initializeFormValidation();
    initializeAjaxSetup();
    initializeDashboardUpdates();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Auto-hide alerts after 5 seconds
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

// Form validation enhancement
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

// AJAX setup with CSRF token
function initializeAjaxSetup() {
    // Get CSRF token
    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    // Add CSRF token to all AJAX requests
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        if (options.method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method.toUpperCase())) {
            options.headers = options.headers || {};
            options.headers['X-CSRFToken'] = getCSRFToken();
        }
        return originalFetch(url, options);
    };
}

// Dashboard real-time updates
function initializeDashboardUpdates() {
    if (document.getElementById('dashboard-stats')) {
        // Update dashboard stats every 30 seconds
        setInterval(updateDashboardStats, 30000);
    }
}

// Update dashboard statistics
function updateDashboardStats() {
    fetch('/dashboard/api/stats/')
        .then(response => response.json())
        .then(data => {
            // Update stat cards if they exist
            updateStatCard('total-users', data.total_users);
            updateStatCard('active-users', data.active_users);
            updateStatCard('online-users', data.online_users);
            updateStatCard('recent-activities', data.recent_activities);
        })
        .catch(error => {
            console.error('Error updating dashboard stats:', error);
        });
}

// Helper function to update stat cards
function updateStatCard(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
        // Add a subtle animation
        element.style.transform = 'scale(1.1)';
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 200);
    }
}

// Utility functions
const NEXAS = {
    // Show loading state
    showLoading: function(element) {
        if (element) {
            element.classList.add('loading');
            element.innerHTML += '<span class="spinner-border spinner-border-sm ms-2" role="status"></span>';
        }
    },

    // Hide loading state
    hideLoading: function(element) {
        if (element) {
            element.classList.remove('loading');
            const spinner = element.querySelector('.spinner-border');
            if (spinner) {
                spinner.remove();
            }
        }
    },

    // Show toast notification
    showToast: function(message, type = 'success') {
        const toastContainer = document.getElementById('toast-container') || createToastContainer();
        
        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
        toastEl.setAttribute('role', 'alert');
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toastEl);
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
        
        // Remove toast element after it's hidden
        toastEl.addEventListener('hidden.bs.toast', () => {
            toastEl.remove();
        });
    },

    // Confirm dialog
    confirm: function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    },

    // Format numbers with commas
    formatNumber: function(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    // Format currency
    formatCurrency: function(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },

    // Format date
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Create toast container if it doesn't exist
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

// Search functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('[data-search]');
    searchInputs.forEach(input => {
        const debouncedSearch = NEXAS.debounce(performSearch, 300);
        input.addEventListener('input', debouncedSearch);
    });
}

function performSearch(event) {
    const searchTerm = event.target.value;
    const searchType = event.target.dataset.search;
    
    // Implement search logic based on searchType
    console.log(`Searching for "${searchTerm}" in ${searchType}`);
}

// User status toggle
function toggleUserStatus(userId) {
    NEXAS.confirm('Are you sure you want to change this user\'s status?', () => {
        fetch(`/accounts/user/${userId}/toggle-status/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                NEXAS.showToast(data.message, 'success');
                // Update UI
                const statusBadge = document.querySelector(`[data-user-id="${userId}"] .status-badge`);
                if (statusBadge) {
                    statusBadge.textContent = data.is_active ? 'Active' : 'Inactive';
                    statusBadge.className = `badge ${data.is_active ? 'bg-success' : 'bg-danger'} status-badge`;
                }
            } else {
                NEXAS.showToast(data.error || 'An error occurred', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            NEXAS.showToast('An error occurred', 'danger');
        });
    });
}

// Export functions to global scope
window.NEXAS = NEXAS;
window.toggleUserStatus = toggleUserStatus;
