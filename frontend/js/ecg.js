// --- ECG WebSocket, Chart & Animation ---

let ecgSocket = null;
let ecgDataQueue = [];  // [{t, v}, ...] raw buffer (deduped)
let ecgAnimationInterval = null;
const MAX_ECG_POINTS = 300;
const ECG_UPDATE_MS = 40;
const ECG_WINDOW_SECONDS = 10; // seconds of ECG to display

// ECG smooth-render state
let ecgLastReceivedTime = -Infinity;  // highest data timestamp received (for dedup)
let ecgRenderWallBase = null;         // performance.now() when rendering started
let ecgRenderDataBase = null;         // data-time corresponding to wallBase
let ecgDisplayOffset = null;          // first data-time of this display session (for 0-based X)

// --- WebSocket ---

function connectWebSocket() {
    if (ecgSocket || !apiToken) return;

    const wsHost = API_BASE_URL.replace(/^https?:\/\//, '');
    const proto = API_BASE_URL.startsWith('https:') ? 'wss' : 'ws';

    const wsUrl = `${proto}://${wsHost}/ws/ecg/stream?token=${apiToken}`;

    ecgSocket = new WebSocket(wsUrl);

    ecgSocket.onopen = () => {
        console.log('ECG WebSocket Connected');
        if (!document.getElementById('page-ecg').classList.contains('hidden')) {
            startEcgAnimation();
        }
    };

    ecgSocket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.points && Array.isArray(data.points)) {
                const times = data.times || [];
                for (let i = 0; i < data.points.length; ++i) {
                    const t = times[i];
                    const v = data.points[i];
                    if (t !== undefined && t !== null && v !== null && t > ecgLastReceivedTime) {
                        ecgDataQueue.push({ t, v });
                        ecgLastReceivedTime = t;
                    }
                }
                if (ecgDataQueue.length > 0 && ecgRenderWallBase === null) {
                    ecgRenderWallBase = performance.now();
                    ecgRenderDataBase = ecgDataQueue[0].t;
                    ecgDisplayOffset = ecgDataQueue[0].t;
                }
            }
            if (data.heart_rate) {
                document.getElementById('current-heart-rate').textContent = data.heart_rate;
            }
            if (data.mode) {
                const modeEl = document.getElementById('ecg-mode-indicator');
                if (modeEl) {
                    const isExercise = data.mode === 'exercise';
                    modeEl.textContent = isExercise ? '運動模式' : '靜息模式';
                    modeEl.className = isExercise
                        ? 'text-sm font-semibold px-3 py-1 shadow-lg bg-purple-950 text-purple-200'
                        : 'text-sm font-semibold px-3 py-1 shadow-lg bg-rose-900 text-rose-200';
                }
            }
        } catch (e) {
            console.error('Error parsing ECG data:', e);
        }
    };

    ecgSocket.onclose = () => {
        console.log('ECG WebSocket Disconnected');
        ecgSocket = null;
        stopEcgAnimation();
        ecgLastReceivedTime = -Infinity;
        ecgRenderWallBase = null;
        ecgRenderDataBase = null;
        ecgDisplayOffset = null;
        ecgDataQueue.length = 0;
    };

    ecgSocket.onerror = (error) => {
        console.error('WebSocket Error:', error);
        stopEcgAnimation();
    };
}

// --- ECG Chart ---

function initializeECGChart() {
    const ctx = document.getElementById('ecgChart').getContext('2d');
    const initialData = [];

    charts.ecgChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'ECG',
                data: initialData,
                borderColor: config.accent_color || '#f43f5e',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            parsing: false,
            layout: {
                autoPadding: false,
                padding: { left: 25, right: 40, top: 10, bottom: 40 }
            },
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            scales: {
                x: {
                    type: 'linear',
                    display: true,
                    offset: false,
                    title: {
                        display: true,
                        text: '時間 (秒)',
                        color: '#d6d3d1',
                    },
                    ticks: {
                        color: '#d6d3d1',
                        maxRotation: 0,
                        autoSkip: false,
                        callback: function(value) {
                            return Number.isInteger(value) ? value + 's' : '';
                        }
                    },
                    afterBuildTicks: function(axis) {
                        const start = Math.ceil(axis.min);
                        const end = Math.floor(axis.max);
                        const ticks = [];
                        for (let v = start; v <= end; ++v) {
                            ticks.push({ value: v });
                        }
                        axis.ticks = ticks;
                    },
                    afterFit: function(axis) {
                        axis.height = 40; // fixed height prevents layout bounce
                    },
                    grid: { color: '#6b5563' }
                },
                y: {
                    min: -1.5,
                    max: 2.0,
                    ticks: { color: '#d6d3d1' },
                    grid: { color: '#6b5563' },
                    afterFit: function(axis) {
                        axis.width = 50; // fixed width prevents horizontal layout shift
                    }
                }
            }
        }
    });

    if (!document.getElementById('page-ecg').classList.contains('hidden')) {
        startEcgAnimation();
    }
}

