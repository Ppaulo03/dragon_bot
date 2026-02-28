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

    updateTriggerPreview(container, file) {
        if (!container || !file) return;
        const url = URL.createObjectURL(file);
        container.innerHTML = `<img src="${url}" class="img-ref-preview">`;
    },

    handleItemInteraction(item) {
        const card = item.closest(CONFIG.SELECTORS.card);
        const fileName = item.dataset.fileName;
        const fileInput = card.querySelector('input[type="file"]:not([name^="trigger_file_upload_"])');

        if (item.classList.contains('new-file')) {
            FileEngine.removeFile(card.id, fileName, fileInput);
            item.remove();
        } else {
            item.classList.toggle('marked-for-delete');
            const hiddenInput = item.querySelector('input[type="hidden"]');
            if (hiddenInput) {
                hiddenInput.disabled = item.classList.contains('marked-for-delete');
            }
        }
    },

    refresh(card) {
        const type = card.querySelector('[name^="type_"]')?.value;
        const matcher = card.querySelector('[name^="matcher_"]')?.value || 'always';
        const mode = card.querySelector('input[type="radio"]:checked')?.value || 'text';
        const cardId = card.id;

        // Lógica de Matcher (Texto vs Imagem)
        const isImageMatcher = (matcher === 'image_similarity');
        this.toggleZone(card, 'matcher-text', !isImageMatcher);
        this.toggleZone(card, 'matcher-image', isImageMatcher);

        // Lógica de Modo de Resposta
        const canToggleMode = ['send_text', 'send_sticker'].includes(type);
        this.toggleZone(card, 'mode-selector', canToggleMode);

        let finalMode = mode;
        if (type === 'send_contact') finalMode = 'api';
        if (['send_image', 'send_audio'].includes(type)) finalMode = 'text';

        this.toggleZone(card, 'input-text', (finalMode === 'text' && type === 'send_text'));
        this.toggleZone(card, 'input-api', (finalMode === 'api'));
        this.toggleZone(card, 'input-file', (finalMode === 'text' && type !== 'send_contact'));

        // Sincronização de Arquivos e Validação de Extensões
        const fileInput = card.querySelector('input[type="file"]:not([name^="trigger_file_upload_"])');
        if (fileInput) {
            fileInput.setAttribute('accept', CONFIG.VALIDATION[type] || CONFIG.VALIDATION.default);
            const syncedFiles = FileEngine.revalidateState(cardId, type);
            fileInput.files = syncedFiles;
        }

        this._cleanupPreviews(card, type);
    },

    _cleanupPreviews(card, type) {
        const previewBox = card.querySelector('.preview-box.sutil-preview');
        if (!previewBox) return;
        previewBox.querySelectorAll('.preview-item:not(.new-file)').forEach(item => {
            const fileName = item.dataset.fileName || "";
            const isCompatible = FileEngine.isValid({ name: fileName }, type);
            const hiddenInput = item.querySelector('input[type="hidden"]');

            if (!isCompatible) {
                item.style.display = 'none';
                if (hiddenInput) hiddenInput.disabled = true;
            } else {
                item.style.display = 'inline-block';
                if (hiddenInput) {
                    hiddenInput.disabled = item.classList.contains('marked-for-delete');
                }
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
};