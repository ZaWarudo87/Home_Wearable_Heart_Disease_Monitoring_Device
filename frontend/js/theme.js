// --- Theme Toggle (Light / Dark Mode) ---

(function () {
    const STORAGE_KEY = 'theme-mode';
    const LIGHT_CLASS = 'light-mode';

    // Chart color schemes
    const chartColors = {
        dark: { tick: '#d6d3d1', grid: '#6b5563', gaugeBg: '#3f0d1e' },
        light: { tick: '#57534e', grid: '#e7e5e4', gaugeBg: '#e7e5e4' }
    };

    function isLightMode() {
        return document.documentElement.classList.contains(LIGHT_CLASS);
    }

    function getChartColors() {
        return isLightMode() ? chartColors.light : chartColors.dark;
    }

    function applyTheme(light) {
        if (light) {
            document.documentElement.classList.add(LIGHT_CLASS);
        } else {
            document.documentElement.classList.remove(LIGHT_CLASS);
        }
        updateToggleIcons(light);
        updateAllCharts();
    }

    function updateToggleIcons(light) {
        const icon = light ? '淺' : '深';
        document.querySelectorAll('#theme-toggle, #theme-toggle-global').forEach(btn => {
            if (btn) btn.textContent = icon;
        });
    }

    function updateAllCharts() {
        if (typeof charts === 'undefined') return;
        const colors = getChartColors();

        Object.keys(charts).forEach(key => {
            const chart = charts[key];
            if (!chart) return;

            if (key === 'gaugeChart') {
                // Update gauge background slice
                const ds = chart.data.datasets[0];
                if (ds && ds.backgroundColor && ds.backgroundColor.length > 1) {
                    ds.backgroundColor[1] = colors.gaugeBg;
                }
            }

            // Update scale colors
            if (chart.options && chart.options.scales) {
                Object.keys(chart.options.scales).forEach(axis => {
                    const scale = chart.options.scales[axis];
                    if (scale.ticks) scale.ticks.color = colors.tick;
                    if (scale.grid) scale.grid.color = colors.grid;
                    if (scale.title) scale.title.color = colors.tick;
                });
            }
            chart.update('none');
        });
    }

    function toggle() {
        const light = !isLightMode();
        localStorage.setItem(STORAGE_KEY, light ? 'light' : 'dark');
        applyTheme(light);
    }

    // Initialize on load
    const saved = localStorage.getItem(STORAGE_KEY);
    const preferLight = saved === 'light';
    applyTheme(preferLight);

    // Bind click handlers once DOM is ready
    function bindToggle(id) {
        const btn = document.getElementById(id);
        if (btn) btn.addEventListener('click', toggle);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            bindToggle('theme-toggle');
            bindToggle('theme-toggle-global');
        });
    } else {
        bindToggle('theme-toggle');
        bindToggle('theme-toggle-global');
    }

    // Expose helper for charts to pick up theme colors at creation time
    window.getThemeChartColors = getChartColors;
    window.updateChartsForTheme = updateAllCharts;
})();
