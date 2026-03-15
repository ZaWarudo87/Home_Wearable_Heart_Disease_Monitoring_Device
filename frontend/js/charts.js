// --- Blood Pressure & Heart Rate Charts ---

// Initialize blood pressure chart
async function initializeBPChart(period) {
    try {
        const data = await fetchWithAuth(`/api/v1/charts/bp?period=${period}`);
        const ctx = document.getElementById('bpChart').getContext('2d');

        charts.bpChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: '靜息血壓',
                    data: data.values,
                    borderColor: config.accent_color || '#ef4444',
                    backgroundColor: (config.accent_color || '#ef4444') + '20',
                    tension: 0.4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: false, ticks: { color: getThemeChartColors().tick }, grid: { color: getThemeChartColors().grid } },
                    x: { ticks: { color: getThemeChartColors().tick }, grid: { color: getThemeChartColors().grid } }
                }
            }
        });
    } catch (error) {
        console.error('Failed to initialize BP Chart:', error);
    }
}

// Update blood pressure chart with new period
async function updateBPChart(period) {
    if (!charts.bpChart) return;
    try {
        const data = await fetchWithAuth(`/api/v1/charts/bp?period=${period}`);
        charts.bpChart.data.labels = data.labels;
        charts.bpChart.data.datasets[0].data = data.values;
        charts.bpChart.update();
    } catch (error) {
        console.error('Failed to update BP Chart:', error);
    }
}

// Initialize 1-minute interval heart rate chart
async function initializeHR1minChart(period) {
    try {
        const data = await fetchWithAuth(`/api/v1/charts/hr?interval=1min&period=${period}`);
        const ctx = document.getElementById('hr1minChart').getContext('2d');
        charts.hr1minChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: '平均心率',
                    data: data.values,
                    borderColor: config.primary_color || '#4f46e5',
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: false, ticks: { color: getThemeChartColors().tick }, grid: { color: getThemeChartColors().grid } },
                    x: { ticks: { color: getThemeChartColors().tick }, grid: { color: getThemeChartColors().grid } }
                }
            }
        });
    } catch (error) {
        console.error('Failed to initialize HR1min Chart:', error);
    }
}

// Initialize 30-minute interval heart rate chart
async function initializeHR30minChart(period) {
    try {
        const data = await fetchWithAuth(`/api/v1/charts/hr?interval=30min&period=${period}`);
        const ctx = document.getElementById('hr30minChart').getContext('2d');
        charts.hr30minChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: '平均心率',
                    data: data.values,
                    borderColor: config.primary_color || '#4f46e5',
                    tension: 0.4,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: false, ticks: { color: getThemeChartColors().tick }, grid: { color: getThemeChartColors().grid } },
                    x: { ticks: { color: getThemeChartColors().tick }, grid: { color: getThemeChartColors().grid } }
                }
            }
        });
    } catch (error) {
        console.error('Failed to initialize HR30min Chart:', error);
    }
}

// Update heart rate chart with new interval/period
async function updateHRChart(chartName, interval, period) {
    if (!charts[chartName]) return;
    try {
        const data = await fetchWithAuth(`/api/v1/charts/hr?interval=${interval}&period=${period}`);
        charts[chartName].data.labels = data.labels;
        charts[chartName].data.datasets[0].data = data.values;
        charts[chartName].update();
    } catch (error) {
        console.error(`Failed to update ${chartName}:`, error);
    }
}
