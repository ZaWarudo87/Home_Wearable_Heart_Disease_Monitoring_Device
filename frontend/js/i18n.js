// --- Language Toggle (Chinese / English) ---

(function () {
    const STORAGE_KEY = 'app-language';
    const ZH = 'zh-TW';
    const EN = 'en';

    const messages = {
        [ZH]: {
            'page.title': '心悸寶貝 - 您的心臟健康小幫手',
            'brand.name': '心悸寶貝',
            'brand.subtitle': '您的心臟健康小幫手',
            'toggle.language.title': '切換中文/English',
            'connection.httpsPrompt': '若要透過 HTTPS 直接開啟系統，請使用：',
            'connection.tunnelLoading': '尚未載入 Cloudflare Tunnel 網址',
            'connection.querying': '正在向後端查詢可用的公開網址。',
            'connection.protocolInfo': '目前頁面使用 {protocol} 連線，API 會自動對應到 {apiUrl}',
            'connection.tunnelReady': '這是 Cloudflare Tunnel 網址。',
            'connection.tunnelNotReady': 'Cloudflare Tunnel 尚未啟用或尚未注入環境變數。',
            'connection.tunnelMissing': '如果後端有開啟 /api/cf_url，這裡會顯示可供 HTTPS 連線的公開入口。',
            'login.prompt': '請輸入身份資料',
            'login.name': '姓名',
            'login.namePlaceholder': '請輸入完整姓名',
            'login.birthday': '生日',
            'login.submit': '登入',
            'login.errorName': '請輸入姓名。',
            'login.errorBirthday': '請輸入生日。',
            'login.errorFailed': '登入失敗，請稍後再試。',
            'registration.title': '完善個人資料',
            'registration.subtitle': '請填寫以下資料以建立您的健康檔案',
            'registration.sex': '生理性別',
            'registration.chestPain': '胸痛類別',
            'registration.exerciseAngina': '是否有運動心絞痛的問題',
            'registration.lvh': '是否曾經有被醫生診斷過左心室肥大 (LVH)',
            'registration.submit': '提交資料',
            'registration.cp_ta': '典型心絞痛 (TA)',
            'registration.cp_ata': '非典型心絞痛 (ATA)',
            'registration.cp_nap': '非心絞痛性疼痛 (NAP)',
            'registration.cp_asy': '無症狀 (ASY)',
            'registration.errorSubmit': '資料提交失敗，請稍後再試。',
            'common.select': '請選擇',
            'common.male': '男性',
            'common.female': '女性',
            'common.yes': '是',
            'common.no': '否',
            'common.have': '有',
            'common.none': '沒有',
            'dashboard.welcome': '歡迎回來，',
            'dashboard.lastUpdatePrefix': '最後更新：',
            'dashboard.lastUpdatePlaceholder': '最後更新：...',
            'dashboard.logout': '登出',
            'tab.overview': '總覽',
            'tab.bp': '靜息血壓',
            'tab.hr1': '心率(1分鐘)',
            'tab.hr30': '心率(30分鐘)',
            'tab.risk': '風險評估',
            'tab.ecg': '即時ECG',
            'tab.healthData': '健康數據',
            'period.7d': '7天',
            'period.30d': '30天',
            'period.1h': '1小時',
            'period.6h': '6小時',
            'period.24h': '24小時',
            'section.bpTrend': '靜息血壓趨勢',
            'section.hr1Trend': '平均心率 (1分鐘間隔)',
            'section.hr30Trend': '平均心率 (30分鐘間隔)',
            'section.riskTitle': '整體風險評估',
            'section.riskScore': '風險分數 (0-100)',
            'section.aboutRisk': '關於風險評估',
            'section.aboutRiskBody': '• 風險指數僅供參考<br>• 更多運動 ECG 才能增加準確度，風險指數高可能是因為缺乏運動 ECG 資料！',
            'section.normalRange': '正常範圍參考',
            'normal.bp': '• 正常：收縮壓 < 120 mmHg<br>• 血壓偏高：120-129 mmHg<br>• 高血壓第一期：130-139 mmHg<br>• 高血壓第二期：>= 140 mmHg',
            'normal.hr1': '• 靜息心率：60-100 bpm<br>• 運動心率：最大心率的 50-85%<br>• 您的最大心率約：175 bpm (220-年齡)<br>• 建議運動心率：88-149 bpm',
            'normal.hr30': '• 日間平均心率：70-90 bpm<br>• 夜間平均心率：50-70 bpm<br>• 心率變異性：正常範圍內波動<br>• 異常警示：持續 > 100 bpm 或 < 50 bpm',
            'overview.restingBp.sm': '靜息血壓',
            'overview.restingBp.xs': 'Resting BP',
            'overview.avgHr.sm': '平均心率',
            'overview.avgHr.xs': 'Average HR',
            'overview.maxHr.sm': '最大心率',
            'overview.maxHr.xs': 'Max HR',
            'overview.stSlope.sm': 'ST 斜率',
            'overview.stSlope.xs': 'ST slope',
            'overview.restingEcg.sm': '靜息 ECG',
            'overview.restingEcg.xs': 'Resting ECG',
            'overview.af.sm': '心房顫動',
            'overview.af.xs': 'AF Detection',
            'ecg.play': '播放',
            'ecg.pause': '暫停',
            'ecg.download': '下載 ECG 圖片',
            'ecg.restMode': '靜息模式',
            'ecg.exerciseMode': '運動模式',
            'ecg.heartRate': '心率',
            'ecg.liveChart': '即時ECG波形圖',
            'ecg.monitoring': 'ECG 監測',
            'ecg.monitoringBody': '• 接收來自後端的即時ECG波形圖數據。<br>• 玫瑰色線條代表即時心跳數據流。',
            'ecg.xAxisTime': '時間 (秒)',
            'ecg.recordTitle': 'ECG 心電圖紀錄',
            'ecg.downloadAt': '下載時間',
            'ecg.dataLength': '資料長度',
            'ecg.sampleCount': '取樣點數',
            'ecg.seconds': '秒',
            'health.success': '✓ 健康數據已成功更新！',
            'health.errorSubmit': '健康數據提交失敗，請稍後再試。',
            'healthData.title': '更新健康數據',
            'healthData.infoTitle': '數據說明',
            'healthData.infoBody': '• 請定期更新您的健康數據，以獲得更準確的健康評估。<br>• 建議每週至少更新一次數據。<br>• 數據將用於 AI 健康分析和風險評估。',
            'healthData.restingBp': '靜息血壓 (mmHg)',
            'healthData.cholesterol': '血清膽固醇 (mm/dl)',
            'healthData.fastingBs': '空腹血糖 (mg/dl)',
            'healthData.restingBpPlaceholder': '例如: 120',
            'healthData.cholesterolPlaceholder': '例如: 200',
            'healthData.fastingBsPlaceholder': '例如: 100',
            'healthData.restingBpRange': '正常範圍: 90-140 mmHg',
            'healthData.cholesterolRange': '正常範圍: 低於 200 mm/dl',
            'healthData.fastingBsRange': '正常範圍: 70-100 mg/dl (空腹)',
            'healthData.submit': '提交數據',
            'ai.title': 'AI 健康建議',
            'ai.loading': '正在載入建議...',
            'ai.generating': '正在產生 AI 健康建議...',
            'ai.empty': '（沒有取得建議）',
            'ai.failed': 'AI 建議取得失敗，請稍後再試。',
            'summary.loadFailed': '資料載入失敗。',
            'chart.bp': '靜息血壓',
            'chart.hrAvg': '平均心率',
            'af.risk': '有風險',
            'af.noRisk': '無風險'
        },
        [EN]: {
            'page.title': 'Heartbeat Buddy - Your Heart Health Assistant',
            'brand.name': 'Heartbeat Buddy',
            'brand.subtitle': 'Your Heart Health Assistant',
            'toggle.language.title': 'Switch Chinese/English',
            'connection.httpsPrompt': 'To open this system directly via HTTPS, use:',
            'connection.tunnelLoading': 'Cloudflare Tunnel URL not loaded yet',
            'connection.querying': 'Querying backend for an available public URL.',
            'connection.protocolInfo': 'This page is using {protocol}; API will map automatically to {apiUrl}',
            'connection.tunnelReady': 'This is the Cloudflare Tunnel URL.',
            'connection.tunnelNotReady': 'Cloudflare Tunnel is not enabled or env var is not injected yet.',
            'connection.tunnelMissing': 'If backend enables /api/cf_url, the public HTTPS entry will be shown here.',
            'login.prompt': 'Please enter your identity information',
            'login.name': 'Name',
            'login.namePlaceholder': 'Enter your full name',
            'login.birthday': 'Birthday',
            'login.submit': 'Sign in',
            'login.errorName': 'Please enter your name.',
            'login.errorBirthday': 'Please enter your birthday.',
            'login.errorFailed': 'Sign-in failed. Please try again later.',
            'registration.title': 'Complete Profile',
            'registration.subtitle': 'Fill in the form below to create your health profile',
            'registration.sex': 'Biological Sex',
            'registration.chestPain': 'Chest Pain Type',
            'registration.exerciseAngina': 'Do you have exercise-induced angina?',
            'registration.lvh': 'Have you ever been diagnosed with LVH by a doctor?',
            'registration.submit': 'Submit Profile',
            'registration.cp_ta': 'Typical Angina (TA)',
            'registration.cp_ata': 'Atypical Angina (ATA)',
            'registration.cp_nap': 'Non-anginal Pain (NAP)',
            'registration.cp_asy': 'Asymptomatic (ASY)',
            'registration.errorSubmit': 'Profile submission failed. Please try again later.',
            'common.select': 'Please select',
            'common.male': 'Male',
            'common.female': 'Female',
            'common.yes': 'Yes',
            'common.no': 'No',
            'common.have': 'Yes',
            'common.none': 'No',
            'dashboard.welcome': 'Welcome back, ',
            'dashboard.lastUpdatePrefix': 'Last update: ',
            'dashboard.lastUpdatePlaceholder': 'Last update: ...',
            'dashboard.logout': 'Sign out',
            'tab.overview': 'Overview',
            'tab.bp': 'Resting BP',
            'tab.hr1': 'Heart Rate (1 min)',
            'tab.hr30': 'Heart Rate (30 min)',
            'tab.risk': 'Risk Assessment',
            'tab.ecg': 'Live ECG',
            'tab.healthData': 'Health Data',
            'period.7d': '7 days',
            'period.30d': '30 days',
            'period.1h': '1 hour',
            'period.6h': '6 hours',
            'period.24h': '24 hours',
            'section.bpTrend': 'Resting BP Trend',
            'section.hr1Trend': 'Average Heart Rate (1-minute interval)',
            'section.hr30Trend': 'Average Heart Rate (30-minute interval)',
            'section.riskTitle': 'Overall Risk Assessment',
            'section.riskScore': 'Risk Score (0-100)',
            'section.aboutRisk': 'About Risk Assessment',
            'section.aboutRiskBody': '• The risk score is for reference only.<br>• More exercise ECG data improves accuracy. A high score may be caused by insufficient exercise ECG data.',
            'section.normalRange': 'Normal Range Reference',
            'normal.bp': '• Normal: systolic < 120 mmHg<br>• Elevated: 120-129 mmHg<br>• Hypertension Stage 1: 130-139 mmHg<br>• Hypertension Stage 2: >= 140 mmHg',
            'normal.hr1': '• Resting HR: 60-100 bpm<br>• Exercise HR: 50-85% of max HR<br>• Your estimated max HR: 175 bpm (220-age)<br>• Suggested exercise HR: 88-149 bpm',
            'normal.hr30': '• Daytime average HR: 70-90 bpm<br>• Nighttime average HR: 50-70 bpm<br>• HRV: fluctuates within normal range<br>• Alert: sustained > 100 bpm or < 50 bpm',
            'overview.restingBp.sm': 'Resting BP',
            'overview.restingBp.xs': '',
            'overview.avgHr.sm': 'Average HR',
            'overview.avgHr.xs': '',
            'overview.maxHr.sm': 'Max HR',
            'overview.maxHr.xs': '',
            'overview.stSlope.sm': 'ST Slope',
            'overview.stSlope.xs': '',
            'overview.restingEcg.sm': 'Resting ECG',
            'overview.restingEcg.xs': '',
            'overview.af.sm': 'AF Detection',
            'overview.af.xs': '',
            'ecg.play': 'Play',
            'ecg.pause': 'Pause',
            'ecg.download': 'Download ECG Image',
            'ecg.restMode': 'Rest Mode',
            'ecg.exerciseMode': 'Exercise Mode',
            'ecg.heartRate': 'Heart Rate',
            'ecg.liveChart': 'Live ECG Waveform',
            'ecg.monitoring': 'ECG Monitoring',
            'ecg.monitoringBody': '• Receives real-time ECG waveform data from backend.<br>• The rose-colored line represents the live heartbeat stream.',
            'ecg.xAxisTime': 'Time (s)',
            'ecg.recordTitle': 'ECG Recording',
            'ecg.downloadAt': 'Downloaded at',
            'ecg.dataLength': 'Data length',
            'ecg.sampleCount': 'Samples',
            'ecg.seconds': 'sec',
            'health.success': '✓ Health data updated successfully!',
            'health.errorSubmit': 'Health data submission failed. Please try again later.',
            'healthData.title': 'Update Health Data',
            'healthData.infoTitle': 'Data Notes',
            'healthData.infoBody': '• Update your health data regularly for a more accurate assessment.<br>• It is recommended to update at least once per week.<br>• Data is used for AI health analysis and risk assessment.',
            'healthData.restingBp': 'Resting BP (mmHg)',
            'healthData.cholesterol': 'Serum Cholesterol (mm/dl)',
            'healthData.fastingBs': 'Fasting Blood Sugar (mg/dl)',
            'healthData.restingBpPlaceholder': 'e.g. 120',
            'healthData.cholesterolPlaceholder': 'e.g. 200',
            'healthData.fastingBsPlaceholder': 'e.g. 100',
            'healthData.restingBpRange': 'Normal range: 90-140 mmHg',
            'healthData.cholesterolRange': 'Normal range: below 200 mm/dl',
            'healthData.fastingBsRange': 'Normal range: 70-100 mg/dl (fasting)',
            'healthData.submit': 'Submit Data',
            'ai.title': 'AI Health Advice',
            'ai.loading': 'Loading recommendations...',
            'ai.generating': 'Generating AI health advice...',
            'ai.empty': '(No recommendation received)',
            'ai.failed': 'Failed to get AI advice. Please try again later.',
            'summary.loadFailed': 'Failed to load data.',
            'chart.bp': 'Resting BP',
            'chart.hrAvg': 'Average HR',
            'af.risk': 'At Risk',
            'af.noRisk': 'No Risk'
        }
    };

    let currentLanguage = localStorage.getItem(STORAGE_KEY) || ZH;
    if (![ZH, EN].includes(currentLanguage)) {
        currentLanguage = ZH;
    }

    function t(key, vars = {}) {
        const locale = messages[currentLanguage] || messages[ZH];
        const fallback = messages[ZH] || {};
        let text = locale[key] || fallback[key] || key;
        Object.keys(vars).forEach((name) => {
            text = text.replace(`{${name}}`, vars[name]);
        });
        return text;
    }

    function setText(selector, key) {
        const el = document.querySelector(selector);
        if (el) el.textContent = t(key);
    }

    function setOptionText(selectId, value, key) {
        const option = document.querySelector(`#${selectId} option[value="${value}"]`);
        if (option) option.textContent = t(key);
    }

    function applyStaticTranslations() {
        document.documentElement.lang = currentLanguage;
        document.title = t('page.title');

        setText('#login-view h1', 'brand.name');
        setText('#login-view h2', 'brand.subtitle');
        setText('#registration-view h1', 'registration.title');
        setText('#registration-view p.text-stone-400.mb-6', 'registration.subtitle');

        setText('#cf-url p.text-sm', 'connection.httpsPrompt');
        if (typeof window.updateConnectionInfoBanner === 'function') {
            window.updateConnectionInfoBanner();
        } else {
            const tunnelLinkEl = document.getElementById('cloudflare-tunnel-link');
            const tunnelHintEl = document.getElementById('cloudflare-tunnel-hint');
            if (tunnelLinkEl && tunnelHintEl) {
                const hasLoadedUrl = !!(tunnelLinkEl.getAttribute('href') && tunnelLinkEl.getAttribute('href') !== '#');
                if (!hasLoadedUrl) {
                    tunnelLinkEl.textContent = t('connection.tunnelLoading');
                    tunnelHintEl.textContent = t('connection.querying');
                }
            }
        }

        setText('#login-view p.text-stone-600.mb-6', 'login.prompt');
        const loginLabels = document.querySelectorAll('#login-form label');
        if (loginLabels[0]) loginLabels[0].textContent = t('login.name');
        if (loginLabels[1]) loginLabels[1].textContent = t('login.birthday');
        setText('#login-form button[type="submit"]', 'login.submit');

        const nameInput = document.getElementById('name');
        if (nameInput) nameInput.placeholder = t('login.namePlaceholder');

        const regLabels = document.querySelectorAll('#registration-form label');
        if (regLabels[0]) regLabels[0].textContent = t('registration.sex');
        if (regLabels[1]) regLabels[1].textContent = t('registration.chestPain');
        if (regLabels[2]) regLabels[2].textContent = t('registration.exerciseAngina');
        if (regLabels[3]) regLabels[3].textContent = t('registration.lvh');
        setText('#registration-form button[type="submit"]', 'registration.submit');

        setOptionText('sex', '', 'common.select');
        setOptionText('sex', 'M', 'common.male');
        setOptionText('sex', 'F', 'common.female');
        setOptionText('chest-pain-type', '', 'common.select');
        setOptionText('chest-pain-type', 'TA', 'registration.cp_ta');
        setOptionText('chest-pain-type', 'ATA', 'registration.cp_ata');
        setOptionText('chest-pain-type', 'NAP', 'registration.cp_nap');
        setOptionText('chest-pain-type', 'ASY', 'registration.cp_asy');
        setOptionText('exercise-angina', '', 'common.select');
        setOptionText('exercise-angina', 'Y', 'common.yes');
        setOptionText('exercise-angina', 'N', 'common.no');
        setOptionText('lvh', '', 'common.select');
        setOptionText('lvh', 'Y', 'common.have');
        setOptionText('lvh', 'N', 'common.none');

        setText('#dashboard-title', 'brand.name');
        setText('#dashboard-view h2.text-lg', 'brand.subtitle');
        setText('#logout-button', 'dashboard.logout');

        setText('#tab-overview', 'tab.overview');
        setText('#tab-bp', 'tab.bp');
        setText('#tab-hr1min', 'tab.hr1');
        setText('#tab-hr30min', 'tab.hr30');
        setText('#tab-risk', 'tab.risk');
        setText('#tab-ecg', 'tab.ecg');
        setText('#tab-health-data', 'tab.healthData');

        setText('#bp-period-7', 'period.7d');
        setText('#bp-period-30', 'period.30d');
        setText('#hr1-period-1h', 'period.1h');
        setText('#hr1-period-6h', 'period.6h');
        setText('#hr30-period-24h', 'period.24h');
        setText('#hr30-period-7d', 'period.7d');

        setText('#page-bp h3.text-lg', 'section.bpTrend');
        setText('#page-hr1min h3.text-lg', 'section.hr1Trend');
        setText('#page-hr30min h3.text-lg', 'section.hr30Trend');
        setText('#page-risk h3.text-lg', 'section.riskTitle');
        setText('#page-risk p.text-sm.text-stone-300', 'section.riskScore');
        setText('#page-risk h4.font-semibold.text-purple-100', 'section.aboutRisk');
        applyNormalRangeTranslations();
        applySupplementalInfoTranslations();

        setText('#ecg-play', 'ecg.play');
        setText('#ecg-pause', 'ecg.pause');
        setText('#ecg-download', 'ecg.download');
        setText('#page-ecg h3.text-lg', 'ecg.liveChart');
        setText('#page-ecg h4.font-semibold.text-purple-100', 'ecg.monitoring');

        setText('#page-health-data h3.text-lg', 'healthData.title');
        const healthLabels = document.querySelectorAll('#health-data-form label');
        if (healthLabels[0]) healthLabels[0].textContent = t('healthData.restingBp');
        if (healthLabels[1]) healthLabels[1].textContent = t('healthData.cholesterol');
        if (healthLabels[2]) healthLabels[2].textContent = t('healthData.fastingBs');
        applyHealthInputTranslations();
        setText('#health-data-form button[type="submit"]', 'healthData.submit');
        setText('main > div.bg-rose-950.rounded-lg.shadow-lg.p-6 > h3.text-lg', 'ai.title');

        const heartRateLabel = document.querySelector('#page-ecg span.text-sm.font-medium.text-rose-300');
        if (heartRateLabel) {
            heartRateLabel.childNodes[0].nodeValue = `${t('ecg.heartRate')}: `;
        }

        const successEl = document.querySelector('#health-data-success p');
        if (successEl) successEl.textContent = t('health.success');

        applyAiSummaryState();
        applyOverviewTranslations();

        applyDashboardMetaPlaceholders();
        updateLanguageToggleButtons();
    }

    function applyOverviewTranslations() {
        const mappings = [
            { id: 'resting-bp', sm: 'overview.restingBp.sm', xs: 'overview.restingBp.xs' },
            { id: 'avg-hr', sm: 'overview.avgHr.sm', xs: 'overview.avgHr.xs' },
            { id: 'max-hr', sm: 'overview.maxHr.sm', xs: 'overview.maxHr.xs' },
            { id: 'st-slope', sm: 'overview.stSlope.sm', xs: 'overview.stSlope.xs' },
            { id: 'resting-ecg', sm: 'overview.restingEcg.sm', xs: 'overview.restingEcg.xs' },
            { id: 'af-detected', sm: 'overview.af.sm', xs: 'overview.af.xs' }
        ];

        mappings.forEach((item) => {
            const valueEl = document.getElementById(item.id);
            if (!valueEl) return;
            const card = valueEl.closest('div.bg-rose-950.rounded-lg.shadow-lg.p-6');
            if (!card) return;
            const smallTexts = card.querySelectorAll('p.text-xs');
            const titleEl = card.querySelector('p.text-sm');
            const subtitleEl = smallTexts[0];
            if (titleEl) titleEl.textContent = t(item.sm);
            if (subtitleEl) subtitleEl.textContent = t(item.xs);
        });
    }

    function applyNormalRangeTranslations() {
        const bpTitle = document.querySelector('#page-bp .bg-purple-950 h4');
        const bpBody = document.querySelector('#page-bp .bg-purple-950 p');
        const hr1Title = document.querySelector('#page-hr1min .bg-purple-950 h4');
        const hr1Body = document.querySelector('#page-hr1min .bg-purple-950 p');
        const hr30Title = document.querySelector('#page-hr30min .bg-purple-950 h4');
        const hr30Body = document.querySelector('#page-hr30min .bg-purple-950 p');

        if (bpTitle) bpTitle.textContent = t('section.normalRange');
        if (hr1Title) hr1Title.textContent = t('section.normalRange');
        if (hr30Title) hr30Title.textContent = t('section.normalRange');
        if (bpBody) bpBody.innerHTML = t('normal.bp');
        if (hr1Body) hr1Body.innerHTML = t('normal.hr1');
        if (hr30Body) hr30Body.innerHTML = t('normal.hr30');
    }

    function applyHealthInputTranslations() {
        const restingInput = document.getElementById('resting-bp-input');
        const cholesterolInput = document.getElementById('cholesterol-input');
        const fastingInput = document.getElementById('fasting-bs-input');
        if (restingInput) restingInput.placeholder = t('healthData.restingBpPlaceholder');
        if (cholesterolInput) cholesterolInput.placeholder = t('healthData.cholesterolPlaceholder');
        if (fastingInput) fastingInput.placeholder = t('healthData.fastingBsPlaceholder');

        const hints = document.querySelectorAll('#health-data-form p.text-xs.text-stone-400');
        if (hints[0]) hints[0].textContent = t('healthData.restingBpRange');
        if (hints[1]) hints[1].textContent = t('healthData.cholesterolRange');
        if (hints[2]) hints[2].textContent = t('healthData.fastingBsRange');
    }

    function applySupplementalInfoTranslations() {
        const riskBody = document.querySelector('#page-risk .bg-purple-950 p.text-sm.text-purple-200');
        if (riskBody) riskBody.innerHTML = t('section.aboutRiskBody');

        const ecgBody = document.querySelector('#page-ecg .bg-purple-950 p.text-sm.text-purple-200');
        if (ecgBody) ecgBody.innerHTML = t('ecg.monitoringBody');

        const healthInfoTitle = document.querySelector('#page-health-data .bg-purple-950 h4.font-semibold.text-purple-100');
        if (healthInfoTitle) healthInfoTitle.textContent = t('healthData.infoTitle');

        const healthInfoBody = document.querySelector('#page-health-data .bg-purple-950 p.text-sm.text-purple-200');
        if (healthInfoBody) healthInfoBody.innerHTML = t('healthData.infoBody');
    }

    function applyAiSummaryState() {
        const summaryEl = document.getElementById('health-summary');
        if (!summaryEl) return;

        const state = summaryEl.dataset.i18nState;
        if (!state) {
            summaryEl.dataset.i18nState = 'ai.loading';
            summaryEl.textContent = t('ai.loading');
            return;
        }

        if (state === 'custom') {
            return;
        }

        summaryEl.textContent = t(state);
    }

    function applyDashboardMetaPlaceholders() {
        const userName = document.getElementById('user-name');
        const lastUpdateEl = document.getElementById('last-update');
        if (!userName || !lastUpdateEl) return;

        const parent = userName.parentElement;
        if (!parent) return;

        const raw = lastUpdateEl.dataset.rawDatetime;
        if (raw) {
            lastUpdateEl.textContent = `${t('dashboard.lastUpdatePrefix')}${new Date(raw).toLocaleString(currentLanguage)}`;
        } else {
            lastUpdateEl.textContent = t('dashboard.lastUpdatePlaceholder');
        }

        const firstNode = parent.firstChild;
        if (firstNode && firstNode.nodeType === Node.TEXT_NODE) {
            firstNode.nodeValue = t('dashboard.welcome');
        } else {
            parent.insertBefore(document.createTextNode(t('dashboard.welcome')), userName);
        }
    }

    function updateLanguageToggleButtons() {
        const label = currentLanguage === ZH ? '中' : 'EN';
        const title = t('toggle.language.title');
        document.querySelectorAll('#language-toggle, #language-toggle-global').forEach((btn) => {
            if (!btn) return;
            btn.textContent = label;
            btn.title = title;
        });
    }

    function applyLanguage(lang) {
        currentLanguage = lang === EN ? EN : ZH;
        localStorage.setItem(STORAGE_KEY, currentLanguage);
        applyStaticTranslations();

        if (typeof window.updateChartsForLanguage === 'function') {
            window.updateChartsForLanguage();
        }

        if (typeof window.updateChartsForTheme === 'function') {
            window.updateChartsForTheme();
        }
    }

    function toggleLanguage() {
        applyLanguage(currentLanguage === ZH ? EN : ZH);
    }

    function bindToggle(id) {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', toggleLanguage);
        }
    }

    window.t = t;
    window.getCurrentLanguage = () => currentLanguage;
    window.setLanguage = applyLanguage;

    function initialize() {
        bindToggle('language-toggle');
        bindToggle('language-toggle-global');
        applyLanguage(currentLanguage);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
})();
