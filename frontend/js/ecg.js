// --- ECG WebSocket, Chart & Animation ---

let ecgSocket = null;
let ecgDataQueue = [];  // [{t, v}, ...] raw buffer (deduped)
let ecgDownloadBuffer = []; // [{t, v}, ...] rolling 30s buffer for download
let ecgAnimationInterval = null;
let isExercise = false;
const MAX_ECG_POINTS = 300;
const ECG_UPDATE_MS = 40;
const ECG_WINDOW_SECONDS = 10; // seconds of ECG to display
const ECG_DOWNLOAD_SECONDS = 30; // seconds of ECG kept for download

// ECG smooth-render state
let ecgLastReceivedTime = -Infinity;  // highest data timestamp received (for dedup)
let ecgRenderWallBase = null;         // performance.now() when rendering started
let ecgRenderDataBase = null;         // data-time corresponding to wallBase
let ecgDisplayOffset = null;          // first data-time of this display session (for 0-based X)

function updateAFStatus(afData) {
    const detectedEl = document.getElementById('af-detected');
    if (!detectedEl || !afData) return;
    detectedEl.textContent = afData.af_detected ? '有風險' : '無風險';
}

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
                        ecgDownloadBuffer.push({ t, v });
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
                    isExercise = data.mode === 'exercise';
                    modeEl.textContent = isExercise ? '運動模式' : '靜息模式';
                    modeEl.className = isExercise
                        ? 'text-sm font-semibold px-3 py-1 shadow-lg bg-purple-950 text-purple-200'
                        : 'text-sm font-semibold px-3 py-1 shadow-lg bg-rose-900 text-rose-200';
                }
            }
            updateAFStatus(data.af);
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
        ecgDownloadBuffer.length = 0;
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
                padding: { left: window.innerWidth * 0.01, right: window.innerWidth * 0.03, top: 10, bottom: 40 }
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
                        color: getThemeChartColors().tick,
                    },
                    ticks: {
                        color: getThemeChartColors().tick,
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
                    grid: { color: getThemeChartColors().grid }
                },
                y: {
                    min: -1.5,
                    max: 2.0,
                    ticks: { color: getThemeChartColors().tick },
                    grid: { color: getThemeChartColors().grid },
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
}

function stopEcgAnimation() {
    if (ecgAnimationInterval) {
        cancelAnimationFrame(ecgAnimationInterval);
        ecgAnimationInterval = null;
    }
}

function updateEcgButtonStyles(playing) {
    const playBtn = document.getElementById('ecg-play');
    const pauseBtn = document.getElementById('ecg-pause');
    if (!playBtn || !pauseBtn) return;
    if (playing) {
        playBtn.classList.add('bg-pink-600', 'text-rose-100');
        playBtn.classList.remove('bg-rose-950', 'text-stone-400');
        pauseBtn.classList.remove('bg-pink-600', 'text-rose-100');
        pauseBtn.classList.add('bg-rose-950', 'text-stone-400');
    } else {
        pauseBtn.classList.add('bg-pink-600', 'text-rose-100');
        pauseBtn.classList.remove('bg-rose-950', 'text-stone-400');
        playBtn.classList.remove('bg-pink-600', 'text-rose-100');
        playBtn.classList.add('bg-rose-950', 'text-stone-400');
    }
}

function ecgPlay() {
    // Reset chart data
    if (charts.ecgChart) {
        charts.ecgChart.data.datasets[0].data.length = 0;
        charts.ecgChart.update('none');
    }
    // Reset state
    ecgLastReceivedTime = -Infinity;
    ecgRenderWallBase = null;
    ecgRenderDataBase = null;
    ecgDisplayOffset = null;
    ecgDataQueue.length = 0;
    ecgDownloadBuffer.length = 0;
    // Connect & start
    connectWebSocket();
    startEcgAnimation();
    updateEcgButtonStyles(true);
}

function ecgPause() {
    // Disconnect WebSocket (onclose will call stopEcgAnimation)
    if (ecgSocket) {
        ecgSocket.close();
    }
    updateEcgButtonStyles(false);
}

