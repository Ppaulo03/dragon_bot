import { CONFIG } from './config.js';
import { FileState } from './state.js';

export const FileEngine = {
    isValid(file, cardType, isTrigger = false) {
        if (isTrigger) return file.type.startsWith('image/');

        const allowedStr = CONFIG.VALIDATION[cardType] || CONFIG.VALIDATION.default;
        if (allowedStr === '*') return true;

        const allowedExts = allowedStr.split(',').map(ext => ext.trim().toLowerCase());
        const fileExt = `.${file.name.split('.').pop().toLowerCase()}`;

        return allowedExts.includes(fileExt);
    },

    handleUpload(inputElement, cardId, type) {
        const files = Array.from(inputElement.files);
        const validFiles = files.filter(f => this.isValid(f, type));

        if (validFiles.length > 0) {
            const updatedFiles = FileState.addFiles(cardId, validFiles);
            inputElement.files = updatedFiles;
        }
        return validFiles;
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
        let changed = false;

        currentFiles.forEach(file => {
            if (this.isValid(file, newType)) {
                dt.items.add(file);
            } else {
                changed = true;
                console.warn(`[Engine] Arquivo ${file.name} removido: incompatível com o novo tipo ${newType}`);
            }
        });

        if (changed) {
            FileState.updateWholeState(cardId, dt);
        }
        return dt.files;
    }
};