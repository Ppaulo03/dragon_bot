function formatPhoneDisplays() {
    document.querySelectorAll('.phone-display').forEach(el => {
        // Evita re-formatar o que já está formatado
        if (el.dataset.formatted === "true") return;

        let x = el.innerText.replace(/\D/g, '');
        if (x.length >= 12) {
            el.innerText = `+${x.substring(0, 2)} (${x.substring(2, 4)}) ${x.substring(4, 9)}-${x.substring(9, 13)}`;
            el.dataset.formatted = "true";
        }
    });
}

function setupPhoneMask() {
    const phoneInput = document.getElementById('phone_mask');
    const hiddenInput = document.getElementById('jid_clean');

    if (!phoneInput || !hiddenInput) return;

    phoneInput.addEventListener('input', function (e) {
        let x = e.target.value.replace(/\D/g, '');
        hiddenInput.value = x;

        let formatted = "";
        if (x.length > 0) {
            formatted = "+" + x.substring(0, 2);
            if (x.length > 2) formatted += " (" + x.substring(2, 4) + ")";
            if (x.length > 4) formatted += " " + x.substring(4, 9);
            if (x.length > 9) formatted += "-" + x.substring(9, 13);
        }
        e.target.value = formatted;
    });
}

document.addEventListener('DOMContentLoaded', () => {
    setupPhoneMask();
    formatPhoneDisplays();
});

document.body.addEventListener('htmx:afterSwap', (event) => {
    if (event.detail.target.id === 'user-list-container') {
        formatPhoneDisplays();
    }
});