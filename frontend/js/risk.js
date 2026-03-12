// --- Risk Gauge Chart ---

async function initializeGaugeChart() {
    try {
        const canvas = document.getElementById('gaugeChart');
        const ctx = canvas.getContext('2d');
        // ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.reset();
        document.getElementById('risk-score').textContent = "--";
        document.getElementById('risk-level').textContent = "--";

        const data = await fetchWithAuth('/api/v1/health/risk');
        const riskScore = data.risk_score;
        const riskLevel = data.level;

        document.getElementById('risk-score').textContent = riskScore;
        document.getElementById('risk-level').textContent = riskLevel;

        if (charts.gaugeChart) {
            charts.gaugeChart.destroy();
        }
        charts.gaugeChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [riskScore, 100 - riskScore],
                    backgroundColor: [
                        riskScore < 30 ? '#00a63e' : riskScore < 70 ? '#e17100' : '#e7000b',
                        getThemeChartColors().gaugeBg
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
