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
const API_BASE_URL = "https://looksmart-demographic-clients-healthy.trycloudflare.com";
