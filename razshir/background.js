// Background service worker для расширения
// Минимальная реализация

chrome.runtime.onInstalled.addListener(() => {
    console.log('Phishing Checker расширение установлено');
});

