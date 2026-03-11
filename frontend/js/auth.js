// --- Google Authentication Handlers ---

async function handleCredentialResponse(credentialResponse) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/google`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ google_token: credentialResponse.credential })
        });

        if (!response.ok) {
            throw new Error('Backend authentication failed');
        }

        const data = await response.json();
        apiToken = data.api_token;
        sessionStorage.setItem('apiToken', apiToken);
        if (data.user.name)
            defaultConfig.user_name = data.user.name;

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

    if (window.google && window.google.accounts && window.google.accounts.id) {
        google.accounts.id.disableAutoSelect();
    }

    document.getElementById('login-view').classList.remove('hidden');
    document.getElementById('registration-view').classList.add('hidden');
    document.getElementById('dashboard-view').classList.add('hidden');
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
        age: parseInt(document.getElementById('age').value),
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
        const userData = await fetchWithAuth('/api/auth/me');
        await initializeApp(userData.user);

    } catch (error) {
        console.error('Registration failed:', error);
        alert('資料提交失敗，請稍後再試。');
    }
}

function initializeGSI() {
    if (!window.google || !window.google.accounts) {
        console.log("Waiting for Google GSI script to load...");
        setTimeout(initializeGSI, 200);
        return;
    }

    google.accounts.id.initialize({
        client_id: "693422158799-3b30id9m2eo0l4463m4njruokbalk5bd.apps.googleusercontent.com",
        callback: handleCredentialResponse
    });

    google.accounts.id.renderButton(
        document.getElementById("g_id_signin"),
        { theme: "outline", size: "large", text: "signin_with", shape: "rectangular" }
    );
}
