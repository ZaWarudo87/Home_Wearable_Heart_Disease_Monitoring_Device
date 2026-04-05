// --- Main Application Logic ---

async function initializeApp(user) {
    document.getElementById('user-name').textContent = user.name;
    document.getElementById('login-view').classList.add('hidden');
    document.getElementById('registration-view').classList.add('hidden');
    document.getElementById('dashboard-view').classList.remove('hidden');
    // Hide global toggle, use header toggle instead
    const globalToggle = document.getElementById('theme-toggle-global');
    if (globalToggle) globalToggle.style.display = 'none';
    const globalLanguageToggle = document.getElementById('language-toggle-global');
    if (globalLanguageToggle) globalLanguageToggle.style.display = 'none';

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
        protocolEl.textContent = t('connection.protocolInfo', {
            protocol: getCurrentProtocolLabel(),
            apiUrl: getApiBaseUrl()
        });
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
            tunnelHintEl.textContent = t('connection.tunnelReady');
        } else if (tunnelUrl) {
            tunnelLinkEl.textContent = tunnelUrl;
            tunnelLinkEl.href = tunnelUrl;
            tunnelLinkEl.classList.add('pointer-events-none', 'opacity-60');
            tunnelHintEl.textContent = t('connection.tunnelNotReady');
        } else {
            tunnelLinkEl.textContent = t('connection.tunnelLoading');
            tunnelLinkEl.removeAttribute('href');
            tunnelLinkEl.classList.add('pointer-events-none', 'opacity-60');
            tunnelHintEl.textContent = t('connection.tunnelMissing');
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

        const lastUpdateEl = document.getElementById('last-update');
        if (lastUpdateEl) {
            lastUpdateEl.dataset.rawDatetime = data.last_update;
            lastUpdateEl.textContent = `${t('dashboard.lastUpdatePrefix')}${new Date(data.last_update).toLocaleString(getCurrentLanguage())}`;
        }
        document.getElementById('resting-bp').textContent = data.overview.resting_bp == 0 ? '--' : data.overview.resting_bp;
        document.getElementById('avg-hr').textContent = data.overview.avg_hr == 0 ? '--' : data.overview.avg_hr;
        document.getElementById('max-hr').textContent = data.overview.max_hr == 0 ? '--' : data.overview.max_hr;
        document.getElementById('st-slope').textContent = data.overview.st_slope;
        document.getElementById('resting-ecg').textContent = data.overview.resting_ecg;

        // Placeholder for AI advice
        const summaryEl = document.getElementById('health-summary');
        summaryEl.dataset.dynamic = '1';
        summaryEl.dataset.i18nState = 'ai.generating';
        summaryEl.textContent = t('ai.generating');

        (async () => {
            try {
                const advice = await fetchWithAuth('/api/v1/health/advice', {
                    method: 'POST',
                    headers: {
                        'X-Client-Language': getCurrentLanguage()
                    },
                    body: JSON.stringify({
                        overview: data.overview,
                        language: getCurrentLanguage()
                    })
                });

                if (!apiToken) return;

                if (advice.ai_summary) {
                    summaryEl.dataset.i18nState = 'custom';
                    summaryEl.textContent = advice.ai_summary;
                } else {
                    summaryEl.dataset.i18nState = 'ai.empty';
                    summaryEl.textContent = t('ai.empty');
                }
            } catch (e) {
                console.error('Failed to fetch AI advice:', e);
                summaryEl.dataset.i18nState = 'ai.failed';
                summaryEl.textContent = t('ai.failed');
            }
        })();

    } catch (error) {
        console.error('Failed to fetch health summary:', error);
        const summaryEl = document.getElementById('health-summary');
        summaryEl.dataset.i18nState = 'summary.loadFailed';
        summaryEl.textContent = t('summary.loadFailed');
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
