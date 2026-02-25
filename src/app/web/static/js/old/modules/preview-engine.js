/**
 * Gera preview para múltiplos ficheiros (usado na zona de resposta)
 */
export function renderMultiplePreviews(incomingFiles, previewBox) {
    incomingFiles.forEach(file => {
        const fileURL = URL.createObjectURL(file);
        const ext = file.name.split('.').pop().toLowerCase();

        const item = document.createElement('div');
        item.className = 'preview-item new-file';
        item.dataset.fileName = file.name;
        item.title = `Novo arquivo: ${file.name}`;
        item.style = "position: relative; display: inline-block; cursor: pointer;";

        if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) {
            item.innerHTML = `<img src="${fileURL}" style="height: 60px; width: 60px; object-fit: cover; border-radius: 4px; border: 1px solid var(--border); pointer-events: none;">`;
        } else {
            const icon = ['mp3', 'ogg', 'wav'].includes(ext) ? '🎵' : '📄';
            item.dataset.audioSrc = fileURL;
            item.innerHTML = `
                <div style="width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; background: #1e293b; border-radius: 4px; pointer-events: none;">
                    <span>${icon}</span>
                </div>`;
            if (['json', 'txt'].includes(ext)) {
                item.dataset.audioSrc = fileURL; // Reutilizamos o dataset para a URL do Blob
                item.dataset.fileName = file.name;
                item.innerHTML = `<div class="file-icon">📄</div>`; // Seu estilo de ícone aqui
            }
        }

        previewBox.appendChild(item);
    });
}



/**
 * Gera preview para um único ficheiro (usado no Gatilho/Trigger)
 */
export function renderSinglePreview(input, containerId) {
    const file = input.files[0];
    const container = document.getElementById(containerId);
    if (!file || !container) return;

    const fileURL = URL.createObjectURL(file);
    container.innerHTML = `<img src="${fileURL}" style="max-height: 80px; border-radius: 4px; border: 2px solid #3b82f6;">`;
}

/**
 * Procura por elementos que precisam de preview de texto do servidor
 * Ex: cards carregados que apontam para um .txt no S3
 */
export function initRemotePreviews() {
    document.querySelectorAll('.fetch-preview-compact').forEach(el => {
        const url = el.getAttribute('data-src');
        console.log("Tentando carregar preview de:", url);
        if (!url || el.dataset.loaded === "true") return;

        fetch(url)
            .then(response => response.ok ? response.text() : Promise.reject())
            .then(data => {
                el.innerText = data.substring(0, 200) + (data.length > 200 ? '...' : '');
                el.dataset.loaded = "true";
            })
            .catch(() => {
                el.innerText = "Conteúdo no servidor (ver ao editar)";
                el.style.opacity = "0.6";
            });
    });
}