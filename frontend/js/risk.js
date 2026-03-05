// --- Risk Gauge Chart ---

async function initializeGaugeChart() {
    try {
        const data = await fetchWithAuth('/api/v1/health/risk');
        const riskScore = data.risk_score;
        const riskLevel = data.level;

        document.getElementById('risk-score').textContent = riskScore;
        document.getElementById('risk-level').textContent = riskLevel;

        const ctx = document.getElementById('gaugeChart').getContext('2d');
        charts.gaugeChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [riskScore, 100 - riskScore],
                    backgroundColor: [
                        riskScore < 30 ? '#00a63e' : riskScore < 70 ? '#e17100' : '#e7000b',
                        '#3f0d1e'
                    ],
                    borderWidth: 0,
                    circumference: 180,
                    rotation: 270
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            }
        });
    } catch (error) {
        console.error('Failed to initialize Gauge Chart:', error);
    }
}
