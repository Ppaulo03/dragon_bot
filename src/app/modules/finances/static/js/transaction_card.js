/**
 * Dragon Finance - Transaction Card Component
 * Gerencia o comportamento individual de cada card de transação.
 */

/**
 * Ponto de entrada para inicializar um card (chamado pelo list.js)
 */
function initTransactionCard(cardElement) {
    const txId = cardElement.id.replace('tx-card-', '');
    const currentCatId = cardElement.dataset.currentCat;

    if (currentCatId) {
        hydrateCategories(txId, currentCatId);
    }
}

/**
 * Reconstrói a árvore de categorias (Pai -> Filho)
 */
function hydrateCategories(txId, catId) {
    const lv3 = categoryTree.find(c => c.id === catId);
    if (!lv3) return;

    const lv2 = categoryTree.find(c => c.id === lv3.parent_id);
    if (!lv2) return;

    const lv1 = categoryTree.find(c => c.id === lv2.parent_id);
    if (!lv1) return;

    // Seta Nível 1
    const s1 = document.getElementById(`lv1-${txId}`);
    if (s1) s1.value = lv1.id;

    // Popula e seta Nível 2
    updateSelectElement(`lv2-${txId}`, lv1.id, "Grupo");
    const s2 = document.getElementById(`lv2-${txId}`);
    if (s2) s2.value = lv2.id;

    // Popula e seta Nível 3
    updateSelectElement(`lv3-${txId}`, lv2.id, "Categoria");
    const s3 = document.getElementById(`lv3-${txId}`);
    if (s3) s3.value = lv3.id;

    updateVisuals(txId, catId);
}

/**
 * OnChange para os selects de nível (Cascata)
 */
function filterLevels(txId, level) {
    const currentVal = document.getElementById(`lv${level}-${txId}`).value;

    if (level === 1) {
        updateSelectElement(`lv2-${txId}`, currentVal, "Grupo");
        const lv3 = document.getElementById(`lv3-${txId}`);
        if (lv3) { lv3.innerHTML = '<option value="">Categoria</option>'; lv3.disabled = true; }
    }
    else if (level === 2) {
        updateSelectElement(`lv3-${txId}`, currentVal, "Categoria");
    }
}

function updateSelectElement(elementId, parentId, label) {
    const select = document.getElementById(elementId);
    if (!select) return;

    const children = categoryTree.filter(c => c.parent_id === parentId);
    select.innerHTML = `<option value="">${label}</option>`;

    children.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.name;
        select.appendChild(opt);
    });

    select.disabled = (children.length === 0);
}

function updateVisuals(txId, catId) {
    const card = document.getElementById(`tx-card-${txId}`);
    const iconDiv = document.getElementById(`icon-${txId}`);
    const cat = categoryTree.find(c => c.id === catId);

    if (!cat || !card || !iconDiv) return;

    if (cat.icon) {
        iconDiv.innerHTML = cat.icon.includes('fa-') ? `<i class="fas ${cat.icon}"></i>` : cat.icon;
    }

    if (cat.color) {
        card.style.borderLeft = `6px solid ${cat.color}`;
        card.style.backgroundColor = `${cat.color}0D`;
    }
}

/**
 * API Patch
 */
