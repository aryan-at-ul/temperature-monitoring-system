/**
 * Main dashboard functionality
 */

// Use the global API client
const api = apiClient;

/**
 * Initialize the dashboard
 */
function initDashboard() {
    // Check if we're on the dashboard page
    if (document.getElementById('temperature-chart')) {
        updateDashboard();
    }
}

/**
 * Update the dashboard with latest data
 */
async function updateDashboard() {
    try {
        // Show loading indicators
        showLoadingState();
        
        // Get facility selector value if it exists
        const facilitySelector = document.getElementById('facility-selector');
        const facilityId = facilitySelector ? facilitySelector.value : 'all';
        
        // Get time range selector value if it exists
        const timeRangeSelector = document.getElementById('time-range-selector');
        const timeRange = timeRangeSelector ? timeRangeSelector.value : '24';
        
        console.log("Fetching data for facility:", facilityId, "time range:", timeRange);
        
        // Create params object with proper handling of 'all' facility
        const params = {
            // Only add facility_id if it's not 'all'
            ...(facilityId !== 'all' && { facility_id: facilityId }),
            hours: timeRange
        };
        
        // Fetch data
        const [temperatures, facilities, alerts] = await Promise.all([
            api.getLatestTemperatures(params),
            api.getCustomerFacilities(),
            api.getTemperatureAlerts(params)
        ]);
        
        console.log("Data fetched:", temperatures, facilities, alerts);
        
        // Update the dashboard components
        updateTemperatureDisplay(temperatures.units || []);
        updateFacilitiesDisplay(facilities.facilities || []);
        updateAlertsDisplay(alerts.alerts || []);
        
        // Update facility selector options
        if (facilitySelector && facilities.facilities) {
            updateFacilitySelector(facilitySelector, facilities.facilities);
        }
        
    } catch (error) {
        console.error('Error updating dashboard:', error);
        showErrorMessage('Failed to update dashboard. Please try again later.');
    }
}

/**
 * Show loading state for dashboard components
 */
