// Конфигурация
const DEFAULT_API_URL = 'http://localhost:5000';

// Элементы DOM
const checkBtn = document.getElementById('checkBtn');
const statusDiv = document.getElementById('status');
const resultsDiv = document.getElementById('results');
const percentageCircle = document.getElementById('percentageCircle');
const percentageValue = document.getElementById('percentageValue');
const percentageLabel = document.getElementById('percentageLabel');
const statusValue = document.getElementById('statusValue');
const confidenceValue = document.getElementById('confidenceValue');
const urlFound = document.getElementById('urlFound');
const emailFound = document.getElementById('emailFound');
const phoneFound = document.getElementById('phoneFound');
const textPreview = document.getElementById('textPreview');
const apiUrlInput = document.getElementById('apiUrl');

// Загрузка сохраненного API URL
if (chrome.storage) {
    chrome.storage.local.get(['apiUrl'], (result) => {
        if (result.apiUrl) {
            apiUrlInput.value = result.apiUrl;
        }
    });

    // Сохранение API URL
    apiUrlInput.addEventListener('change', () => {
        chrome.storage.local.set({ apiUrl: apiUrlInput.value });
    });
}

// Функция для показа статуса
function showStatus(message, type = 'info') {
    statusDiv.textContent = message;
    statusDiv.className = `status ${type}`;
    statusDiv.classList.remove('hidden');
}

// Функция для скрытия статуса
function hideStatus() {
    statusDiv.classList.add('hidden');
}

// Функция для получения текста со страницы
async function getPageText() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        const results = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            function: extractPageText
        });
        
        return results[0].result;
    } catch (error) {
        console.error('Ошибка при получении текста:', error);
        throw error;
    }
}

// Функция, которая выполняется на странице для извлечения текста
function extractPageText() {
    // Удаляем скрипты и стили
    const scripts = document.querySelectorAll('script, style, noscript');
    scripts.forEach(el => el.remove());
    
    // Получаем весь видимый текст
    const bodyText = document.body.innerText || document.body.textContent || '';
    
    // Извлекаем URL
    const urlRegex = /(https?:\/\/[^\s]+|www\.[^\s]+)/gi;
    const urls = bodyText.match(urlRegex) || [];
    const hasUrl = urls.length > 0;
    
    // Извлекаем email
    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi;
    const emails = bodyText.match(emailRegex) || [];
    const hasEmail = emails.length > 0;
    
    // Извлекаем телефоны (различные форматы)
    const phoneRegex = /(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\d{10,}/gi;
    const phones = bodyText.match(phoneRegex) || [];
    const hasPhone = phones.length > 0;
    
    // Очищаем текст от лишних пробелов
    const cleanText = bodyText.replace(/\s+/g, ' ').trim();
    
    // Ограничиваем длину текста (первые 5000 символов)
    const limitedText = cleanText.substring(0, 5000);
    
    return {
        text: limitedText,
        url: hasUrl,
        email: hasEmail,
        phone: hasPhone,
        urlCount: urls.length,
        emailCount: emails.length,
        phoneCount: phones.length
    };
}

// Функция для отправки запроса к API
async function checkPhishing(text, url, email, phone) {
    const apiUrl = apiUrlInput.value || DEFAULT_API_URL;
    const endpoint = `${apiUrl}/api/predict/text`;  // Исправлен endpoint
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text  // API принимает только text, остальное определяет сам
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Ошибка при запросе к API:', error);
        throw error;
    }
}

// Функция для обновления UI с результатами
function updateResults(data, pageInfo) {
    // Исправляем формат ответа под новый API
    const percentage = data.result?.percentage || data.result?.phishing_percentage || 0;
    const isPhishing = data.result?.is_phishing || false;
    const confidence = data.result?.confidence || 0;
    
    // Обновляем процент
    percentageValue.textContent = `${percentage.toFixed(1)}%`;
    
    // Определяем класс для круга в зависимости от процента
    percentageCircle.className = 'percentage-circle';
    if (percentage < 30) {
        percentageCircle.classList.add('safe');
        statusValue.textContent = 'Безопасно';
        statusValue.className = 'detail-value safe';
    } else if (percentage < 50) {
        percentageCircle.classList.add('warning');
        statusValue.textContent = 'Подозрительно';
        statusValue.className = 'detail-value warning';
    } else if (percentage < 70) {
        percentageCircle.classList.add('danger');
        statusValue.textContent = 'Опасно';
        statusValue.className = 'detail-value danger';
    } else {
        percentageCircle.classList.add('critical');
        statusValue.textContent = 'Критично';
        statusValue.className = 'detail-value danger';
    }
    
    // Обновляем детали
    confidenceValue.textContent = `${confidence.toFixed(1)}%`;
    urlFound.textContent = pageInfo.url ? `Да (${pageInfo.urlCount})` : 'Нет';
    emailFound.textContent = pageInfo.email ? `Да (${pageInfo.emailCount})` : 'Нет';
    phoneFound.textContent = pageInfo.phone ? `Да (${pageInfo.phoneCount})` : 'Нет';
    
    // Показываем превью текста
    const previewText = data.input.text || pageInfo.text.substring(0, 200);
    textPreview.textContent = previewText + (pageInfo.text.length > 200 ? '...' : '');
    
    // Показываем результаты
    resultsDiv.classList.remove('hidden');
}

// Обработчик нажатия на кнопку
checkBtn.addEventListener('click', async () => {
    try {
        // Блокируем кнопку
        checkBtn.disabled = true;
        checkBtn.querySelector('.button-text').style.display = 'none';
        checkBtn.querySelector('.button-loader').style.display = 'inline-block';
        
        // Скрываем предыдущие результаты
        resultsDiv.classList.add('hidden');
        hideStatus();
        
        showStatus('Извлечение текста со страницы...', 'info');
        
        // Получаем текст со страницы
        const pageInfo = await getPageText();
        
        if (!pageInfo.text || pageInfo.text.trim().length === 0) {
            throw new Error('Не удалось извлечь текст со страницы');
        }
        
        showStatus('Анализ текста...', 'info');
        
        // Отправляем запрос к API
        const result = await checkPhishing(
            pageInfo.text,
            false,  // API сам определяет наличие URL/email/phone
            false,
            false
        );
        
        if (result.success) {
            updateResults(result, pageInfo);
            showStatus('Анализ завершен!', 'success');
        } else {
            throw new Error(result.error || 'Ошибка при анализе');
        }
        
    } catch (error) {
        console.error('Ошибка:', error);
        showStatus(`Ошибка: ${error.message}`, 'error');
        resultsDiv.classList.add('hidden');
    } finally {
        // Разблокируем кнопку
        checkBtn.disabled = false;
        checkBtn.querySelector('.button-text').style.display = 'inline';
        checkBtn.querySelector('.button-loader').style.display = 'none';
    }
});

// Проверка доступности API при загрузке
async function checkAPIHealth() {
    const apiUrl = apiUrlInput.value || DEFAULT_API_URL;
    try {
        const response = await fetch(`${apiUrl}/api/health`);  // Исправлен endpoint
        if (response.ok) {
            showStatus('API доступен', 'success');
            setTimeout(hideStatus, 2000);
        }
    } catch (error) {
        showStatus('API недоступен. Проверьте настройки.', 'error');
    }
}

// Проверяем API при загрузке
checkAPIHealth();

