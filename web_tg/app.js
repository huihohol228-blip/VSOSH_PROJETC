// Telegram Web App API
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Настройка цвета кнопки
tg.setHeaderColor('#667eea');
tg.setBackgroundColor('#ffffff');

// API URL - автоматически определяется из текущего URL
// При работе через ngrok будет использовать HTTPS URL
const API_BASE = window.location.origin + '/api';

// DOM элементы
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');
const loadingOverlay = document.getElementById('loading-overlay');
const resultsContainer = document.getElementById('results-container');

// Табы
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetTab = btn.dataset.tab;
        
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        tabContents.forEach(content => {
            content.classList.remove('active');
            if (content.id === `${targetTab}-tab`) {
                content.classList.add('active');
            }
        });
    });
});

// Проверка текста
const textInput = document.getElementById('text-input');
const checkTextBtn = document.getElementById('check-text-btn');

checkTextBtn.addEventListener('click', async () => {
    const text = textInput.value.trim();
    
    if (!text) {
        showError('Пожалуйста, введите текст для проверки');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/predict/text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text })
        });
        
        const data = await response.json();
        hideLoading();
        
        if (data.success) {
            displayResults(data);
            tg.HapticFeedback.notificationOccurred('success');
        } else {
            showError(data.error || 'Произошла ошибка');
            tg.HapticFeedback.notificationOccurred('error');
        }
    } catch (error) {
        hideLoading();
        showError('Ошибка подключения к серверу');
        tg.HapticFeedback.notificationOccurred('error');
        console.error(error);
    }
});

// Проверка изображения
const imageInput = document.getElementById('image-input');
const imageUploadArea = document.getElementById('image-upload-area');
const imagePreview = document.getElementById('image-preview');
const checkImageBtn = document.getElementById('check-image-btn');

setupFileUpload(imageUploadArea, imageInput, imagePreview, checkImageBtn, 'image');

checkImageBtn.addEventListener('click', async () => {
    const file = imageInput.files[0];
    
    if (!file) {
        showError('Пожалуйста, выберите изображение');
        return;
    }
    
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE}/predict/image`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        hideLoading();
        
        if (data.success) {
            displayResults(data);
            tg.HapticFeedback.notificationOccurred('success');
        } else {
            showError(data.error || 'Произошла ошибка');
            tg.HapticFeedback.notificationOccurred('error');
        }
    } catch (error) {
        hideLoading();
        showError('Ошибка подключения к серверу');
        tg.HapticFeedback.notificationOccurred('error');
        console.error(error);
    }
});

// Проверка .eml
const emlInput = document.getElementById('eml-input');
const emlUploadArea = document.getElementById('eml-upload-area');
const emlPreview = document.getElementById('eml-preview');
const checkEmlBtn = document.getElementById('check-eml-btn');

setupFileUpload(emlUploadArea, emlInput, emlPreview, checkEmlBtn, 'eml');

checkEmlBtn.addEventListener('click', async () => {
    const file = emlInput.files[0];
    
    if (!file) {
        showError('Пожалуйста, выберите .eml файл');
        return;
    }
    
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE}/predict/eml`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        hideLoading();
        
        if (data.success) {
            displayResults(data);
            tg.HapticFeedback.notificationOccurred('success');
        } else {
            showError(data.error || 'Произошла ошибка');
            tg.HapticFeedback.notificationOccurred('error');
        }
    } catch (error) {
        hideLoading();
        showError('Ошибка подключения к серверу');
        tg.HapticFeedback.notificationOccurred('error');
        console.error(error);
    }
});

// Функции
function setupFileUpload(area, input, preview, button, type) {
    area.addEventListener('click', () => {
        tg.HapticFeedback.impactOccurred('light');
        input.click();
    });
    
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleFileSelect(file, preview, button, type);
            tg.HapticFeedback.impactOccurred('medium');
        }
    });
}

function handleFileSelect(file, preview, button, type) {
    preview.classList.add('active');
    
    if (type === 'image' && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.innerHTML = `
                <img src="${e.target.result}" alt="Preview">
                <div class="file-preview-info">${file.name}</div>
            `;
        };
        reader.readAsDataURL(file);
    } else if (type === 'eml' && file.name.endsWith('.eml')) {
        preview.innerHTML = `
            <div class="file-preview-info">📧 ${file.name}</div>
        `;
    }
    
    button.disabled = false;
}

function displayResults(data) {
    const result = data.result;
    const found = data.found;
    
    let html = `
        <div class="result-card">
            <div class="result-header">
                <h2 class="result-title">Результаты</h2>
                <div class="result-percentage">${result.percentage}%</div>
            </div>
            
            <div style="text-align: center;">
                <div class="percentage-circle ${result.risk_level}">
                    ${result.percentage.toFixed(1)}%
                </div>
                <div class="risk-level ${result.risk_level}">
                    ${result.risk_emoji} ${result.risk_name}
                </div>
            </div>
            
            ${data.email_info ? `
                <div class="email-info">
                    <h3>📧 Информация о письме</h3>
                    <div class="email-info-item">
                        <span class="email-info-label">От:</span>
                        <span>${data.email_info.from}</span>
                    </div>
                    <div class="email-info-item">
                        <span class="email-info-label">Кому:</span>
                        <span>${data.email_info.to}</span>
                    </div>
                    <div class="email-info-item">
                        <span class="email-info-label">Тема:</span>
                        <span>${data.email_info.subject}</span>
                    </div>
                </div>
            ` : ''}
            
            <div class="result-stats">
                <div class="stat-item">
                    <div class="stat-label">🔗 URL</div>
                    <div class="stat-value">${found.url_count}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">📧 Email</div>
                    <div class="stat-value">${found.email_count}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">📞 Телефоны</div>
                    <div class="stat-value">${found.phone_count}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">📈 Уверенность</div>
                    <div class="stat-value">${result.confidence.toFixed(1)}%</div>
                </div>
            </div>
            
            ${found.urls.length > 0 ? `
                <div class="found-items">
                    <h3>🔗 URL:</h3>
                    <div class="items-list">
                        ${found.urls.slice(0, 5).map(url => `<span class="item-tag">${url}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${found.emails.length > 0 ? `
                <div class="found-items">
                    <h3>📧 Email:</h3>
                    <div class="items-list">
                        ${found.emails.slice(0, 5).map(email => `<span class="item-tag">${email}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
            
            <div class="recommendation">
                <strong>💡 Рекомендация:</strong> ${data.recommendation}
            </div>
        </div>
    `;
    
    resultsContainer.innerHTML = html;
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    tg.HapticFeedback.impactOccurred('heavy');
}

function showLoading() {
    loadingOverlay.classList.add('active');
    tg.MainButton.showProgress();
}

function hideLoading() {
    loadingOverlay.classList.remove('active');
    tg.MainButton.hideProgress();
}

function showError(message) {
    resultsContainer.innerHTML = `
        <div class="result-card" style="border-left: 3px solid #dc3545;">
            <h3 style="color: #dc3545; margin-bottom: 10px;">❌ Ошибка</h3>
            <p>${message}</p>
        </div>
    `;
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Enter для текста
textInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        checkTextBtn.click();
    }
});