// --- ECG Animation Loop ---

function ecgUpdateLoop() {
    if (!charts.ecgChart) {
        ecgAnimationInterval = requestAnimationFrame(ecgUpdateLoop);
        return;
    }

    const dataset = charts.ecgChart.data.datasets[0];
    const data = dataset.data;

    let currentDataTime;
    if (ecgRenderWallBase !== null && ecgRenderDataBase !== null) {
        const wallElapsedSec = (performance.now() - ecgRenderWallBase) / 1000;
        currentDataTime = ecgRenderDataBase + wallElapsedSec;
    } else {
        ecgAnimationInterval = requestAnimationFrame(ecgUpdateLoop);
        return;
    }

    let changed = false;
    while (ecgDataQueue.length > 0 && ecgDataQueue[0].t <= currentDataTime) {
        const point = ecgDataQueue.shift();
        const relX = point.t - ecgDisplayOffset;
        if (data.length > 0) {
            const prevRelX = data[data.length - 1].x;
            if (relX < prevRelX - 1.0) {
                // Timestamp reset (ESP32 restart)
                data.length = 0;
                ecgRenderWallBase = performance.now();
                ecgRenderDataBase = point.t;
                ecgDisplayOffset = point.t;
            }
        }
        data.push({ x: relX, y: point.v });
        changed = true;
    }

    const elapsed = currentDataTime - ecgRenderDataBase;
    const displayElapsed = currentDataTime - ecgDisplayOffset;
    const viewEnd = displayElapsed;
    const viewStart = viewEnd - ECG_WINDOW_SECONDS;

    let trimIdx = 0;
    while (trimIdx < data.length && data[trimIdx].x < viewStart - 1) {
        ++trimIdx;
    }
    if (trimIdx > 0) data.splice(0, trimIdx);

    charts.ecgChart.options.scales.x.min = Math.max(0, viewStart);
    charts.ecgChart.options.scales.x.max = Math.max(ECG_WINDOW_SECONDS, viewEnd);
    charts.ecgChart.update('none');

    ecgAnimationInterval = requestAnimationFrame(ecgUpdateLoop);
}

function startEcgAnimation() {
    if (ecgAnimationInterval) return;
    ecgAnimationInterval = requestAnimationFrame(ecgUpdateLoop);

    document.getElementById('ecg-play').classList.add('bg-pink-600', 'text-rose-100');
    document.getElementById('ecg-play').classList.remove('bg-rose-950', 'text-stone-400');
    document.getElementById('ecg-pause').classList.remove('bg-pink-600', 'text-rose-100');
    document.getElementById('ecg-pause').classList.add('bg-rose-950', 'text-stone-400');
}

function stopEcgAnimation() {
    if (ecgAnimationInterval) {
        cancelAnimationFrame(ecgAnimationInterval);
        ecgAnimationInterval = null;
    }

    const playBtn = document.getElementById('ecg-play');
    const pauseBtn = document.getElementById('ecg-pause');

    if (playBtn && pauseBtn) {
        pauseBtn.classList.add('bg-pink-600', 'text-rose-100');
        pauseBtn.classList.remove('bg-rose-950', 'text-stone-400');
        playBtn.classList.remove('bg-pink-600', 'text-rose-100');
        playBtn.classList.add('bg-rose-950', 'text-stone-400');
    }
}

function setupEcgControls() {
    document.getElementById('ecg-play').addEventListener('click', startEcgAnimation);
    document.getElementById('ecg-pause').addEventListener('click', stopEcgAnimation);
}
