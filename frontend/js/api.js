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
