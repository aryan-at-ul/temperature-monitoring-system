// dashboard/static/js/admin.js

/**
 * Admin dashboard specific JavaScript functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize admin dashboard components
    initAdminDashboard();
    
    // Set up customer management
    initCustomerManagement();
    
    // Set up facility management
    initFacilityManagement();
    
    // Set up configuration management
    initConfigManagement();
    
    // Set up ML controls
    initMlControls();
});

/**
 * Initialize admin dashboard
 */
function initAdminDashboard() {
    // Customer stats chart
    const customerStatsChart = document.getElementById('customerStatsChart');
    if (customerStatsChart) {
        // Fetch customer stats data
        fetch('/admin/api/customer_stats')
            .then(response => response.json())
            .then(data => {
                renderCustomerStatsChart(customerStatsChart, data);
            })
            .catch(error => {
                console.error('Error fetching customer stats:', error);
                customerStatsChart.parentElement.innerHTML = '<div class="alert alert-danger">Error loading customer statistics</div>';
            });
    }
    
    // Ingestion summary chart
    const ingestionSummaryChart = document.getElementById('ingestionSummaryChart');
    if (ingestionSummaryChart) {
        // Fetch ingestion summary data
        fetch('/admin/api/ingestion_summary')
            .then(response => response.json())
            .then(data => {
                renderIngestionSummaryChart(ingestionSummaryChart, data);
            })
            .catch(error => {
                console.error('Error fetching ingestion summary:', error);
                ingestionSummaryChart.parentElement.innerHTML = '<div class="alert alert-danger">Error loading ingestion statistics</div>';
            });
    }
}

/**
 * Render customer statistics chart
 * @param {HTMLElement} canvas - The canvas element
 * @param {Object} data - The customer statistics data
 */
function renderCustomerStatsChart(canvas, data) {
    const ctx = canvas.getContext('2d');
    
    // Extract data
    const labels = data.map(customer => customer.customer_code);
    const facilityCounts = data.map(customer => customer.facility_count);
    const unitCounts = data.map(customer => customer.unit_count);
    const readingCounts = data.map(customer => customer.reading_count);
    
    // Create chart
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Facilities',
                    data: facilityCounts,
                    backgroundColor: 'rgba(13, 110, 253, 0.7)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Storage Units',
                    data: unitCounts,
                    backgroundColor: 'rgba(220, 53, 69, 0.7)',
                    borderColor: 'rgba(220, 53, 69, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Count'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Customer'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Customer Resources'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            }
        }
    });
    
    // Create a separate chart for readings (different scale)
    const readingsCanvas = document.createElement('canvas');
    readingsCanvas.id = 'customerReadingsChart';
    readingsCanvas.height = 300;
    canvas.parentElement.appendChild(readingsCanvas);
    
    const readingsCtx = readingsCanvas.getContext('2d');
    
    new Chart(readingsCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Temperature Readings',
                    data: readingCounts,
                    backgroundColor: 'rgba(25, 135, 84, 0.7)',
                    borderColor: 'rgba(25, 135, 84, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Reading Count'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Customer'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Customer Temperature Readings'
                }
            }
        }
    });
}

/**
 * Render ingestion summary chart
 * @param {HTMLElement} canvas - The canvas element
 * @param {Object} data - The ingestion summary data
 */
