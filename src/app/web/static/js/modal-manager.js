import { CONFIG } from './config.js';

export const ModalManager = {
    _modal: null,
    _getModal() {
        if (!this._modal) {
            this._modal = document.querySelector(CONFIG.SELECTORS.previewModal);
            if (!this._modal) {
                this._modal = document.createElement('div');
                this._modal.className = 'preview-modal';
                this._modal.onclick = (e) => {
                    if (e.target === this._modal) this.close();
                };
                document.body.appendChild(this._modal);
            }
        }
        return this._modal;
    },
    close() {
        const modal = this._getModal();
        modal.classList.remove('active');
        modal.innerHTML = '';
    },
    async open(sourceUrl, fileName) {
        const modal = this._getModal();
        const ext = fileName.split('.').pop().toLowerCase();

        modal.innerHTML = '<div class="loader">Carregando...</div>';
        modal.classList.add('active');

        try {
            if (['json', 'txt'].includes(ext)) {
                await this._renderText(modal, sourceUrl, fileName, ext);
            } else if (['mp3', 'ogg', 'wav', 'm4a'].includes(ext)) {
                this._renderAudio(modal, sourceUrl, fileName);
            } else if (['mp4', 'webm'].includes(ext)) {
                this._renderVideo(modal, sourceUrl);
            } else {
                this._renderImage(modal, sourceUrl);
            }
        } catch (err) {
            modal.innerHTML = '<div style="color: white; padding: 20px;">Erro ao carregar preview.</div>';
        }
    },

    async _renderText(container, url, name, ext) {
        const response = await fetch(url);
        let content = await response.text();

        if (ext === 'json') {
            try { content = JSON.stringify(JSON.parse(content), null, 2); } catch (e) { }
        }

        // Criamos um wrapper interno para garantir as margens
        container.innerHTML = `
        <div class="text-preview-wrapper">
            <div class="text-preview-content">
                <pre><code>${content.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</code></pre>
            </div>
        </div>
    `;
    },

    _renderAudio(container, url, name) {
        container.innerHTML = `
            <div class="audio-preview-box">
                <div style="font-size: 40px;">🎵</div>
                <p>${name}</p>
                <audio src="${url}" autoplay controls></audio>
            </div>
        `;
    },

    _renderImage(container, url) {
        container.innerHTML = `<img src="${url}" class="modal-img-content">`;
    },

    _renderVideo(container, url) {
        container.innerHTML = `<video src="${url}" autoplay controls class="modal-video-content"></video>`;
    }
};