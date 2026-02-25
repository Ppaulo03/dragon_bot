/**
 * Triggers Editor Entrypoint
 * Gerencia a lógica de edição de regras, visibilidade dinâmica e criação de cards.
 */
console.log("!!! O SCRIPT FOI CARREGADO PELO NAVEGADOR !!!");
import { initTabs, initCollapsibles, setupSortable } from '../modules/ui-utils.js';
import { renderMultiplePreviews, renderSinglePreview, initRemotePreviews } from '../modules/preview-engine.js';
const FILE_VALIDATION = {
    'send_sticker': '.png, .jpg, .jpeg, .webp',
    'send_image': '.png, .jpg, .jpeg, .gif, .webp',
    'send_audio': '.mp3, .ogg, .wav, .m4a',
    'send_text': '.txt, .json',
    'default': '*'
};
const pendingFiles = {}; // Armazena arquivos selecionados para cada card, chaveada por cardId
const TriggersEditor = {
    init() {
        initTabs();
        initCollapsibles();
        initRemotePreviews();
        setupSortable('container-triggers');
        setupSortable('container-no-triggers');
        this.bindEvents();
        document.querySelectorAll('.rule-card').forEach(card => this.refreshCardUI(card));
        console.log("🐲 Dragon Bot Editor: Sistema carregado com sucesso.");
    },

    bindEvents() {
        // Ouvinte global para mudanças de estado (Selects, Radios e Inputs)
        document.addEventListener('change', (e) => {
            const card = e.target.closest('.rule-card');
            if (!card) return;

            // Se mudou algo que afeta o layout do card
            if (e.target.matches('[name^="type_"], [name^="matcher_"], input[type="radio"]')) {
                this.refreshCardUI(card);
            }

            // Se foi um upload de arquivo
            if (e.target.type === 'file') {
                this.handleFileUpload(e.target, card);
            }
        });
    },

    /**
     * Reatividade: Mostra/Esconde campos baseado no Tipo e Matcher
     */
    refreshCardUI(card) {
        // 1. Captura de Elementos
        const typeEl = card.querySelector('[name^="type_"]');
        const matcherEl = card.querySelector('[name^="matcher_"]');
        const modeEl = card.querySelector('input[type="radio"]:checked');
        const triggerInput = card.querySelector('[name="trigger_file_upload"]');
        const destInput = card.querySelector('input[name^="file_upload_"]');
        const previewBox = card.querySelector('.preview-box.sutil-preview');

        const type = typeEl ? typeEl.value : 'send_text';
        const matcher = matcherEl ? matcherEl.value : 'always';
        const mode = modeEl ? modeEl.value : 'text';

        // 2. Validação de Filtros (Janela de seleção)
        if (triggerInput) triggerInput.setAttribute('accept', 'image/*');

        const allowed = FILE_VALIDATION[type] || FILE_VALIDATION['default'];
        if (destInput) destInput.setAttribute('accept', allowed);

        // 3. Validação de Arquivos Existentes (Storage)
        if (previewBox) {
            const existingItems = previewBox.querySelectorAll('.preview-item:not(.new-file)');
            const allowedExts = allowed.split(',').map(ext => ext.trim().toLowerCase());

            existingItems.forEach(item => {
                const fileName = (item.dataset.fileName || "").toLowerCase();
                const fileExt = `.${fileName.split('.').pop()}`;
                const hiddenInput = item.querySelector('input[type="hidden"]');

                const isCompatible = allowedExts.includes('*') || allowedExts.includes(fileExt);

                if (!isCompatible) {
                    item.classList.add('incompatible-file');
                    item.style.display = 'none';
                    if (hiddenInput) hiddenInput.disabled = true;
                } else {
                    item.classList.remove('incompatible-file');
                    item.style.display = 'inline-block';
                    // Só reativa se o usuário não tiver marcado para deletar manualmente
                    if (hiddenInput && !item.classList.contains('marked-for-delete')) {
                        hiddenInput.disabled = false;
                    }
                }
            });
        }

        // 4. Lógica de Visibilidade das Zonas
        const isImageMatcher = (matcher === 'image_similarity');
        this.toggleZone(card, 'matcher-text', !isImageMatcher);
        this.toggleZone(card, 'matcher-image', isImageMatcher);

        const canToggleMode = ['send_text', 'send_sticker'].includes(type);
        this.toggleZone(card, 'mode-selector', canToggleMode);

        let finalMode = mode;
        if (type === 'send_contact') finalMode = 'api';
        if (['send_image', 'send_audio', 'send_sticker'].includes(type)) finalMode = 'text';

        this.toggleZone(card, 'input-text', (finalMode === 'text' && type === 'send_text'));
        this.toggleZone(card, 'input-api', (finalMode === 'api'));
        this.toggleZone(card, 'input-file', (finalMode === 'text' && type !== 'send_contact'));
    },

    /**
     * Gerencia a visibilidade de uma div e desabilita seus inputs
     */
    toggleZone(card, zoneName, isVisible) {
        const zone = card.querySelector(`[data-zone="${zoneName}"]`);
        if (!zone) return;

        zone.style.display = isVisible ? 'block' : 'none';

        // Desabilitar inputs escondidos é crucial para o backend não receber lixo
        zone.querySelectorAll('input, textarea, select').forEach(input => {
            input.disabled = !isVisible;
        });
    },

    handleFileUpload(input, card) {
        const cardId = card.id.replace('card-', '');
        const type = card.querySelector('[name^="type_"]').value;
        const allowedExtensions = (FILE_VALIDATION[type] || "").split(',').map(ext => ext.trim().toLowerCase());
        const filesThisTime = Array.from(input.files).filter(file => {
            const fileExt = `.${file.name.split('.').pop().toLowerCase()}`;
            const isAllowed = input.name === 'trigger_file_upload'
                ? file.type.startsWith('image/')
                : (allowedExtensions.includes('*') || allowedExtensions.includes(fileExt));

            if (!isAllowed) {
                console.warn(`Arquivo bloqueado por tipo inválido: ${file.name}`);
            }
            return isAllowed;
        });

        if (filesThisTime.length === 0) {
            input.value = "";
            return;
        }

        if (input.name === 'trigger_file_upload') {
            const previewId = `preview-trig-${cardId}`;
            console.log(previewId)
            const container = document.getElementById(previewId);
            if (container) container.innerHTML = '';
            renderSinglePreview(input, previewId);
        } else {
            const previewBox = document.getElementById(`preview-dest-${cardId}`);
            if (previewBox) {
                renderMultiplePreviews(filesThisTime, previewBox);

                if (!pendingFiles[cardId]) pendingFiles[cardId] = new DataTransfer();
                filesThisTime.forEach(f => {
                    const alreadyExists = Array.from(pendingFiles[cardId].files)
                        .some(extFile => extFile.name === f.name && extFile.size === f.size);
                    if (!alreadyExists) {
                        pendingFiles[cardId].items.add(f);
                    }
                });

                input.files = pendingFiles[cardId].files;
            }
        }
    },

    addCard(section) {
        const container = document.getElementById(`container-${section}s`);
        const template = document.getElementById('template-rule-card');
        if (!container || !template) return;

        const clone = template.content.cloneNode(true);
        const uniqueIdx = Date.now();
        const shortId = Math.random().toString(36).substring(2, 10);

        const card = clone.querySelector('.rule-card');
        card.id = `card-${uniqueIdx}`;
        card.dataset.section = section;
        card.querySelector('[name="rule_id"]').value = shortId;

        if (section === 'no-trigger') {
            const matcherSelect = card.querySelector('[name^="matcher_"]');
            if (matcherSelect) {
                // 1. Define o valor padrão obrigatório para fallbacks
                matcherSelect.value = 'always';

                // 2. Localiza o label pai e esconde completamente
                const labelWrapper = matcherSelect.closest('label');
                if (labelWrapper) {
                    labelWrapper.style.display = 'none';
                }
            }
        }

        container.appendChild(clone);
        this.refreshCardUI(card);

        // Scroll suave para o novo card
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
};


TriggersEditor.init();
window.addCard = (section) => TriggersEditor.addCard(section);

window.switchTab = (tabId) => {
    console.log(`Trocando para aba: ${tabId}`);


    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
        content.style.display = 'none';
    });

    const activeContent = document.getElementById(`tab-${tabId}`);
    if (activeContent) {
        activeContent.classList.add('active');
        activeContent.style.display = 'block';
    }

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    const activeBtn = document.getElementById(`btn-tab-${tabId}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
};

document.addEventListener('input', (e) => {
    if (e.target.matches('input[name="chance"]')) {
        const card = e.target.closest('.rule-card');
        const display = card.querySelector('.chance-display');
        if (display) {
            const val = parseFloat(e.target.value) * 100;
            display.textContent = `${val.toFixed(1)}%`;
        }
    }
});

let longPressTimer;
const LONG_PRESS_DURATION = 500; // ms

document.addEventListener('mousedown', (e) => {
    const item = e.target.closest('.preview-item');
    if (!item) return;
    longPressTimer = setTimeout(() => {
        openQuickPreview(item);
        longPressTimer = null;
    }, LONG_PRESS_DURATION);
});

document.addEventListener('mouseup', (e) => {
    const item = e.target.closest('.preview-item');
    if (!item) {
        clearTimeout(longPressTimer);
        return;
    }
    if (longPressTimer) {
        clearTimeout(longPressTimer);
        handleItemInteraction(item);
    }
});

function syncInputState(cardId, fileInput) {
    if (pendingFiles[cardId]) {
        fileInput.files = pendingFiles[cardId].files;
        console.log(`[Sync] Card ${cardId}: ${fileInput.files.length} arquivos no buffer.`);
    }
}

function handleItemInteraction(item) {
    const card = item.closest('.rule-card');
    const cardId = card.id.replace('card-', '');
    const fileInput = card.querySelector('input[type="file"]');

    if (item.classList.contains('new-file')) {
        const fileNameToRemove = item.dataset.fileName;

        if (pendingFiles[cardId]) {
            const dt = new DataTransfer();
            const { files } = pendingFiles[cardId];

            for (let i = 0; i < files.length; i++) {
                if (files[i].name !== fileNameToRemove) {
                    dt.items.add(files[i]);
                }
            }

            pendingFiles[cardId] = dt;
            syncInputState(cardId, fileInput);
            fileInput.files = dt.files;
        }

        const img = item.querySelector('img');
        if (img) URL.revokeObjectURL(img.src);
        item.remove();

        console.log(`Upload cancelado: ${fileNameToRemove}`);
    } else {
        item.classList.toggle('marked-for-delete');
        const input = item.querySelector('input[type="hidden"]');
        if (input) {
            input.disabled = item.classList.contains('marked-for-delete');
        }
    }
}

document.addEventListener('contextmenu', (e) => {
    if (e.target.closest('.preview-item')) e.preventDefault();
});

async function openQuickPreview(item) {
    const img = item.querySelector('img');
    const source = img ? img.src : (item.dataset.audioSrc || item.dataset.path);
    const fileName = item.dataset.fileName || item.dataset.path?.split('/').pop() || "Arquivo";
    const ext = fileName.split('.').pop().toLowerCase();

    let modal = document.querySelector('.preview-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.className = 'preview-modal';
        modal.onclick = (e) => { if (e.target === modal) modal.classList.remove('active'); };
        document.body.appendChild(modal);
    }

    modal.innerHTML = '<div class="loader">Carregando...</div>'; // Feedback visual
    modal.classList.add('active');

    // Lógica para Documentos (JSON e TXT)
    if (['json', 'txt'].includes(ext)) {
        try {
            const response = await fetch(source);
            let content = await response.text();

            if (ext === 'json') {
                try {
                    content = JSON.stringify(JSON.parse(content), null, 2);
                } catch (e) { /* Se o JSON for inválido, mostra texto puro */ }
            }

            modal.innerHTML = `
                <div class="text-preview-container" style="background: #1e1e1e; color: #d4d4d4; padding: 20px; border-radius: 8px; max-width: 80vw; max-height: 80vh; overflow: auto; font-family: 'Courier New', monospace;">
                    <div style="border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 10px; display: flex; justify-content: space-between;">
                        <span>📄 ${fileName}</span>
                        <span style="cursor:pointer" onclick="this.closest('.preview-modal').classList.remove('active')">✖</span>
                    </div>
                    <pre style="margin: 0; white-space: pre-wrap; font-size: 13px;">${content.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</pre>
                </div>
            `;
        } catch (err) {
            modal.innerHTML = '<div style="color: white;">Erro ao carregar documento.</div>';
        }
    }
    // Lógica para Áudio
    else if (['mp3', 'ogg', 'wav', 'm4a'].includes(ext) || source.startsWith('blob:')) {
        modal.innerHTML = `
            <div class="audio-preview-container" style="background: var(--card-background); padding: 20px; border-radius: 8px; text-align: center; min-width: 320px;">
                <div style="font-size: 40px;">🎵</div>
                <p style="font-size: 0.8rem;">${fileName}</p>
                <audio src="${source}" autoplay controls style="width: 100%;"></audio>
            </div>
        `;
    }
    // Lógica para Imagem/Vídeo
    else {
        const isVideo = ['mp4', 'webm'].includes(ext);
        modal.innerHTML = isVideo
            ? `<video src="${source}" autoplay controls style="max-width: 90vw; max-height: 85vh;"></video>`
            : `<img src="${source}" style="max-width: 90vw; max-height: 85vh; border-radius: 8px;">`;
    }
}