function renderIngestionSummaryChart(canvas, data) {
    const ctx = canvas.getContext('2d');
    
    // Create chart
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Success', 'Failure'],
            datasets: [
                {
                    data: [data.success_count, data.failure_count],
                    backgroundColor: [
                        'rgba(25, 135, 84, 0.7)',
                        'rgba(220, 53, 69, 0.7)'
                    ],
                    borderColor: [
                        'rgba(25, 135, 84, 1)',
                        'rgba(220, 53, 69, 1)'
                    ],
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Ingestion Process Results'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = data.success_count + data.failure_count;
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    // Add summary text
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'mt-3 text-center';
    summaryDiv.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Success Rate</h5>
                        <h2 class="text-success">${data.success_rate.toFixed(1)}%</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Total Records</h5>
                        <h2>${data.total_records}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Processes</h5>
                        <h2>${data.success_count + data.failure_count}</h2>
                    </div>
                </div>
            </div>
        </div>
    `;
    canvas.parentElement.appendChild(summaryDiv);
}

/**
 * Initialize customer management
 */
function initCustomerManagement() {
    // Customer create form
    const customerCreateForm = document.getElementById('customerCreateForm');
    if (customerCreateForm) {
        customerCreateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(customerCreateForm);
            const jsonData = {};
            formData.forEach((value, key) => { jsonData[key] = value; });
            
            // Submit the form data
            fetch('/admin/customers', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(jsonData)
            })
            .then(response => response.json())
            .then(data => {
                showAlert('success', 'Customer created successfully!');
                customerCreateForm.reset();
                
                // Refresh the page after a short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            })
            .catch(error => {
                console.error('Error creating customer:', error);
                showAlert('danger', 'Error creating customer: ' + error.message);
            });
        });
    }
    
    // Customer update forms
    const customerUpdateForms = document.querySelectorAll('.customer-update-form');
    customerUpdateForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const customerId = form.getAttribute('data-customer-id');
            const formData = new FormData(form);
            const jsonData = {};
            formData.forEach((value, key) => { jsonData[key] = value; });
            
            // Submit the form data
            fetch(`/admin/customers/${customerId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(jsonData)
            })
            .then(response => response.json())
            .then(data => {
                showAlert('success', 'Customer updated successfully!');
                
                // Update the customer name in the UI
                const customerNameElements = document.querySelectorAll(`.customer-name-${customerId}`);
                customerNameElements.forEach(el => {
                    el.textContent = jsonData.name;
                });
            })
            .catch(error => {
                console.error('Error updating customer:', error);
                showAlert('danger', 'Error updating customer: ' + error.message);
            });
        });
    });
    
    // Customer token creation forms
    const tokenCreateForms = document.querySelectorAll('.token-create-form');
    tokenCreateForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const customerId = form.getAttribute('data-customer-id');
            const formData = new FormData(form);
            const jsonData = {};
            formData.forEach((value, key) => { jsonData[key] = value; });
            
            // Submit the form data
            fetch(`/admin/customers/${customerId}/tokens`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(jsonData)
            })
            .then(response => response.json())
            .then(data => {
                showAlert('success', 'Token created successfully!');
                form.reset();
                
                // Show the token value to the user
                const tokenModal = document.getElementById('tokenModal');
                const tokenValueElement = document.getElementById('newTokenValue');
                
                if (tokenValueElement && tokenModal && bootstrap.Modal) {
                    tokenValueElement.textContent = data.token_value || data.token;
                    const modal = new bootstrap.Modal(tokenModal);
                    modal.show();
                }
                
                // Refresh the token list
                setTimeout(() => {
                    window.location.reload();
                }, 5000);
            })
            .catch(error => {
                console.error('Error creating token:', error);
                showAlert('danger', 'Error creating token: ' + error.message);
            });
        });
    });
    
    // Token revocation buttons
    const revokeTokenButtons = document.querySelectorAll('.revoke-token-btn');
    revokeTokenButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (!confirm('Are you sure you want to revoke this token? This action cannot be undone.')) {
                return;
            }
            
            const customerId = button.getAttribute('data-customer-id');
            const tokenId = button.getAttribute('data-token-id');
            
            fetch(`/admin/customers/${customerId}/tokens/${tokenId}`, {
                method: 'DELETE'
            })
            .then(response => {
                if (response.ok) {
                    showAlert('success', 'Token revoked successfully!');
                    
                    // Remove the token from the UI
                    const tokenRow = button.closest('tr');
                    if (tokenRow) {
                        tokenRow.remove();
                    }
                } else {
                    throw new Error('Failed to revoke token');
                }
            })
            .catch(error => {
                console.error('Error revoking token:', error);
                showAlert('danger', 'Error revoking token: ' + error.message);
            });
        });
    });
}

/**
 * Initialize facility management
 */
