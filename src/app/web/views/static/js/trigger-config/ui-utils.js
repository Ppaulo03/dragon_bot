import { CONFIG } from './config.js';

export const UIUtils = {
    initTabs() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-tab-target]');
            if (!btn) return;

            const targetId = btn.dataset.tabTarget;
            const nav = btn.closest('nav') || document;

            // Limpa estados ativos
            nav.querySelectorAll('[data-tab-target]').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(el => {
                el.classList.remove('active');
                el.style.display = 'none';
            });

            // Ativa os novos
            btn.classList.add('active');
            const targetContent = document.getElementById(targetId);
            if (targetContent) {
                targetContent.classList.add('active');
                targetContent.style.display = 'block';
            }

            // Notifica o sistema
            document.dispatchEvent(new CustomEvent('ui:tabChanged', { detail: { targetId } }));
        });
    },

    initCollapsibles() {
        document.addEventListener('click', (e) => {
            const header = e.target.closest('.card-header');
            if (!header) return;

            // Ignora se o clique for em botões de ação ou inputs dentro do header
            if (e.target.matches('input, button, select, .remove-btn, .action-icon')) return;

            const card = header.closest(CONFIG.SELECTORS.card);
            if (card) {
                card.classList.toggle('collapsed');
            }
        });
    },

    setupSortable(containerId) {
        const el = document.getElementById(containerId);
        // Verifica se o Sortable está disponível globalmente (via CDN/Script tag)
        if (!el || typeof Sortable === 'undefined') return;

        return new Sortable(el, {
            animation: CONFIG.UI.sortableAnimation,
            handle: '.card-header',
            ghostClass: 'sortable-ghost',
            onEnd: () => {
                document.dispatchEvent(new CustomEvent('ui:orderUpdated', { detail: { containerId } }));
            }
        });
    },

    scrollToElement(el) {
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
};