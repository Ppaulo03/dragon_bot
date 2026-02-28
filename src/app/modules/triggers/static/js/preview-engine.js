export const PreviewEngine = {
    _createContainer(fileName, isNew = true) {
        const item = document.createElement('div');
        item.className = `preview-item ${isNew ? 'new-file' : ''}`;
        item.dataset.fileName = fileName;
        item.style = "position: relative; display: inline-block; cursor: pointer;";
        return item;
    },
    renderImage(fileURL) {
        return `<img src="${fileURL}" style="height: 60px; width: 60px; object-fit: cover; border-radius: 4px; border: 1px solid #333; pointer-events: none;">`;
    },

    renderIcon(ext) {
        const icons = {
            audio: '🎵',
            doc: '📄',
            json: 'curly_braces'
        };
        const icon = ['mp3', 'ogg', 'wav', 'm4a'].includes(ext) ? icons.audio : icons.doc;

        return `
            <div class="file-icon-wrapper" style="width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; background: #1e293b; border-radius: 4px; pointer-events: none;">
                <span style="font-size: 20px;">${icon}</span>
            </div>`;
    },

    createPreviewElement(file, isRemote = false) {
        const fileName = file.name;
        const fileURL = isRemote ? file.url : URL.createObjectURL(file);
        const ext = fileName.split('.').pop().toLowerCase();

        const container = this._createContainer(fileName, !isRemote);

        const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
        if (imageExtensions.includes(ext)) {
            container.innerHTML = this.renderImage(fileURL);
            container.dataset.sourceUrl = fileURL;
        } else {
            container.innerHTML = this.renderIcon(ext);
            container.dataset.sourceUrl = fileURL;
        }

        return container;
    },

    renderTriggerPreview(file, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const url = URL.createObjectURL(file);
        container.innerHTML = `<img src="${url}" style="max-height: 80px; border-radius: 4px; border: 2px solid #3b82f6;">`;
    },

    getSource(item) {

        if (item.classList.contains('new-file')) {
            return item.dataset.sourceUrl;
        }
        const img = item.querySelector('img');
        if (img && img.src) {
            return img.src;
        }
        return item.dataset.path || item.getAttribute('data-src');
    }
};