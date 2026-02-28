const _fileStore = new Map();

export const FileState = {
    getFiles(cardId) {
        if (!_fileStore.has(cardId)) {
            _fileStore.set(cardId, new DataTransfer());
        }
        return _fileStore.get(cardId);
    },
    addFiles(cardId, newFiles) {
        const dt = this.getFiles(cardId);
        const existingFiles = Array.from(dt.files);

        newFiles.forEach(file => {
            const isDuplicate = existingFiles.some(f =>
                f.name === file.name && f.size === file.size
            );

            if (!isDuplicate) {
                dt.items.add(file);
            }
        });

        return dt.files;
    },
    removeFile(cardId, fileName) {
        const currentFiles = Array.from(this.getFiles(cardId).files);
        const newDt = new DataTransfer();

        currentFiles.forEach(file => {
            if (file.name !== fileName) {
                newDt.items.add(file);
            }
        });

        _fileStore.set(cardId, newDt);
        return newDt.files;
    },
    updateWholeState(cardId, dataTransfer) {
        _fileStore.set(cardId, dataTransfer);
    },
    clearCardState(cardId) {
        _fileStore.delete(cardId);
    }
};