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

function updateConnectionInfoBanner() {
    const connectionCard = document.getElementById('cf-url');
    const protocolEl = document.getElementById('connection-protocol');
    const apiUrlEl = document.getElementById('connection-api-url');
    const tunnelLinkEl = document.getElementById('cloudflare-tunnel-link');
    const tunnelHintEl = document.getElementById('cloudflare-tunnel-hint');
    const shouldShowConnectionInfo = window.location.protocol === 'http:';

    if (connectionCard) {
        connectionCard.style.display = shouldShowConnectionInfo ? '' : 'none';
    }

    if (!shouldShowConnectionInfo) {
        return;
    }

    if (protocolEl) {
        protocolEl.textContent = `目前頁面使用 ${getCurrentProtocolLabel()} 連線，API 會自動對應到 ${getApiBaseUrl()}`;
    }

    if (apiUrlEl) {
        apiUrlEl.textContent = getApiBaseUrl();
    }

    if (tunnelLinkEl && tunnelHintEl) {
        const tunnelUrl = getCloudflareTunnelUrl();
        const hasPublicTunnel = tunnelUrl && !isLocalTunnelUrl(tunnelUrl);

        if (hasPublicTunnel) {
            tunnelLinkEl.textContent = tunnelUrl;
            tunnelLinkEl.href = tunnelUrl;
            tunnelLinkEl.classList.remove('pointer-events-none', 'opacity-60');
            tunnelHintEl.textContent = '這是 Cloudflare Tunnel 網址。';
        } else if (tunnelUrl) {
            tunnelLinkEl.textContent = tunnelUrl;
            tunnelLinkEl.href = tunnelUrl;
            tunnelLinkEl.classList.add('pointer-events-none', 'opacity-60');
            tunnelHintEl.textContent = 'Cloudflare Tunnel 尚未啟用或尚未注入環境變數。';
        } else {
            tunnelLinkEl.textContent = '尚未載入 Cloudflare Tunnel 網址';
            tunnelLinkEl.removeAttribute('href');
            tunnelLinkEl.classList.add('pointer-events-none', 'opacity-60');
            tunnelHintEl.textContent = '如果後端有開啟 /api/cf_url，這裡會顯示可供 HTTPS 連線的公開入口。';
        }
    }
}

async function initializeConnectionInfo() {
    updateConnectionInfoBanner();
    if (window.location.protocol === 'http:') {
        await refreshBackendConnectionInfo();
    } else {
        setCloudflareTunnelUrl(null);
    }
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
    initializeLoginForm();
    initializeConnectionInfo();

    const token = sessionStorage.getItem('apiToken');
    if (token) {
        apiToken = token;
        fetchWithAuth('/api/v1/auth/me')
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
                handleSignOut();
            });
    } else {
        handleSignOut();
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
