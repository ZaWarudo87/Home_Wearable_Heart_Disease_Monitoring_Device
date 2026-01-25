// --- Configuration and State ---

const defaultConfig = {
    user_name: "王小明",
    dashboard_title: "心臟健康監測系統",
    summary_text: "目前心臟狀況穩定...",
    background_color: "#f8fafc",
    surface_color: "#ffffff",
    text_color: "#1f2937",
    primary_color: "#4f46e5",
    accent_color: "#ef4444"
};
let config = { ...defaultConfig };

let charts = {};
let apiToken = null; 
let ecgSocket = null; 
let ecgDataQueue = []; 
let ecgAnimationInterval = null;
const MAX_ECG_POINTS = 300;
const ECG_UPDATE_MS = 40;

// --- API Base URL ---
const API_BASE_URL = "https://templates-discipline-uses-ratios.trycloudflare.com";

// --- API Helper ---

async function fetchWithAuth(url, options = {}) {
    if (!apiToken) {
        console.error('No API token. Redirecting to login.');
        handleSignOut(); 
        throw new Error('Not Authenticated');
    }

    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiToken}`,
        ...options.headers,
    };

    const fullUrl = `${API_BASE_URL}${url}`;

    const response = await fetch(fullUrl, { ...options, headers });

    if (!response.ok) {
        if (response.status === 401) {
            console.error('Authentication failed. Logging out.');
            handleSignOut();
        }
        throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
}

// --- Google Authentication Handlers ---

async function handleCredentialResponse(credentialResponse) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/google`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ google_token: credentialResponse.credential })
        });

        if (!response.ok) {
            throw new Error('Backend authentication failed');
        }

        const data = await response.json();
        apiToken = data.api_token;
        sessionStorage.setItem('apiToken', apiToken);
        if(data.user.name)
            defaultConfig.user_name = data.user.name;
        
        // 檢查是否為新用戶
        if (data.is_new_user) {
            showRegistrationForm();
        } else {
            await initializeApp(data.user);
        }

    } catch (error) {
        console.error('Login failed:', error);
        alert('登入失敗，請稍後再試。');
    }
}

function handleSignOut() {
    apiToken = null;
    sessionStorage.removeItem('apiToken');
    
    if (ecgSocket) {
        ecgSocket.close();
        ecgSocket = null;
    }
    stopEcgAnimation();
    
    Object.keys(charts).forEach(key => {
        if (charts[key]) {
            charts[key].destroy();
            charts[key] = null;
        }
    });
    charts = {};
    
    if (window.google && window.google.accounts && window.google.accounts.id) {
        google.accounts.id.disableAutoSelect();
    }

    document.getElementById('login-view').classList.remove('hidden');
    document.getElementById('registration-view').classList.add('hidden');
    document.getElementById('dashboard-view').classList.add('hidden');
}

// --- Registration Form ---

function showRegistrationForm() {
    document.getElementById('login-view').classList.add('hidden');
    document.getElementById('registration-view').classList.remove('hidden');
    document.getElementById('dashboard-view').classList.add('hidden');
}

