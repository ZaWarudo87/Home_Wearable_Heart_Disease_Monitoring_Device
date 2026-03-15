// --- Main Application Logic ---

async function initializeApp(user) {
    document.getElementById('user-name').textContent = user.name;
    document.getElementById('login-view').classList.add('hidden');
    document.getElementById('registration-view').classList.add('hidden');
    document.getElementById('dashboard-view').classList.remove('hidden');
    // Hide global toggle, use header toggle instead
    const globalToggle = document.getElementById('theme-toggle-global');
    if (globalToggle) globalToggle.style.display = 'none';

    setupTabListeners();
    setupPeriodListeners();
    setupEcgControls();
    setupHealthDataForm();
    document.getElementById('logout-button').addEventListener('click', handleSignOut);

    await fetchHealthSummary();

    // Default 'overview'
    document.getElementById('tab-overview').classList.add('bg-rose-800', 'text-rose-100');
    document.getElementById('tab-overview').classList.remove('bg-rose-950', 'text-stone-400');
    document.getElementById('page-overview').classList.remove('hidden');
}

async function fetchHealthSummary() {
    try {
        const data = await fetchWithAuth('/api/v1/health/summary');

        document.getElementById('last-update').textContent =
            `最後更新：${new Date(data.last_update).toLocaleString()}`;
        document.getElementById('resting-bp').textContent = data.overview.resting_bp == 0 ? '--' : data.overview.resting_bp;
        document.getElementById('avg-hr').textContent = data.overview.avg_hr == 0 ? '--' : data.overview.avg_hr;
        document.getElementById('max-hr').textContent = data.overview.max_hr == 0 ? '--' : data.overview.max_hr;
        document.getElementById('st-slope').textContent = data.overview.st_slope;
        document.getElementById('resting-ecg').textContent = data.overview.resting_ecg;

        // Placeholder for AI advice
        const summaryEl = document.getElementById('health-summary');
        summaryEl.textContent = '正在產生 AI 健康建議...';

        (async () => {
            try {
                const advice = await fetchWithAuth('/api/v1/health/advice', {
                    method: 'POST',
                    body: JSON.stringify({ overview: data.overview })
                });

                if (!apiToken) return;

                summaryEl.textContent = advice.ai_summary || '（沒有取得建議）';
            } catch (e) {
                console.error('Failed to fetch AI advice:', e);
                summaryEl.textContent = 'AI 建議取得失敗，請稍後再試。';
            }
        })();

    } catch (error) {
        console.error('Failed to fetch health summary:', error);
        document.getElementById('health-summary').textContent = '資料載入失敗。';
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

    // --- DEMO: skip Google login ---
    // apiToken = "DEMO_TOKEN";
    // sessionStorage.setItem("apiToken", apiToken);
    // initializeApp({ name: "Demo User" });

    if (window.elementSdk) {
        window.elementSdk.init({
            defaultConfig,
            onConfigChange,
            mapToCapabilities,
            mapToEditPanelValues
        });
    }
});