function downloadEcgImage() {
    if (ecgDownloadBuffer.length === 0) return;

    // Trim buffer to last 30 seconds
    const latestT = ecgDownloadBuffer[ecgDownloadBuffer.length - 1].t;
    const cutoff = latestT - ECG_DOWNLOAD_SECONDS;
    while (ecgDownloadBuffer.length > 0 && ecgDownloadBuffer[0].t < cutoff) {
        ecgDownloadBuffer.shift();
    }

    const baseT = ecgDownloadBuffer[0].t;
    const points = ecgDownloadBuffer.map(p => ({ x: p.t - baseT, y: p.v }));
    const xMin = points[0].x;
    const xMax = points[points.length - 1].x;
    const totalSeconds = xMax - xMin;
    if (totalSeconds <= 0) return;

    // Canvas sizing: ~109px per second, min 2160px
    const pxPerSec = 109;
    const width = Math.max(2160, Math.ceil(totalSeconds * pxPerSec) + 160);
    const height = 500;
    const pad = { top: 60, bottom: 60, left: 80, right: 80 };
    const plotW = width - pad.left - pad.right;
    const plotH = height - pad.top - pad.bottom;

    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');

    // Background
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, width, height);

    // Grid
    const yMin = -1.5, yMax = 2.0;
    const toX = x => pad.left + ((x - xMin) / totalSeconds) * plotW;
    const toY = y => pad.top + ((yMax - y) / (yMax - yMin)) * plotH;

    // Light grid lines every 0.5s / 0.5mV
    ctx.strokeStyle = '#fecdd3';
    ctx.lineWidth = 0.5;
    const gridStart = Math.ceil(xMin * 2) / 2;
    for (let s = gridStart; s <= xMax; s += 0.5) {
        const px = toX(s);
        ctx.beginPath(); ctx.moveTo(px, pad.top); ctx.lineTo(px, pad.top + plotH); ctx.stroke();
    }
    for (let mv = yMin; mv <= yMax; mv += 0.5) {
        const py = toY(mv);
        ctx.beginPath(); ctx.moveTo(pad.left, py); ctx.lineTo(pad.left + plotW, py); ctx.stroke();
    }
    // Bold grid lines every 1s / 1mV
    ctx.strokeStyle = '#fda4af';
    ctx.lineWidth = 1;
    const boldStart = Math.ceil(xMin);
    for (let s = boldStart; s <= xMax; s += 1) {
        const px = toX(s);
        ctx.beginPath(); ctx.moveTo(px, pad.top); ctx.lineTo(px, pad.top + plotH); ctx.stroke();
    }
    for (let mv = Math.ceil(yMin); mv <= yMax; mv += 1) {
        const py = toY(mv);
        ctx.beginPath(); ctx.moveTo(pad.left, py); ctx.lineTo(pad.left + plotW, py); ctx.stroke();
    }

    // Axes labels
    ctx.fillStyle = '#44403c';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    for (let s = boldStart; s <= xMax; s += 1) {
        ctx.fillText(Math.round(s) + 's', toX(s), pad.top + plotH + 20);
    }
    ctx.textAlign = 'right';
    for (let mv = Math.ceil(yMin); mv <= yMax; mv += 1) {
        ctx.fillText(mv.toFixed(1), pad.left - 8, toY(mv) + 4);
    }

    // ECG trace
    ctx.strokeStyle = '#e11d48';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let i = 0; i < points.length; i++) {
        const px = toX(points[i].x);
        const py = toY(points[i].y);
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
    }
    ctx.stroke();

    // Title & info
    ctx.fillStyle = '#1c1917';
    ctx.font = 'bold 18px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('ECG 心電圖紀錄', pad.left, 30);
    ctx.font = '12px sans-serif';
    ctx.fillStyle = '#78716c';
    const now = new Date();
    const ts = now.getFullYear() + '/' + String(now.getMonth()+1).padStart(2,'0') + '/' + String(now.getDate()).padStart(2,'0') + ' ' + String(now.getHours()).padStart(2,'0') + ':' + String(now.getMinutes()).padStart(2,'0');
    ctx.fillText('下載時間: ' + ts + '  |  ' + (isExercise ? '運動模式' : '靜息模式') + '  |  資料長度: ' + totalSeconds.toFixed(1) + ' 秒  |  取樣點數: ' + points.length, pad.left, 48);

    // Download
    const link = document.createElement('a');
    link.download = 'ECG_' + now.getFullYear() + String(now.getMonth()+1).padStart(2,'0') + String(now.getDate()).padStart(2,'0') + '_' + String(now.getHours()).padStart(2,'0') + String(now.getMinutes()).padStart(2,'0') + String(now.getSeconds()).padStart(2,'0') + '.png';
    link.href = canvas.toDataURL('image/png');
    link.click();
}

function setupEcgControls() {
    document.getElementById('ecg-play').addEventListener('click', ecgPlay);
    document.getElementById('ecg-pause').addEventListener('click', ecgPause);
    document.getElementById('ecg-download').addEventListener('click', downloadEcgImage);
}