async function handleRegistrationSubmit(event) {
    event.preventDefault();
    
    const formData = {
        sex: document.getElementById('sex').value,
        age: parseInt(document.getElementById('age').value),
        chest_pain_type: document.getElementById('chest-pain-type').value,
        exercise_angina: document.getElementById('exercise-angina').value === 'Y'
    };
    
    try {
        const response = await fetchWithAuth('/api/v1/user/profile', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        console.log('Registration successful:', response);
        
        // 註冊成功後，獲取用戶資料並初始化應用
        const userData = await fetchWithAuth('/api/auth/me');
        await initializeApp(userData.user);
        
    } catch (error) {
        console.error('Registration failed:', error);
        alert('資料提交失敗，請稍後再試。');
    }
}

function initializeGSI() {
    if (!window.google || !window.google.accounts) {
        console.error("Google GSI script not loaded.");
        return;
    }
    
    google.accounts.id.initialize({
        client_id: "693422158799-3b30id9m2eo0l4463m4njruokbalk5bd.apps.googleusercontent.com",
        callback: handleCredentialResponse
    });
    
    google.accounts.id.renderButton(
        document.getElementById("g_id_signin"),
        { theme: "outline", size: "large", text: "signin_with", shape: "rectangular" }
    );
}

// --- Main Application Logic ---

async function initializeApp(user) {
    document.getElementById('user-name').textContent = user.name;
    document.getElementById('login-view').classList.add('hidden');
    document.getElementById('registration-view').classList.add('hidden');
    document.getElementById('dashboard-view').classList.remove('hidden');

    setupTabListeners();
    setupPeriodListeners();
    setupEcgControls();
    setupHealthDataForm();
    document.getElementById('logout-button').addEventListener('click', handleSignOut);

    await fetchHealthSummary();
    
    // 預設選中 'overview'
    document.getElementById('tab-overview').classList.add('bg-indigo-600', 'text-white');
    document.getElementById('tab-overview').classList.remove('bg-gray-200', 'text-gray-700');
    document.getElementById('page-overview').classList.remove('hidden');
}

async function fetchHealthSummary() {
    try {
        const data = await fetchWithAuth('/api/v1/health/summary');
        
        document.getElementById('last-update').textContent = `最後更新：${new Date(data.last_update).toLocaleString()}`;
        document.getElementById('resting-bp').textContent = data.overview.resting_bp;
        document.getElementById('avg-hr').textContent = data.overview.avg_hr;
        document.getElementById('max-hr').textContent = data.overview.max_hr;
        document.getElementById('st-slope').textContent = data.overview.st_slope;
        document.getElementById('health-summary').textContent = data.ai_summary;
        
    } catch (error) {
        console.error('Failed to fetch health summary:', error);
        document.getElementById('health-summary').textContent = '資料載入失敗。';
    }
}

// --- Chart Functions ---

function switchTab(tabId) {
    // 停止所有動畫
    stopEcgAnimation();
    
    // 如果切換到非 ECG 頁面，關閉 WebSocket
    if (tabId !== 'ecg' && ecgSocket) {
        ecgSocket.close();
        ecgSocket = null;
    }

    // 隱藏所有分頁
    document.querySelectorAll('.tab-content').forEach(page => {
        page.classList.add('hidden');
    });
    
    // 重設所有分頁按鈕樣式
    document.querySelectorAll('[id^="tab-"]').forEach(btn => {
        btn.classList.remove('bg-indigo-600', 'text-white');
        btn.classList.add('bg-gray-200', 'text-gray-700');
    });
    
    // 顯示點擊的分頁
    const activePage = document.getElementById(`page-${tabId}`);
    if (activePage) {
        activePage.classList.remove('hidden');
    }
    
    // 設置點擊按鈕的 active 樣式
    const activeButton = document.getElementById(`tab-${tabId}`);
    if (activeButton) {
        activeButton.classList.add('bg-indigo-600', 'text-white');
        activeButton.classList.remove('bg-gray-200', 'text-gray-700');
    }
    
    // 根據 tabId 初始化圖表
    switch(tabId) {
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
            if (!charts.ecgChart) { //gohere
                connectWebSocket();
                initializeECGChart();
            } else {
                charts.ecgChart.resize();
            }
            startEcgAnimation();
            break;
    }
}

// 初始化血壓圖表
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
                    y: { beginAtZero: false }
                }
            }
        });
    } catch (error) {
        console.error('Failed to initialize BP Chart:', error);
    }
}

// 更新血壓圖表
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

// 初始化1分鐘心率圖表
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
                    y: { beginAtZero: false }
                }
            }
        });
    } catch (error) {
        console.error('Failed to initialize HR1min Chart:', error);
    }
}

// 初始化30分鐘心率圖表
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
                    y: { beginAtZero: false }
                }
            }
        });
    } catch (error) {
        console.error('Failed to initialize HR30min Chart:', error);
    }
}

// 更新心率圖表 (通用)
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

// 初始化儀表圖
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
                        riskScore < 30 ? '#10b981' : riskScore < 70 ? '#f59e0b' : '#ef4444',
                        '#e5e7eb'
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

// --- WebSocket Functions ---

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
                ecgDataQueue.push(...data.points);
            }
            if(data.heart_rate){
                document.getElementById('current-heart-rate').textContent = data.heart_rate;
            }
        } catch (e) {
            console.error('Error parsing ECG data:', e);
        }
    };

    ecgSocket.onclose = () => {
        console.log('ECG WebSocket Disconnected');
        ecgSocket = null;
        stopEcgAnimation();
    };

    ecgSocket.onerror = (error) => {
        console.error('WebSocket Error:', error);
        stopEcgAnimation();
    };
}

// --- ECG Chart and Animation ---

function initializeECGChart() {
    const ctx = document.getElementById('ecgChart').getContext('2d');
    const initialData = new Array(MAX_ECG_POINTS).fill(null);
    const initialLabels = new Array(MAX_ECG_POINTS).fill('');

    charts.ecgChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: initialLabels,
            datasets: [{
                label: 'ECG',
                data: initialData,
                borderColor: '#10b981',
                borderWidth: 2,
                pointRadius: 0,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            scales: {
                x: { display: false },
                y: { min: -1.5, max: 2.0 }
            }
        }
    });
    
    if (!document.getElementById('page-ecg').classList.contains('hidden')) {
        startEcgAnimation();
    }
}

function ecgUpdateLoop() {
    if (!charts.ecgChart) return;

    const data = charts.ecgChart.data.datasets[0].data;
    const labels = charts.ecgChart.data.labels;

    const newDataPoint = ecgDataQueue.length > 0 ? ecgDataQueue.shift() : null;

    data.shift();
    labels.shift();

    data.push(newDataPoint);
    labels.push('');

    charts.ecgChart.update('none');
}

