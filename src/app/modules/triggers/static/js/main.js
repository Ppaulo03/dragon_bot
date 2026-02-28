import { CONFIG } from './config.js';
import { FileState } from './state.js';
import { FileEngine } from './file-engine.js';
import { PreviewEngine } from './preview-engine.js';
import { CardManager } from './card-manager.js';
import { ModalManager } from './modal-manager.js';
import { UIUtils } from './ui-utils.js';


document.addEventListener('DOMContentLoaded', () => {
    UIUtils.initTabs();
    UIUtils.initCollapsibles();
    UIUtils.setupSortable(CONFIG.SELECTORS.triggerContainer);
    UIUtils.setupSortable(CONFIG.SELECTORS.fallbackContainer);
    document.querySelectorAll(CONFIG.SELECTORS.card).forEach(card => {
        CardManager.refresh(card);
    });
});

/**
 * 2. Delegação de Eventos: Mudanças de Estado
 * Captura interações de select, radio e upload de arquivos.
 */
document.addEventListener('change', (e) => {
    const card = e.target.closest(CONFIG.SELECTORS.card);
    if (!card) return;

    if (e.target.matches('[name^="type_"], [name^="matcher_"], input[type="radio"]')) {
        CardManager.refresh(card);
        return;
    }

    if (e.target.type === 'file') {
        handleFileSelection(e.target, card);
    }
});

/**
 * Orquestra o processamento de arquivos selecionados.
 */
function handleFileSelection(input, card) {
    const isTrigger = input.name.startsWith('trigger_file_upload_');
    const type = card.querySelector('[name^="type_"]').value;

    if (isTrigger) {
        const file = input.files[0];
        if (file && FileEngine.isValid(file, type, true)) {
            const previewContainer = card.querySelector(`[id^="preview-trig-"]`);
            CardManager.updateTriggerPreview(previewContainer, file);
        } else {
            input.value = '';
        }
    } else {
        const validFiles = FileEngine.handleUpload(input, card.id, type);
        input.value = '';

        const previewContainer = card.querySelector('.sutil-preview');
        if (previewContainer && validFiles.length > 0) {
            validFiles.forEach(file => {
                const previewEl = PreviewEngine.createPreviewElement(file);
                previewContainer.appendChild(previewEl);
            });
            const msg = previewContainer.parentElement.querySelector('.no-files-msg');
            if (msg) msg.style.display = 'none';
        }
    }
}

/**
 * 3. Drag and Drop
 * Implementação simplificada usando delegação.
 */
['dragover', 'dragleave', 'drop'].forEach(eventType => {
    document.addEventListener(eventType, (e) => {
        const zone = e.target.closest('.zone-container');
        if (!zone) return;

        e.preventDefault();

        if (eventType === 'dragover') zone.classList.add('drag-over');
        if (eventType === 'dragleave') zone.classList.remove('drag-over');

        if (eventType === 'drop') {
            zone.classList.remove('drag-over');
            const fileInput = zone.querySelector('input[type="file"]');
            if (fileInput) {
                fileInput.files = e.dataTransfer.files;
                fileInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    });
});

/**
 * 4. Interação com Previews (Clique e Long Press)
 */
let longPressTimer;
document.addEventListener('mousedown', (e) => {
    const item = e.target.closest('.preview-item');
    if (!item) return;

    longPressTimer = setTimeout(() => {
        const source = PreviewEngine.getSource(item);
        if (source) {
            ModalManager.open(source, item.dataset.fileName);
        }
        longPressTimer = null;
    }, CONFIG.UI.longPressDuration);
});

document.addEventListener('mouseup', (e) => {
    const item = e.target.closest('.preview-item');
    if (longPressTimer) {
        clearTimeout(longPressTimer);
        // Se soltou antes do tempo do long press, trata como interação (delete/toggle)
        CardManager.handleItemInteraction(item);
    }
});

/**
 * 5. Funções de Salvamento e Exposição Global
 */
window.addCard = (section) => CardManager.addCard(section);
window.closeModal = () => ModalManager.close();

// Listener para atualização visual de porcentagem
document.addEventListener('input', (e) => {
    if (e.target.matches('input[name^="chance_"]')) {
        const display = e.target.closest(CONFIG.SELECTORS.card).querySelector('.chance-display');
        if (display) {
            const val = parseFloat(e.target.value) * 100;
            display.textContent = `${val.toFixed(1)}%`;
        }
    }
});

async function saveAll() {
    const form = document.getElementById('main-form') || document.querySelector('form');
    if (!form) return console.error("Formulário não encontrado");

    const formData = new FormData(form);

    document.querySelectorAll(CONFIG.SELECTORS.card).forEach(card => {
        const cardId = card.id;
        const ruleIdInput = card.querySelector('[name="rule_id"]');
        if (!ruleIdInput) return;

        const realId = ruleIdInput.value;

        // Limpa entradas automáticas do FormData para controle manual
        formData.delete(`file_upload_${realId}`);
        formData.delete(`trigger_file_upload_${realId}`);
        formData.delete(`keep_files_${realId}`);

        // 1. Re-adiciona apenas os arquivos remotos que NÃO foram marcados para exclusão
        card.querySelectorAll(`input[name="keep_files_${realId}"]`).forEach(input => {
            if (!input.disabled) {
                formData.append(`keep_files_${realId}`, input.value);
            }
        });

        // 2. Adiciona arquivos novos vindos do FileState
        const filesInState = FileState.getFiles(cardId).files;
        Array.from(filesInState).forEach(file => {
            formData.append(`file_upload_${realId}`, file);
        });

        // 3. Adiciona arquivo de trigger se existir
        const triggerInput = card.querySelector(`[name="trigger_file_upload_${realId}"]`);
        if (triggerInput && triggerInput.files.length > 0) {
            formData.append(`trigger_file_upload_${realId}`, triggerInput.files[0]);
        }
    });

    try {
        const response = await fetch('/trigger-config', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            alert("Configurações salvas com sucesso!");
            window.location.reload();
        } else {
            const errorData = await response.json();
            alert("Erro ao salvar: " + (errorData.detail || "Erro desconhecido"));
        }
    } catch (error) {
        console.error("Erro na requisição:", error);
        alert("Erro de conexão ao salvar.");
    }
}
window.saveAll = saveAll;