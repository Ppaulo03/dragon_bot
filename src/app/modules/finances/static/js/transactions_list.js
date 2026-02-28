/**
 * Dragon Finance - Transactions List Engine 🐲
 * Versão Unificada e Corrigida para Scroll ao Topo
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Inicialização Inicial
    initializeAllCards();

    // 2. Listener Único para HTMX (Scroll e Reidratação)
    document.body.addEventListener('htmx:afterSwap', (evt) => {
        if (evt.detail.target.id === 'transactions-wrapper') {

            // Reidrata os novos cards
            initializeAllCards();
            setTimeout(() => {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            }, 10);
        }
    });

    // 3. Limpeza de URL (Único)
    document.body.addEventListener('htmx:configRequest', (evt) => {
        const params = evt.detail.parameters;
        for (const key in params) {
            if (params[key] === "" || params[key] === null) {
                delete params[key];
            }
        }
    });
});

/**
 * Inicializa a interatividade dos cards
 */
function initializeAllCards() {
    const cards = document.querySelectorAll('.tx-card');
    cards.forEach(card => {
        if (card.dataset.initialized === "true") return;

        if (typeof initTransactionCard === 'function') {
            initTransactionCard(card);
            card.dataset.initialized = "true";
        }
    });
}