// --- Health Data Form ---

function setupHealthDataForm() {
    document.getElementById('health-data-form').addEventListener('submit', handleHealthDataSubmit);
}

async function handleHealthDataSubmit(event) {
    event.preventDefault();

    const formData = {
        resting_bp: parseInt(document.getElementById('resting-bp-input').value),
        cholesterol: parseInt(document.getElementById('cholesterol-input').value),
        fasting_bs: parseInt(document.getElementById('fasting-bs-input').value)
    };

    try {
        const response = await fetchWithAuth('/api/v1/user/health-data', {
            method: 'POST',
            body: JSON.stringify(formData)
        });

        console.log('Health data submitted successfully:', response);

        // Show success message
        const successMsg = document.getElementById('health-data-success');
        successMsg.classList.remove('hidden');
        setTimeout(() => {
            successMsg.classList.add('hidden');
        }, 3000);

        // Clear form inputs
        document.getElementById('health-data-form').reset();
        await fetchHealthSummary();
    } catch (error) {
        console.error('Health data submission failed:', error);
        alert('健康數據提交失敗，請稍後再試。');
    }
}