function initFacilityManagement() {
    // Facility create form
    const facilityCreateForm = document.getElementById('facilityCreateForm');
    if (facilityCreateForm) {
        facilityCreateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(facilityCreateForm);
            const jsonData = {};
            formData.forEach((value, key) => { jsonData[key] = value; });
            
            // Submit the form data
            fetch('/admin/facilities', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(jsonData)
            })
            .then(response => response.json())
            .then(data => {
                showAlert('success', 'Facility created successfully!');
                facilityCreateForm.reset();
                
                // Refresh the page after a short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            })
            .catch(error => {
                console.error('Error creating facility:', error);
                showAlert('danger', 'Error creating facility: ' + error.message);
            });
        });
    }
    
    // Facility update forms
    const facilityUpdateForms = document.querySelectorAll('.facility-update-form');
    facilityUpdateForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const facilityId = form.getAttribute('data-facility-id');
            const formData = new FormData(form);
            const jsonData = {};
            formData.forEach((value, key) => { jsonData[key] = value; });
            
            // Submit the form data
            fetch(`/admin/facilities/${facilityId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(jsonData)
            })
            .then(response => response.json())
            .then(data => {
                showAlert('success', 'Facility updated successfully!');
                
                // Update the facility name in the UI
                const facilityNameElements = document.querySelectorAll(`.facility-name-${facilityId}`);
                facilityNameElements.forEach(el => {
                    el.textContent = jsonData.name || jsonData.facility_code;
                });
            })
            .catch(error => {
                console.error('Error updating facility:', error);
                showAlert('danger', 'Error updating facility: ' + error.message);
            });
        });
    });
    
    // Storage unit create forms
    const unitCreateForms = document.querySelectorAll('.unit-create-form');
    unitCreateForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const facilityId = form.getAttribute('data-facility-id');
            const formData = new FormData(form);
            const jsonData = {};
            formData.forEach((value, key) => { jsonData[key] = value; });
            
            // Submit the form data
            fetch(`/admin/facilities/${facilityId}/units`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(jsonData)
            })
            .then(response => response.json())
            .then(data => {
                showAlert('success', 'Storage unit created successfully!');
                form.reset();
                
                // Refresh the page after a short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            })
            .catch(error => {
                console.error('Error creating storage unit:', error);
                showAlert('danger', 'Error creating storage unit: ' + error.message);
            });
        });
    });
    
    // Storage unit update forms
    const unitUpdateForms = document.querySelectorAll('.unit-update-form');
    unitUpdateForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const unitId = form.getAttribute('data-unit-id');
            const formData = new FormData(form);
            const jsonData = {};
            formData.forEach((value, key) => { jsonData[key] = value; });
            
            // Submit the form data
            fetch(`/admin/units/${unitId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(jsonData)
            })
            .then(response => response.json())
            .then(data => {
                showAlert('success', 'Storage unit updated successfully!');
                
                // Update the unit name in the UI
                const unitNameElements = document.querySelectorAll(`.unit-name-${unitId}`);
                unitNameElements.forEach(el => {
                    el.textContent = jsonData.name || jsonData.unit_code;
                });
            })
            .catch(error => {
                console.error('Error updating storage unit:', error);
                showAlert('danger', 'Error updating storage unit: ' + error.message);
            });
        });
    });
}

/**
 * Initialize configuration management
 */
function initConfigManagement() {
    // Config update forms
    const configUpdateForms = document.querySelectorAll('.config-update-form');
    configUpdateForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const configKey = form.getAttribute('data-config-key');
            const formData = new FormData(form);
            const jsonData = {};
            formData.forEach((value, key) => { jsonData[key] = value; });
            
            // Submit the form data
            fetch(`/admin/config/${configKey}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(jsonData)
            })
            .then(response => response.json())
            .then(data => {
                showAlert('success', 'Configuration updated successfully!');
                
                // Update the config value in the UI
                const configValueElements = document.querySelectorAll(`.config-value-${configKey}`);
                configValueElements.forEach(el => {
                    el.textContent = jsonData.value;
                });
            })
            .catch(error => {
                console.error('Error updating configuration:', error);
                showAlert('danger', 'Error updating configuration: ' + error.message);
            });
        });
    });
}

/**
 * Initialize ML controls
 */
function initMlControls() {
    // This is a placeholder for future ML integration
    // Currently, ML features are in preview mode
    
    // ML model configuration forms
    const mlConfigForms = document.querySelectorAll('.ml-config-form');
    mlConfigForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Since ML features are in preview, just show a message
            showAlert('info', 'ML feature is currently in preview. This functionality will be available in the future.');
        });
    });
    
    // ML training buttons
    const mlTrainingButtons = document.querySelectorAll('.ml-training-btn');
    mlTrainingButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Since ML features are in preview, just show a message
            showAlert('info', 'ML training is currently in preview. This functionality will be available in the future.');
        });
    });
}