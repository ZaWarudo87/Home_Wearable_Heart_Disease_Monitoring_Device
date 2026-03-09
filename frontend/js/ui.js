// --- Tab Switching & UI Helpers ---

function switchTab(tabId) {
    // Stop animation & disconnect WS when leaving ECG tab
    if (tabId !== 'ecg') {
        stopEcgAnimation();
        if (ecgSocket) {
            ecgSocket.close();
            ecgSocket = null;
        }
    }

    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(page => {
        page.classList.add('hidden');
    });

    // Reset all tab buttons to default style
    document.querySelectorAll('[id^="tab-"]').forEach(btn => {
        btn.classList.remove('bg-rose-800', 'text-rose-100');
        btn.classList.add('bg-rose-950', 'text-stone-400');
    });

    // Show the active tab content
    const activePage = document.getElementById(`page-${tabId}`);
    if (activePage) {
        activePage.classList.remove('hidden');
    }

    // Set active button style
    const activeButton = document.getElementById(`tab-${tabId}`);
    if (activeButton) {
        activeButton.classList.add('bg-rose-800', 'text-rose-100');
        activeButton.classList.remove('bg-rose-950', 'text-stone-400');
    }

    // Initialize or resize charts based on the active tab
    switch (tabId) {
        case 'bp':
            if (!charts.bpChart) {
                initializeBPChart('7d');
            } else {
                charts.bpChart.resize();
            }
            break;
        case 'hr1min':
            if (!charts.hr1minChart) {
                initializeHR1minChart('1h');
            } else {
                charts.hr1minChart.resize();
            }
            break;
        case 'hr30min':
            if (!charts.hr30minChart) {
                initializeHR30minChart('24h');
            } else {
                charts.hr30minChart.resize();
            }
            break;
        case 'risk':
            if (!charts.gaugeChart) {
                initializeGaugeChart();
            } else {
                charts.gaugeChart.resize();
            }
            break;
        case 'ecg':
            if (!charts.ecgChart) {
                initializeECGChart();
            }
            ecgPlay();
            break;
    }
}

function setupTabListeners() {
    document.getElementById('tab-overview').addEventListener('click', () => switchTab('overview'));
    document.getElementById('tab-bp').addEventListener('click', () => switchTab('bp'));
    document.getElementById('tab-hr1min').addEventListener('click', () => switchTab('hr1min'));
    document.getElementById('tab-hr30min').addEventListener('click', () => switchTab('hr30min'));
    document.getElementById('tab-risk').addEventListener('click', () => switchTab('risk'));
    document.getElementById('tab-ecg').addEventListener('click', () => switchTab('ecg'));
    document.getElementById('tab-health-data').addEventListener('click', () => switchTab('health-data'));
}

// --- Button Style Helper ---

function updateButtonStyles(activeButton, groupId) {
    const buttons = document.querySelectorAll(`[id^="${groupId}"]`);

    buttons.forEach(btn => {
        btn.classList.remove('bg-pink-600', 'text-rose-100');
        btn.classList.add('bg-rose-950', 'text-stone-400');
    });

    activeButton.classList.add('bg-pink-600', 'text-rose-100');
    activeButton.classList.remove('bg-rose-950', 'text-stone-400');
}

// --- Period Button Listeners ---

function setupPeriodListeners() {
    // BP period
    document.getElementById('bp-period-7').addEventListener('click', function() {
        updateBPChart('7d');
        updateButtonStyles(this, 'bp-period');
    });
    document.getElementById('bp-period-30').addEventListener('click', function() {
        updateBPChart('30d');
        updateButtonStyles(this, 'bp-period');
    });

    // HR 1-min period
    document.getElementById('hr1-period-1h').addEventListener('click', function() {
        updateHRChart('hr1minChart', '1min', '1h');
        updateButtonStyles(this, 'hr1-period');
    });
    document.getElementById('hr1-period-6h').addEventListener('click', function() {
        updateHRChart('hr1minChart', '1min', '6h');
        updateButtonStyles(this, 'hr1-period');
    });

    // HR 30-min period
    document.getElementById('hr30-period-24h').addEventListener('click', function() {
        updateHRChart('hr30minChart', '30min', '24h');
        updateButtonStyles(this, 'hr30-period');
    });
    document.getElementById('hr30-period-7d').addEventListener('click', function() {
        updateHRChart('hr30minChart', '30min', '7d');
        updateButtonStyles(this, 'hr30-period');
    });
}
