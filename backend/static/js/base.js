function showAlert(message, type = 'info', duration = 3000) {
    const alertDiv = document.createElement('div');
    const alertClass = {
        success: 'alert-success',
        error: 'alert-danger',
        info: 'alert-info',
        warning: 'alert-warning'
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

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showAlert('Скопировано в буфер обмена', 'success');
        return true;
    } catch {
        showAlert('Не удалось скопировать текст', 'error');
        return false;
    }
}

function countWords(text) {
    if (!text) {
        return 0;
    }
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

function countSentences(text) {
    if (!text) {
        return 0;
    }
    return text.split(/[.!?]+/).filter(sentence => sentence.trim().length > 0).length;
}

document.addEventListener('click', async event => {
    const button = event.target.closest('.copy-result-button');
    if (!button) {
        return;
    }

    const targetId = button.dataset.copyTarget;
    const target = document.getElementById(targetId);
    if (!target) {
        showAlert('Текст для копирования не найден', 'error');
        return;
    }

    await copyToClipboard(target.textContent || '');
});
