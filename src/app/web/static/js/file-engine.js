import { CONFIG } from './config.js';
import { FileState } from './state.js';
import { PreviewEngine } from './preview-engine.js';

export const FileEngine = {
    isValid(file, cardType, isTrigger = false) {
        if (isTrigger) {
            return file.type.startsWith('image/');
        }

        const allowedStr = CONFIG.VALIDATION[cardType] || CONFIG.VALIDATION.default;
        if (allowedStr === '*') return true;

        const allowedExts = allowedStr.split(',').map(ext => ext.trim().toLowerCase());
        const fileExt = `.${file.name.split('.').pop().toLowerCase()}`;

        return allowedExts.includes(fileExt);
    },
    handleUpload(input, cardId, type) {
        const files = Array.from(input.files);
        const validFiles = files.filter(f => this.isValid(f, type));

        if (validFiles.length === 0) return [];

        // Salva no estado global
        FileState.addFiles(cardId, validFiles);

        const cleanId = cardId.replace('card-', '');
        const previewContainer = document.getElementById(`preview-dest-${cleanId}`)
            || document.querySelector(`#card-${cleanId} .sutil-preview`);

        if (previewContainer) {
            validFiles.forEach(file => {
                const previewEl = PreviewEngine.createPreviewElement(file);
                previewEl.classList.add('new-file');
                previewContainer.appendChild(previewEl);
            });

            const msg = previewContainer.parentElement.querySelector('.no-files-msg');
            if (msg) msg.style.display = 'none';
        }

        return validFiles; // Retorna para o main.js saber que deu certo
    },
    removeFile(cardId, fileName, inputElement) {
        const updatedFiles = FileState.removeFile(cardId, fileName);
        if (inputElement) {
            inputElement.files = updatedFiles;
        }
        return updatedFiles;
    },
    revalidateState(cardId, newType) {
        const currentFiles = Array.from(FileState.getFiles(cardId).files);
        const dt = new DataTransfer();
        let removedAny = false;

        currentFiles.forEach(file => {
            if (this.isValid(file, newType)) {
                dt.items.add(file);
            } else {
                removedAny = true;
                console.warn(`Arquivo ${file.name} removido: incompatível com ${newType}`);
            }
        });

        if (removedAny) {
            FileState.updateWholeState(cardId, dt); // Precisaremos criar esse método no state
        }
        return dt.files;
    }
};