async function updateTx(txId, payload) {
    if (payload.category_id) updateVisuals(txId, payload.category_id);

    payload.is_category_automatic = false;

    try {
        const res = await fetch(`/api/internal/finance/transactions/${txId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const statusLabel = document.getElementById(`status-${txId}`);
            if (statusLabel) {
                statusLabel.textContent = '👤 Revisado';
                statusLabel.style.color = 'var(--primary)';
            }
            const card = document.getElementById(`tx-card-${txId}`);
            card.style.opacity = '0.5';
            setTimeout(() => card.style.opacity = '1', 150);
        }
    } catch (err) {
        console.error("Erro:", err);
    }
}

async function updateTx(txId, payload) {
    const card = document.getElementById(`tx-card-${txId}`);

    // 1. Feedback Visual: Indica que o salvamento iniciou
    if (card) {
        card.classList.add('saving');
        card.classList.remove('saved'); // Limpa estados anteriores
    }

    try {
        // 2. Chamada para o seu Backend
        const response = await fetch(`/api/internal/finance/transactions/${txId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            // 3. Sucesso: Aplica animação de confirmação (Ref: image_65ceac.png)
            if (card) {
                card.classList.remove('saving');
                card.classList.add('saved');

                // Remove a classe de animação após 1.5s
                setTimeout(() => card.classList.remove('saved'), 1500);
            }

            // 4. Se a alteração foi de categoria, atualizamos o badge de status
            if (payload.category_id) {
                const statusBadge = document.getElementById(`status-${txId}`);
                if (statusBadge) {
                    statusBadge.innerHTML = '👤 Revisado';
                    statusBadge.className = 'status-badge user'; // Muda para o estilo verde
                }
            }
        } else {
            throw new Error('Falha ao salvar');
        }
    } catch (error) {
        console.error("Erro Dragon Finance:", error);
        if (card) {
            card.classList.remove('saving');
            card.style.borderColor = 'var(--negative)'; // Indica erro visualmente
        }
    }
}

/**
 * Gerencia a lógica de filtragem hierárquica dos selects (Lv1 -> Lv2 -> Lv3)
 */
/**
 * Atualiza os dados da transação via API com feedback visual de alta densidade.
 */
async function updateTx(txId, payload) {
    const card = document.getElementById(`tx-card-${txId}`);

    // 1. Feedback Visual: Indica que o salvamento iniciou
    if (card) {
        card.classList.add('saving');
        card.classList.remove('saved'); // Limpa estados anteriores
    }

    try {
        // 2. Chamada para o seu Backend
        const response = await fetch(`/api/internal/finance/transactions/${txId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            // 3. Sucesso: Aplica animação de confirmação (Ref: image_65ceac.png)
            if (card) {
                card.classList.remove('saving');
                card.classList.add('saved');

                // Remove a classe de animação após 1.5s
                setTimeout(() => card.classList.remove('saved'), 1500);
            }

            // 4. Se a alteração foi de categoria, atualizamos o badge de status
            if (payload.category_id) {
                const statusBadge = document.getElementById(`status-${txId}`);
                if (statusBadge) {
                    statusBadge.innerHTML = '👤 Revisado';
                    statusBadge.className = 'status-badge user'; // Muda para o estilo verde
                }
            }
        } else {
            throw new Error('Falha ao salvar');
        }
    } catch (error) {
        console.error("Erro Dragon Finance:", error);
        if (card) {
            card.classList.remove('saving');
            card.style.borderColor = 'var(--negative)'; // Indica erro visualmente
        }
    }
}

/**
 * Gerencia a lógica de filtragem hierárquica dos selects (Lv1 -> Lv2 -> Lv3)
 */
async function filterLevels(txId, level) {
    const currentSelect = document.getElementById(`lv${level}-${txId}`);
    const nextLevel = level + 1;
    const nextSelect = document.getElementById(`lv${nextLevel}-${txId}`);
    const thirdSelect = document.getElementById(`lv3-${txId}`);

    if (!currentSelect.value) {
        if (nextSelect) { nextSelect.disabled = true; nextSelect.value = ""; }
        if (thirdSelect && level === 1) { thirdSelect.disabled = true; thirdSelect.value = ""; }
        return;
    }

    try {
        const response = await fetch(`/api/internal/finance/categories?parent_id=${currentSelect.value}`);
        const categories = await response.json();

        if (nextSelect) {
            nextSelect.innerHTML = `<option value="">${level === 1 ? 'Grupo' : 'Categoria'}</option>`;
            categories.forEach(c => {
                nextSelect.innerHTML += `<option value="${c.id}">${c.name}</option>`;
            });
            nextSelect.disabled = false;
        }
    } catch (e) {
        console.error("Erro ao carregar subcategorias:", e);
    }
}