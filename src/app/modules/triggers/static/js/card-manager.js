import { CONFIG } from './config.js';
import { FileEngine } from './file-engine.js';
import { FileState } from './state.js';

export const CardManager = {
    toggleZone(card, zoneName, isVisible) {
        const zone = card.querySelector(`[data-zone="${zoneName}"]`);
        if (!zone) return;

        zone.style.display = isVisible ? 'block' : 'none';
        zone.querySelectorAll('input, textarea, select').forEach(input => {
            input.disabled = !isVisible;
        });
    },

    refresh(card) {
        // --- BLOCO 1: CAPTURA DE DADOS ---
        const type = card.querySelector('[name^="type_"]')?.value;
        const matcher = card.querySelector('[name^="matcher_"]')?.value || 'always';
        const mode = card.querySelector('input[type="radio"]:checked')?.value || 'text';
        const cardId = card.id;

        const isImageMatcher = (matcher === 'image_similarity');
        this.toggleZone(card, 'matcher-text', !isImageMatcher);
        this.toggleZone(card, 'matcher-image', isImageMatcher);

        const canToggleMode = ['send_text', 'send_sticker'].includes(type);
        this.toggleZone(card, 'mode-selector', canToggleMode);

        let finalMode = mode;
        if (type === 'send_contact') finalMode = 'api';
        if (['send_image', 'send_audio'].includes(type)) finalMode = 'text';

        this.toggleZone(card, 'input-text', (finalMode === 'text' && type === 'send_text'));
        this.toggleZone(card, 'input-api', (finalMode === 'api'));
        this.toggleZone(card, 'input-file', (finalMode === 'text' && type !== 'send_contact'));
        const fileInput = card.querySelector('input[type="file"]:not([name="trigger_file_upload"])');

        if (fileInput) {
            fileInput.setAttribute('accept', CONFIG.VALIDATION[type] || CONFIG.VALIDATION.default);
        }

        if (fileInput) {
            const syncedFiles = FileEngine.revalidateState(cardId, type);
            fileInput.files = syncedFiles;
        }

        const previewBox = card.querySelector('.preview-box.sutil-preview');
        if (previewBox) {
            previewBox.querySelectorAll('.preview-item:not(.new-file)').forEach(item => {
                const img = item.querySelector('img');
                const fileName = item.dataset.fileName || (img ? img.src.split('/').pop() : "");
                const isCompatible = FileEngine.isValid({ name: fileName }, type);
                const hiddenInput = item.querySelector('input[type="hidden"]');
                if (!isCompatible) {
                    item.style.display = 'none';
                    if (hiddenInput) hiddenInput.disabled = true;

                } else {
                    const isMarkedDelete = item.classList.contains('marked-for-delete');
                    item.style.display = 'inline-block';
                    if (hiddenInput) hiddenInput.disabled = isMarkedDelete;
                }
            });


            previewBox.querySelectorAll('.preview-item.new-file').forEach(item => {
                const fileName = item.dataset.fileName;
                if (!FileEngine.isValid({ name: fileName }, type)) {
                    item.remove();
                    FileState.removeFile(card.id, fileName);
                }
            });
        }


    },

    addCard(sectionType) {
        const container = document.getElementById(`container-${sectionType}s`);
        const template = document.getElementById('template-rule-card');
        if (!container || !template) return;

        const clone = template.content.cloneNode(true);
        const card = clone.querySelector(CONFIG.SELECTORS.card);
        const uniqueId = `card-${Date.now()}`;

        card.id = uniqueId;
        card.dataset.section = sectionType;

        // Se for fallback (no-trigger), trava o matcher
        if (sectionType === 'no-trigger') {
            const matcherSelect = card.querySelector('[name^="matcher_"]');
            if (matcherSelect) {
                matcherSelect.value = 'always';
                matcherSelect.closest('label').style.display = 'none';
            }
        }

        container.appendChild(clone);
        this.refresh(card);
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });

        return card;
    }
};