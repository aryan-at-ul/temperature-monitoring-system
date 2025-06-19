// dashboard/static/js/dashboard.js

/**
 * Main dashboard JavaScript functionality
 */

// Initialize all tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap 5 is loaded
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Auto-close alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            if (bootstrap && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                alert.style.display = 'none';
            }
        });
    }, 5000);
    
    // Handle responsive navbar
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            if (bootstrap && bootstrap.Collapse) {
                const navbarCollapse = document.querySelector('#navbarNav');
                const bsCollapse = new bootstrap.Collapse(navbarCollapse);
                bsCollapse.toggle();
            }
        });
    }
    
    // Initialize any date pickers
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function(input) {
        // Set default value to today if not already set
        if (!input.value) {
            const today = new Date().toISOString().split('T')[0];
            input.value = today;
        }
    });
    
    // Add active class to current nav link
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        }
    });
    
    // Implement AJAX form submissions where needed
    const ajaxForms = document.querySelectorAll('form[data-ajax="true"]');
    ajaxForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const url = form.getAttribute('action') || window.location.href;
            const method = form.getAttribute('method') || 'POST';
            
            // Show loading indicator
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn ? submitBtn.innerHTML : '';
            
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
            }
            
            // Convert FormData to JSON
            const jsonData = {};
            formData.forEach(function(value, key) {
                jsonData[key] = value;
            });
            
            // Make API request
            fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(jsonData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Show success message
                showAlert('success', data.message || 'Operation completed successfully!');
                
                // Handle callback if specified
                const callback = form.getAttribute('data-callback');
                if (callback && typeof window[callback] === 'function') {
                    window[callback](data);
                }
                
                // Reset form if needed
                if (form.getAttribute('data-reset') === 'true') {
                    form.reset();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('danger', 'An error occurred: ' + error.message);
            })
            .finally(() => {
                // Restore submit button
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                }
            });
        });
    });
    
    // Implement confirmation dialogs
    const confirmBtns = document.querySelectorAll('[data-confirm]');
    confirmBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            const message = btn.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
    
    // Global temperature status updater
    updateTemperatureStatuses();
});

/**
 * Show an alert message
 * @param {string} type - Bootstrap alert type (success, danger, warning, info)
 * @param {string} message - The message to display
 * @param {boolean} dismissible - Whether the alert should be dismissible
 */
function showAlert(type, message, dismissible = true) {
    const alertContainer = document.getElementById('alertContainer') || document.createElement('div');
    
    if (!document.getElementById('alertContainer')) {
        alertContainer.id = 'alertContainer';
        alertContainer.style.position = 'fixed';
        alertContainer.style.top = '20px';
        alertContainer.style.right = '20px';
        alertContainer.style.zIndex = '9999';
        document.body.appendChild(alertContainer);
    }
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} fade show`;
    if (dismissible) {
        alert.className += ' alert-dismissible';
        alert.innerHTML = `
            <div>${message}</div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
    } else {
        alert.innerHTML = message;
    }
    
    alertContainer.appendChild(alert);
    
    // Auto-close after 5 seconds
    setTimeout(function() {
        if (bootstrap && bootstrap.Alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        } else {
            alert.style.display = 'none';
            if (alertContainer.contains(alert)) {
                alertContainer.removeChild(alert);
            }
        }
    }, 5000);
}

/**
 * Format temperature with the appropriate unit
 * @param {number} temp - The temperature value
 * @param {string} unit - The temperature unit (C, F, K)
 * @returns {string} - Formatted temperature string
 */
function formatTemperature(temp, unit) {
    return `${temp.toFixed(1)}°${unit}`;
}

/**
 * Get temperature status class based on the value and range
 * @param {number} temp - The temperature value
 * @param {number} setTemp - The set point temperature
 * @param {number} warningThreshold - Warning threshold deviation
 * @param {number} criticalThreshold - Critical threshold deviation
 * @returns {string} - CSS class for the temperature status
 */
function getTemperatureStatusClass(temp, setTemp, warningThreshold = 2, criticalThreshold = 5) {
    const deviation = Math.abs(temp - setTemp);
    
    if (deviation <= warningThreshold) {
        return 'temp-normal';
    } else if (deviation <= criticalThreshold) {
        return 'temp-warning';
    } else {
        return 'temp-danger';
    }
}

/**
 * Update all temperature status indicators
 */
function updateTemperatureStatuses() {
    const tempElements = document.querySelectorAll('[data-temp]');
    
    tempElements.forEach(function(element) {
        const temp = parseFloat(element.getAttribute('data-temp'));
        const setTemp = parseFloat(element.getAttribute('data-set-temp') || 0);
        const unit = element.getAttribute('data-unit') || 'C';
        const warningThreshold = parseFloat(element.getAttribute('data-warning') || 2);
        const criticalThreshold = parseFloat(element.getAttribute('data-critical') || 5);
        
        // Update temperature display
        element.textContent = formatTemperature(temp, unit);
        
        // Update status class
        element.classList.remove('temp-normal', 'temp-warning', 'temp-danger');
        element.classList.add(getTemperatureStatusClass(temp, setTemp, warningThreshold, criticalThreshold));
    });
}

/**
 * Format date and time
 * @param {string} dateString - The date string to format
 * @returns {string} - Formatted date string
 */
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

/**
 * Format date only
 * @param {string} dateString - The date string to format
 * @returns {string} - Formatted date string
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

/**
 * Format time only
 * @param {string} dateString - The date string to format
 * @returns {string} - Formatted time string
 */
function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString();
}

/**
 * Create a loading spinner
 * @returns {HTMLElement} - The spinner element
 */
function createLoadingSpinner() {
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    return spinner;
}

/**
 * Fetch data from the API
 * @param {string} endpoint - The API endpoint to fetch
 * @param {object} options - Fetch options
 * @returns {Promise} - Fetch promise
 */
async function fetchApi(endpoint, options = {}) {
    try {
        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API fetch error:', error);
        showAlert('danger', `API request failed: ${error.message}`);
        throw error;
    }
}