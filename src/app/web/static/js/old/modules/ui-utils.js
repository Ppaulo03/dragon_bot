/**
 * Inicializa o sistema de Abas (Tabs) baseado em data-attributes.
 * O gatilho deve ter [data-tab-target="id-da-aba"]
 * A aba deve ter o ID correspondente e a classe .tab-content
 */
export function initTabs() {
    document.addEventListener('click', (e) => {
        const target = e.target.closest('[data-tab-target]');
        if (!target) return;

        const targetId = target.dataset.tabTarget;
        const container = target.closest('nav') || document;

        // 1. Remove classes ativas dos links e conteúdos
        container.querySelectorAll('[data-tab-target]').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));

        // 2. Ativa o link clicado e a aba correspondente
        target.classList.add('active');
        const content = document.getElementById(targetId);
        if (content) content.classList.add('active');

        // Dispara um evento personalizado caso outras partes do código precisem saber da troca
        document.dispatchEvent(new CustomEvent('tabChanged', { detail: { tabId: targetId } }));
    });
}

/**
 * Inicializa o comportamento de colapsar cards.
 * Espera um container com a classe .card-header e um pai .rule-card
 */
export function initCollapsibles() {
    document.addEventListener('click', (e) => {
        const header = e.target.closest('.card-header');
        if (!header) return;

        // Não colapsa se clicar em inputs ou botões dentro do header
        if (e.target.matches('input, button, select, .remove-btn')) return;

        const card = header.closest('.rule-card');
        if (card) {
            card.classList.toggle('collapsed');
        }
    });
}

/**
 * Configura o SortableJS para um container específico
 * @param {string} containerId - ID do elemento que contém os itens arrastáveis
 */
export function setupSortable(containerId) {
    const el = document.getElementById(containerId);
    if (!el || typeof Sortable === 'undefined') return;

    return new Sortable(el, {
        animation: 150,
        handle: '.card-header',
        ghostClass: 'sortable-ghost',
        onEnd: () => {
            document.dispatchEvent(new CustomEvent('orderUpdated', { detail: { containerId } }));
        },
    });
}