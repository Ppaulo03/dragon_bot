const _fileStore = new Map();

export const FileState = {
    getFiles(cardId) {
        return _fileStore.get(cardId) || new DataTransfer();
    },

    addFiles(cardId, newFiles) {
        const dt = this.getFiles(cardId);
        const existingFiles = Array.from(dt.files);

        newFiles.forEach(file => {
            const isDuplicate = existingFiles.some(f => f.name === file.name && f.size === file.size);
            if (!isDuplicate) {
                dt.items.add(file);
            }
        });

        _fileStore.set(cardId, dt);
        return dt.files;
    },

    removeFile(cardId, fileName) {
        const dt = new DataTransfer();
        const currentFiles = Array.from(this.getFiles(cardId).files);

        currentFiles.forEach(file => {
            if (file.name !== fileName) {
                dt.items.add(file);
            }
        });

        _fileStore.set(cardId, dt);
        return dt.files;
    },
    updateWholeState(cardId, dataTransfer) {
        _fileStore.set(cardId, dataTransfer);
    }
};