import { CONFIG } from './config.js';
import { FileState } from './state.js';
import { FileEngine } from './file-engine.js';
import { PreviewEngine } from './preview-engine.js';
import { CardManager } from './card-manager.js';
import { ModalManager } from './modal-manager.js';
import { UIUtils } from './ui-utils.js';

/**
 * 1. Inicialização Global
 */
document.addEventListener('DOMContentLoaded', () => {
    UIUtils.initTabs();
    UIUtils.initCollapsibles();
    UIUtils.setupSortable(CONFIG.SELECTORS.triggerContainer);
    UIUtils.setupSortable(CONFIG.SELECTORS.fallbackContainer);

    // Refresh inicial em cards que já vieram renderizados pelo Jinja2
    document.querySelectorAll(CONFIG.SELECTORS.card).forEach(card => {
        CardManager.refresh(card);
    });
});

/**
 * 2. Delegação de Eventos: Mudanças de Estado
 */
document.addEventListener('change', (e) => {
    const card = e.target.closest(CONFIG.SELECTORS.card);
    if (!card) return;

    // Lógica de Refresh de UI
    if (e.target.matches('[name^="type_"], [name^="matcher_"], input[type="radio"]')) {
        CardManager.refresh(card);
        return; // Interrompe para não processar como arquivo
    }

    // Lógica de Arquivos
    if (e.target.type === 'file') {
        const isTrigger = e.target.name.startsWith('trigger_file_upload_');

        if (isTrigger) {

            const file = e.target.files[0];
            if (file && !file.type.startsWith('image/')) {
                e.target.value = ''; // Limpa o input
                return;
            }
            if (file) {
                const previewContainer = card.querySelector(`[id^="preview-trig-"]`);
                const url = URL.createObjectURL(file);
                previewContainer.innerHTML = `<img src="${url}" class="img-ref-preview">`;
            }
        } else {
            const type = card.querySelector('[name^="type_"]').value;
            FileEngine.handleUpload(e.target, card.id, type);
            e.target.value = '';
        }
    }
});


document.addEventListener('dragover', (e) => {
    const zone = e.target.closest('.zone-container');
    if (!zone || !zone.querySelector('input[type="file"]')) return;

    e.preventDefault();
    zone.classList.add('drag-over');
    e.dataTransfer.dropEffect = 'copy';
});

document.addEventListener('dragleave', (e) => {
    const zone = e.target.closest('.zone-container');
    if (!zone) return;

    // Previne que o destaque suma ao passar por cima de elementos filhos
    const related = e.relatedTarget ? e.relatedTarget.closest('.zone-container') : null;
    if (related !== zone) {
        zone.classList.remove('drag-over');
    }
});

document.addEventListener('drop', (e) => {
    const zone = e.target.closest('.zone-container');
    if (!zone) return;

    const fileInput = zone.querySelector('input[type="file"]');
    if (!fileInput) return;

    e.preventDefault();
    zone.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        // Injeta os arquivos no input
        fileInput.files = files;
        // Dispara o evento change para acionar sua lógica de Preview/Upload já existente
        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
    }
});
/**
 * 3. Delegação de Eventos: Interação com Previews (Clique e Long Press)
 */
let longPressTimer;
document.addEventListener('mousedown', (e) => {
    const item = e.target.closest('.preview-item');
    if (!item) return;
    longPressTimer = setTimeout(() => {
        const source = PreviewEngine.getSource(item);
        const fileName = item.dataset.fileName;

        if (source) {
            ModalManager.open(source, fileName);
        } else {
            console.error("Não foi possível encontrar a URL para o arquivo:", fileName);
        }
        longPressTimer = null;
    }, CONFIG.UI.longPressDuration);
});

document.addEventListener('mouseup', (e) => {
    const item = e.target.closest('.preview-item');
    if (longPressTimer) {
        clearTimeout(longPressTimer);
        handleItemInteraction(item);
    }
});

function handleItemInteraction(item) {
    const card = item.closest(CONFIG.SELECTORS.card);
    const fileName = item.dataset.fileName;
    const fileInput = card.querySelector('input[type="file"]:not([name="trigger_file_upload"])');

    if (item.classList.contains('new-file')) {
        // Remove do buffer local
        FileEngine.removeFile(card.id, fileName, fileInput);
        item.remove();
    } else {
        // Marca para exclusão no servidor
        item.classList.toggle('marked-for-delete');
        const hiddenInput = item.querySelector('input[type="hidden"]');
        if (hiddenInput) hiddenInput.disabled = item.classList.contains('marked-for-delete');
    }
}

/**
 * 4. Exposição para o HTML (Jinja2 Templates)
 */
window.addCard = (section) => CardManager.addCard(section);
window.closeModal = () => ModalManager.close();

// Listener para atualização de % nos cards
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
        const realId = card.querySelector('[name="rule_id"]').value;

        formData.delete(`file_upload_${realId}`);
        formData.delete(`trigger_file_upload_${realId}`);

        formData.delete(`keep_files_${realId}`);

        // 2. Re-adiciona apenas os que NÃO estão desabilitados
        card.querySelectorAll(`input[name="keep_files_${realId}"]`).forEach(input => {
            if (!input.disabled) {
                formData.append(`keep_files_${realId}`, input.value);
            }
        });

        const filesInState = FileState.getFiles(cardId).files;
        Array.from(filesInState).forEach(file => {
            formData.append(`file_upload_${realId}`, file);
        });

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