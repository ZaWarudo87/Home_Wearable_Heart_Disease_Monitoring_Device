// --- Name + Birthday Login Handlers ---

async function handleLoginSubmit(event) {
    event.preventDefault();

    const name = (document.getElementById('name').value || '').trim();
    const birthday = (document.getElementById('birthday').value || '').trim();

    if (!name) {
        alert('請輸入姓名。');
        return;
    }
    if (!birthday) {
        alert('請輸入生日。');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, birthday })
        });

        if (!response.ok) {
            throw new Error('Backend authentication failed');
        }

        const data = await response.json();
        apiToken = data.token || (data.user && data.user.token);
        sessionStorage.setItem('apiToken', apiToken);

        if (data.user && data.user.name) {
            defaultConfig.user_name = data.user.name;
        }

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

    document.getElementById('login-view').classList.remove('hidden');
    document.getElementById('registration-view').classList.add('hidden');
    document.getElementById('dashboard-view').classList.add('hidden');

    const globalToggle = document.getElementById('theme-toggle-global');
    if (globalToggle) globalToggle.style.display = 'block';
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
        chest_pain_type: document.getElementById('chest-pain-type').value,
        exercise_angina: document.getElementById('exercise-angina').value === 'Y',
        resting_ecg: document.getElementById('lvh').value === 'Y'
    };

    try {
        const response = await fetchWithAuth('/api/v1/user/profile', {
            method: 'POST',
            body: JSON.stringify(formData)
        });

        console.log('Registration successful:', response);
        const userData = await fetchWithAuth('/api/v1/auth/me');
        await initializeApp(userData.user);

    } catch (error) {
        console.error('Registration failed:', error);
        alert('資料提交失敗，請稍後再試。');
    }
}

function initializeLoginForm() {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLoginSubmit);
    }
}
