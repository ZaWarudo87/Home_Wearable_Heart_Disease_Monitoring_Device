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

    const fullUrl = buildApiUrl(url);

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

async function refreshBackendConnectionInfo() {
    try {
        const response = await fetch(buildApiUrl('/api/cf_url'));
        if (!response.ok) {
            throw new Error(`Failed to load tunnel URL: ${response.status}`);
        }

        const data = await response.json();
        setCloudflareTunnelUrl(data.cf_url || null);
        updateConnectionInfoBanner();
    } catch (error) {
        console.error('Failed to refresh backend connection info:', error);
        setCloudflareTunnelUrl(null);
        updateConnectionInfoBanner();
    }
}

function getWebSocketUrl(path) {
    const url = new URL(path, getApiBaseUrl());
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    return url.toString();
}