function startEcgAnimation() {
    if (ecgAnimationInterval) return;
    ecgAnimationInterval = setInterval(ecgUpdateLoop, ECG_UPDATE_MS);
    
    document.getElementById('ecg-play').classList.add('bg-indigo-600', 'text-white');
    document.getElementById('ecg-play').classList.remove('bg-gray-200', 'text-gray-700');
    document.getElementById('ecg-pause').classList.remove('bg-indigo-600', 'text-white');
    document.getElementById('ecg-pause').classList.add('bg-gray-200', 'text-gray-700');
}

function stopEcgAnimation() {
    if (ecgAnimationInterval) {
        clearInterval(ecgAnimationInterval);
        ecgAnimationInterval = null;
    }
    
    const playBtn = document.getElementById('ecg-play');
    const pauseBtn = document.getElementById('ecg-pause');
    
    if(playBtn && pauseBtn) {
        pauseBtn.classList.add('bg-indigo-600', 'text-white');
        pauseBtn.classList.remove('bg-gray-200', 'text-gray-700');
        playBtn.classList.remove('bg-indigo-600', 'text-white');
        playBtn.classList.add('bg-gray-200', 'text-gray-700');
    }
}

// --- Event Listeners Setup ---

function setupTabListeners() {
    document.getElementById('tab-overview').addEventListener('click', () => switchTab('overview'));
    document.getElementById('tab-bp').addEventListener('click', () => switchTab('bp'));
    document.getElementById('tab-hr1min').addEventListener('click', () => switchTab('hr1min'));
    document.getElementById('tab-hr30min').addEventListener('click', () => switchTab('hr30min'));
    document.getElementById('tab-risk').addEventListener('click', () => switchTab('risk'));
    document.getElementById('tab-ecg').addEventListener('click', () => switchTab('ecg'));
    document.getElementById('tab-health-data').addEventListener('click', () => switchTab('health-data'));
}

function setupEcgControls() {
    document.getElementById('ecg-play').addEventListener('click', startEcgAnimation);
    document.getElementById('ecg-pause').addEventListener('click', stopEcgAnimation);
}

/**
 * 輔助函數：更新按鈕組的 active 樣式
 */
function updateButtonStyles(activeButton, groupId) {
    const buttons = document.querySelectorAll(`[id^="${groupId}"]`);
    
    buttons.forEach(btn => {
        btn.classList.remove('bg-indigo-600', 'text-white');
        btn.classList.add('bg-gray-200', 'text-gray-700');
    });
    
    activeButton.classList.add('bg-indigo-600', 'text-white');
    activeButton.classList.remove('bg-gray-200', 'text-gray-700');
}

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

// --- Health Data Form ---

function setupHealthDataForm() {
    document.getElementById('health-data-form').addEventListener('submit', handleHealthDataSubmit);
}

async function handleHealthDataSubmit(event) {
    event.preventDefault();
    
    const formData = {
        resting_bp: parseInt(document.getElementById('resting-bp-input').value),
        cholesterol: parseInt(document.getElementById('cholesterol-input').value),
        fasting_bs: parseInt(document.getElementById('fasting-bs-input').value)
    };
    
    try {
        const response = await fetchWithAuth('/api/v1/user/health-data', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        console.log('Health data submitted successfully:', response);
        
        // 顯示成功訊息
        const successMsg = document.getElementById('health-data-success');
        successMsg.classList.remove('hidden');
        
        // 3秒後隱藏成功訊息
        setTimeout(() => {
            successMsg.classList.add('hidden');
        }, 3000);
        
        // 清空表單
        document.getElementById('health-data-form').reset();
        
        // 重新獲取健康摘要
        await fetchHealthSummary();
        
    } catch (error) {
        console.error('Health data submission failed:', error);
        alert('健康數據提交失敗，請稍後再試。');
    }
}

// --- Element SDK ---
async function onConfigChange(newConfig) { 
    config = { ...config, ...newConfig }; 
}

function mapToCapabilities(config) { 
    // Element SDK capabilities mapping
}

function mapToEditPanelValues(config) { 
    // Element SDK edit panel values mapping
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', function() {
    // 設置註冊表單監聽器
    document.getElementById('registration-form').addEventListener('submit', handleRegistrationSubmit);
    
    const token = sessionStorage.getItem('apiToken');
    if (token) {
        apiToken = token;
        fetchWithAuth('/api/auth/me')
            .then(data => {
                if (data.is_new_user) {
                    showRegistrationForm();
                } else {
                    initializeApp(data.user);
                }
            })
            .catch(error => {
                console.error("Session restore failed", error);
                sessionStorage.removeItem('apiToken');
                initializeGSI();
            });
    } else {
        initializeGSI();
    }
    
    if (window.elementSdk) {
        window.elementSdk.init({
            defaultConfig,
            onConfigChange,
            mapToCapabilities,
            mapToEditPanelValues
        });
    }
});
