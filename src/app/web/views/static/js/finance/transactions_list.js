/**
 * Dragon Finance - Transactions List Engine
 * Focada em gerenciar o ciclo de vida dos cards injetados via HTMX.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Inicializa os cards que já vieram no carregamento inicial da página
    initializeAllCards();

    // 2. Escuta o HTMX para inicializar novos cards após cada troca (filtro/paginação)
    document.body.addEventListener('htmx:afterSwap', (evt) => {
        // Se o que mudou foi o container de transações, reinicializamos os cards
        if (evt.detail.target.id === 'transactions-wrapper') {
            initializeAllCards();
            // Opcional: Scroll suave para o topo da lista ao mudar de página
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });

    // 3. Listener para limpar campos vazios da URL (Opcional com HTMX)
    // O HTMX envia todos os campos, mas podemos interceptar se quiser uma URL super limpa
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
 * Função auxiliar para garantir que todos os cards na tela 
 * tenham seus eventos e reidratação de categorias ativos.
 */
function initializeAllCards() {
    const cards = document.querySelectorAll('.tx-card');
    cards.forEach(card => {
        // Evita inicializar o mesmo card duas vezes
        if (card.dataset.initialized === "true") return;

        if (typeof initTransactionCard === 'function') {
            initTransactionCard(card);
            card.dataset.initialized = "true";
        }
    });
}