function showLoadingState() {
    const temperatureTable = document.getElementById('current-temps-table');
    if (temperatureTable) {
        const tbody = temperatureTable.querySelector('tbody');
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center">
                    <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    Loading temperature data...
                </td>
            </tr>
        `;
    }
    
    const facilitiesContainer = document.getElementById('facilities-container');
    if (facilitiesContainer) {
        facilitiesContainer.innerHTML = `
            <div class="col-12 text-center">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p>Loading facilities data...</p>
            </div>
        `;
    }
    
    const alertsContainer = document.getElementById('alerts-container');
    if (alertsContainer) {
        alertsContainer.innerHTML = `
            <div class="text-center">
                <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                Loading alerts...
            </div>
        `;
    }
}

/**
 * Update temperature display with latest data
 * @param {Array} units - Temperature units data
 */
function updateTemperatureDisplay(units) {
    const temperatureTable = document.getElementById('current-temps-table');
    if (!temperatureTable) return;
    
    const tbody = temperatureTable.querySelector('tbody');
    
    if (!units || units.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No temperature data available</td></tr>';
        return;
    }
    
    // Sort units by status (critical first, then warning, then normal)
    const sortedUnits = [...units].sort((a, b) => {
        const statusOrder = { 'critical': 0, 'warning': 1, 'normal': 2 };
        return (statusOrder[a.status] || 3) - (statusOrder[b.status] || 3);
    });
    
    // Generate table rows
    tbody.innerHTML = sortedUnits.map(unit => {
        // Format status with appropriate styling
        let statusHtml = '';
        if (unit.status === 'critical') {
            statusHtml = '<span class="badge bg-danger">Critical</span>';
        } else if (unit.status === 'warning') {
            statusHtml = '<span class="badge bg-warning text-dark">Warning</span>';
        } else if (unit.status === 'normal') {
            statusHtml = '<span class="badge bg-success">Normal</span>';
        } else {
            statusHtml = `<span class="badge bg-secondary">${unit.status || 'Unknown'}</span>`;
        }
        
        // Format last updated time
        const lastUpdated = unit.last_updated ? new Date(unit.last_updated) : null;
        const timeAgo = lastUpdated ? getTimeAgo(lastUpdated) : 'Unknown';
        
        return `
            <tr data-unit-id="${unit.unit_id}" class="unit-row" style="cursor: pointer">
                <td>${unit.name || 'Unnamed Unit'}</td>
                <td>${unit.facility_name || 'Unknown Facility'}</td>
                <td>${unit.current_temperature !== undefined ? unit.current_temperature.toFixed(1) + '°' + (unit.unit || 'C') : 'N/A'}</td>
                <td>${statusHtml}</td>
                <td>${timeAgo}</td>
            </tr>
        `;
    }).join('');
    
    // Add click event to show unit details
    document.querySelectorAll('.unit-row').forEach(row => {
        row.addEventListener('click', () => {
            const unitId = row.dataset.unitId;
            showUnitDetails(unitId, sortedUnits);
        });
    });
    
    // Update temperature chart if it exists
    const chartCanvas = document.getElementById('temperature-chart');
    if (chartCanvas) {
        updateTemperatureChart(chartCanvas, units);
    }
}

/**
 * Update facilities display
 * @param {Array} facilities - Facilities data
 */
function updateFacilitiesDisplay(facilities) {
    const facilitiesContainer = document.getElementById('facilities-container');
    if (!facilitiesContainer) return;
    
    if (!facilities || facilities.length === 0) {
        facilitiesContainer.innerHTML = '<div class="col-12 text-center">No facilities available</div>';
        return;
    }
    
    // Generate facility cards
    facilitiesContainer.innerHTML = facilities.map(facility => {
        return `
            <div class="col-md-4 mb-4">
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="card-title mb-0">${facility.name || 'Unnamed Facility'}</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Location:</strong> ${facility.city ? facility.city + ', ' + (facility.country || '') : 'Unknown'}</p>
                        <p><strong>Units:</strong> ${facility.units_count || 0}</p>
                    </div>
                    <div class="card-footer">
                        <button class="btn btn-sm btn-primary view-facility-btn" data-facility-id="${facility.id}">
                            <i class="bi bi-eye"></i> View Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    // Add event listeners to view facility buttons
    document.querySelectorAll('.view-facility-btn').forEach(button => {
        button.addEventListener('click', () => {
            const facilityId = button.getAttribute('data-facility-id');
            const facilitySelector = document.getElementById('facility-selector');
            if (facilitySelector) {
                facilitySelector.value = facilityId;
                updateDashboard();
            }
        });
    });
}

/**
 * Update alerts display
 * @param {Array} alerts - Alerts data
 */
function updateAlertsDisplay(alerts) {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    if (!alerts || alerts.length === 0) {
        alertsContainer.innerHTML = '<div class="text-center text-muted">No alerts in the selected time period</div>';
        return;
    }
    
    // Sort alerts by timestamp (newest first) and severity
    const sortedAlerts = [...alerts].sort((a, b) => {
        // First by resolved status
        if (a.resolved !== b.resolved) {
            return a.resolved ? 1 : -1;
        }
        
        // Then by severity
        if (a.severity !== b.severity) {
            return a.severity === 'critical' ? -1 : 1;
        }
        
        // Finally by timestamp
        return new Date(b.timestamp) - new Date(a.timestamp);
    });
    
    // Generate alert items
    alertsContainer.innerHTML = sortedAlerts.map(alert => {
        const timestamp = new Date(alert.timestamp);
        const timeAgo = getTimeAgo(timestamp);
        
        return `
            <div class="alert-item ${alert.severity} ${alert.resolved ? 'resolved' : ''}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>
                            ${alert.unit_name} - ${alert.facility_name}
                            ${alert.resolved ? '<span class="badge bg-secondary ms-2">Resolved</span>' : ''}
                        </strong>
                        <div>${alert.message}</div>
                    </div>
                    <span class="alert-time">${timeAgo}</span>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Update facility selector options
 * @param {HTMLElement} selector - Facility selector element
 * @param {Array} facilities - Facilities data
 */
function updateFacilitySelector(selector, facilities) {
    // Save current selection
    const currentValue = selector.value;
    
    // Clear existing options except the first one (All Facilities)
    while (selector.options.length > 1) {
        selector.remove(1);
    }
    
    // Add facility options
    facilities.forEach(facility => {
        const option = document.createElement('option');
        option.value = facility.id;
        option.textContent = facility.name || 'Unnamed Facility';
        selector.appendChild(option);
    });
    
    // Restore selection if possible
    if (currentValue && Array.from(selector.options).some(opt => opt.value === currentValue)) {
        selector.value = currentValue;
    }
}

/**
 * Update temperature chart
 * @param {HTMLElement} canvas - Chart canvas element
 * @param {Array} units - Temperature units data
 */
function updateTemperatureChart(canvas, units) {
    // This is a placeholder for the chart implementation
    // In a real application, you would use Chart.js to create a chart
    console.log('Updating temperature chart with', units.length, 'units');
    
    // Simple implementation to show something on the chart
    if (window.temperatureChart) {
        window.temperatureChart.destroy();
    }
    
    const ctx = canvas.getContext('2d');
    window.temperatureChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Now'],
            datasets: units.map((unit, index) => {
                const colors = [
                    'rgba(13, 110, 253, 1)',
                    'rgba(25, 135, 84, 1)',
                    'rgba(220, 53, 69, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(13, 202, 240, 1)',
                    'rgba(111, 66, 193, 1)'
                ];
                return {
                    label: unit.name || `Unit ${index + 1}`,
                    data: [unit.current_temperature],
                    borderColor: colors[index % colors.length],
                    backgroundColor: colors[index % colors.length].replace('1)', '0.2)'),
                    tension: 0.1
                };
            })
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Temperature (°C)'
                    }
                }
            }
        }
    });
}

/**
 * Show unit details in a modal
 * @param {string} unitId - Unit ID
 * @param {Array} units - All units data
 */
async function showUnitDetails(unitId, units) {
    const unit = units.find(u => u.unit_id === unitId);
    if (!unit) return;
    
    // Populate modal with unit data
    document.getElementById('modal-unit-name').textContent = unit.name || 'Unnamed Unit';
    document.getElementById('modal-facility-name').textContent = unit.facility_name || 'Unknown Facility';
    document.getElementById('modal-current-temp').textContent = unit.current_temperature !== undefined ? 
        `${unit.current_temperature.toFixed(1)}°${unit.unit || 'C'}` : 'N/A';
    document.getElementById('modal-target-temp').textContent = unit.set_temperature !== undefined ? 
        `${unit.set_temperature.toFixed(1)}°${unit.unit || 'C'}` : 'N/A';
    
    // Format status with appropriate styling
    let statusHtml = '';
    if (unit.status === 'critical') {
        statusHtml = '<span class="badge bg-danger">Critical</span>';
    } else if (unit.status === 'warning') {
        statusHtml = '<span class="badge bg-warning text-dark">Warning</span>';
    } else if (unit.status === 'normal') {
        statusHtml = '<span class="badge bg-success">Normal</span>';
    } else {
        statusHtml = `<span class="badge bg-secondary">${unit.status || 'Unknown'}</span>`;
    }
    document.getElementById('modal-status').innerHTML = statusHtml;
    
    // Additional data if available
    document.getElementById('modal-equipment-type').textContent = unit.equipment_type || 'N/A';
    document.getElementById('modal-size').textContent = unit.size_value ? 
        `${unit.size_value} ${unit.size_unit || ''}` : 'N/A';
    document.getElementById('modal-last-update').textContent = unit.last_updated ? 
        new Date(unit.last_updated).toLocaleString() : 'N/A';
    
    // Try to get history data
    try {
        const response = await api.getTemperatures({
            unit_id: unitId,
            hours: 24,
            limit: 24
        });
        
        // Update unit history chart
        const chartCanvas = document.getElementById('unit-history-chart');
        if (chartCanvas && response.readings && response.readings.length > 0) {
            renderUnitHistoryChart(chartCanvas, response.readings, unit);
        } else {
            document.getElementById('unit-history-chart').parentNode.innerHTML = 
                '<div class="alert alert-info">No historical data available for this unit</div>';
        }
    } catch (error) {
        console.error('Error fetching unit history:', error);
        document.getElementById('unit-history-chart').parentNode.innerHTML = 
            '<div class="alert alert-danger">Failed to load history data</div>';
    }
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('unit-detail-modal'));
    modal.show();
}

/**
 * Render unit history chart
 * @param {HTMLElement} canvas - Chart canvas element
 * @param {Array} readings - Temperature readings
 * @param {Object} unit - Unit information
 */
function renderUnitHistoryChart(canvas, readings, unit) {
    // Sort readings by timestamp
    const sortedReadings = [...readings].sort((a, b) => 
        new Date(a.timestamp) - new Date(b.timestamp));
    
    // Extract data for chart
    const labels = sortedReadings.map(reading => {
        const date = new Date(reading.timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    });
    
    const temperatures = sortedReadings.map(reading => reading.temperature);
    
    // Create reference line for set temperature
    const setTemperature = Array(labels.length).fill(unit.set_temperature || null);
    
    if (window.unitHistoryChart) {
        window.unitHistoryChart.destroy();
    }
    
    const ctx = canvas.getContext('2d');
    window.unitHistoryChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Temperature',
                    data: temperatures,
                    borderColor: 'rgba(13, 110, 253, 1)',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    fill: true,
                    tension: 0.1
                },
                {
                    label: 'Set Temperature',
                    data: setTemperature,
                    borderColor: 'rgba(25, 135, 84, 1)',
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    title: {
                        display: true,
                        text: `Temperature (°${unit.unit || 'C'})`
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                }
            }
        }
    });
}

/**
 * Show error message on the dashboard
 * @param {string} message - Error message
 */
function showErrorMessage(message) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        <strong>Error:</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Find a good place to show the alert
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    }
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
}

/**
 * Get time ago string from date
 * @param {Date} date - Date to format
 * @returns {string} - Formatted time ago string
 */
function getTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.round(diffMs / 1000);
    const diffMin = Math.round(diffSec / 60);
    const diffHour = Math.round(diffMin / 60);
    const diffDay = Math.round(diffHour / 24);
    
    if (diffSec < 60) {
        return `${diffSec} second${diffSec !== 1 ? 's' : ''} ago`;
    } else if (diffMin < 60) {
        return `${diffMin} minute${diffMin !== 1 ? 's' : ''} ago`;
    } else if (diffHour < 24) {
        return `${diffHour} hour${diffHour !== 1 ? 's' : ''} ago`;
    } else {
        return `${diffDay} day${diffDay !== 1 ? 's' : ''} ago`;
    }
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', initDashboard);