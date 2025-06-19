/**
 * Charts module for temperature monitoring dashboard
 */

/**
 * Render temperature chart for a specific unit
 * @param {string} canvasId - Canvas element ID
 * @param {Array} readings - Temperature readings
 * @param {Object} unit - Unit information
 */
function renderUnitHistoryChart(canvasId, readings, unit) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Convert readings to chart data format
    const labels = readings.map(reading => {
        const date = new Date(reading.timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    });
    
    const temperatures = readings.map(reading => reading.temperature);
    
    // Create chart
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Temperature',
                data: temperatures,
                borderColor: 'rgba(13, 110, 253, 1)',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                tension: 0.1,
                fill: true
            }]
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
    
    return chart;
}