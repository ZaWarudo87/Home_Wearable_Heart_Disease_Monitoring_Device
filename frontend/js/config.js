// --- Configuration and Shared State ---

const defaultConfig = {
    user_name: "王小明",
    dashboard_title: "心臟健康監測系統",
    summary_text: "目前心臟狀況穩定...",
    background_color: "#1c1917",
    surface_color: "#4c0519",
    text_color: "#fecdd3",
    primary_color: "#db2777",
    accent_color: "#f43f5e"
};
let config = { ...defaultConfig };

let charts = {};
let apiToken = null;

// --- API Base URL ---
const FALLBACK_API_BASE_URL = "http://localhost:39244/";

function normalizeApiBaseUrl(value) {
    if (!value) return FALLBACK_API_BASE_URL;
    return value.endsWith('/') ? value : `${value}/`;
}

function resolveDefaultApiBaseUrl() {
    const { origin, protocol } = window.location;
    if ((protocol === 'http:' || protocol === 'https:') && origin && origin !== 'null') {
        return normalizeApiBaseUrl(origin);
    }

    return FALLBACK_API_BASE_URL;
}

let apiBaseUrl = resolveDefaultApiBaseUrl();
let cloudflareTunnelUrl = null;

function setApiBaseUrl(value) {
    apiBaseUrl = normalizeApiBaseUrl(value);
}

function getApiBaseUrl() {
    return apiBaseUrl;
}

function buildApiUrl(path) {
    return new URL(path, getApiBaseUrl()).toString();
}

function getCurrentProtocolLabel() {
    return window.location.protocol === 'https:' ? 'HTTPS' : 'HTTP';
}

function isLocalTunnelUrl(value) {
    if (!value) return true;
    return /localhost|127\.0\.0\.1|\[::1\]/i.test(value);
}

function setCloudflareTunnelUrl(value) {
    cloudflareTunnelUrl = value || null;
}

function getCloudflareTunnelUrl() {
    return cloudflareTunnelUrl;
}
