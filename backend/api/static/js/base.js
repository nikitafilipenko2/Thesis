// ========================================
// Общие утилиты
// ========================================

/**
 * Показать всплывающее уведомление
 * @param {string} message - Текст уведомления
 * @param {string} type - Тип: 'success', 'error', 'info', 'warning'
 * @param {number} duration - Длительность в мс
 */
function showAlert(message, type = 'info', duration = 3000) {
    const alertDiv = document.createElement('div');
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'info': 'alert-info',
        'warning': 'alert-warning'
    }[type] || 'alert-info';

    alertDiv.className = `alert ${alertClass} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <span>${message}</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 300);
    }, duration);
}

/**
 * Копирование текста в буфер обмена
 * @param {string} text - Текст для копирования
 * @returns {Promise<boolean>}
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showAlert('Скопировано в буфер обмена', 'success');
        return true;
    } catch (err) {
        console.error('Ошибка копирования:', err);
        showAlert('Не удалось скопировать текст', 'error');
        return false;
    }
}

/**
 * Подсчёт количества слов в тексте
 * @param {string} text
 * @returns {number}
 */
function countWords(text) {
    if (!text) return 0;
    return text.trim().split(/\s+/).filter(w => w.length > 0).length;
}

/**
 * Подсчёт количества предложений в тексте
 * @param {string} text
 * @returns {number}
 */
function countSentences(text) {
    if (!text) return 0;
    return text.split(/[.!?]+/).filter(s => s.trim().length > 0).length;
}

/**
 * Форматирование времени (секунды -> mm:ss)
 * @param {number} seconds
 * @returns {string}
 */
function formatTime(seconds) {
    if (!seconds) return '0 сек';
    if (seconds < 60) return `${seconds.toFixed(2)} сек`;
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(0);
    return `${mins} мин ${secs} сек`;
}