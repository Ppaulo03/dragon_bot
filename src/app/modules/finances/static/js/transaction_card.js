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
    const lv1Select = document.getElementById(`lv1-${txId}`);

    // Garante que o Nível 2 comece populado e habilitado se o Tipo estiver selecionado
    if (lv1Select && lv1Select.value) {
        updateSelectElementLv2(txId, lv1Select.value, null);
    }

    if (currentCatId) {
        hydrateCategories(txId, currentCatId);
    }
}

/**
 * Reconstrói a árvore de categorias (Tipo -> Categoria -> Subcategoria)
 */
function hydrateCategories(txId, catId) {
    if (!catId) return;

    // Busca insensitiva para IDs (UUIDs)
    const catOrSub = categoryTree.find(c => String(c.id).toLowerCase() === String(catId).toLowerCase());
    if (!catOrSub) return;

    let lv2Id, lv3Id;
    let type = catOrSub.transaction_type;

    // parent_id pode ser null ou string vazia para raízes
    if (!catOrSub.parent_id) {
        // É uma Categoria Raiz (Lv2 no UI)
        lv2Id = catOrSub.id;
        lv3Id = "";
    } else {
        // É uma Subcategoria (Lv3 no UI)
        lv3Id = catOrSub.id;
        lv2Id = catOrSub.parent_id;
    }

    // Seta Nível 1 (Tipo)
    const s1 = document.getElementById(`lv1-${txId}`);
    if (s1 && type) s1.value = type;

    // Popula e seta Nível 2 (Categoria)
    updateSelectElementLv2(txId, type, lv2Id);

    // Popula e seta Nível 3 (Subcategoria) se houver
    if (lv2Id) {
        updateSelectElementLv3(txId, lv2Id, lv3Id);
    }

    updateVisuals(txId, catId);
}

/**
 * OnChange para os selects de nível (Cascata)
 */
async function filterLevels(txId, level) {
    const currentSelect = document.getElementById(`lv${level}-${txId}`);
    const nextLevel = level + 1;
    const nextSelect = document.getElementById(`lv${nextLevel}-${txId}`);
    const thirdSelect = document.getElementById(`lv3-${txId}`);

    if (!currentSelect || !currentSelect.value) {
        if (nextSelect) { nextSelect.disabled = true; nextSelect.value = ""; }
        if (thirdSelect && level === 1) { thirdSelect.disabled = true; thirdSelect.value = ""; }
        return;
    }

    const val = currentSelect.value;

    if (level === 1) {
        // Nivel 1 -> Nivel 2: Usa categoryTree local para maior velocidade
        updateSelectElementLv2(txId, val, null);
        if (thirdSelect) {
            thirdSelect.innerHTML = '<option value="">Categoria</option>';
            thirdSelect.disabled = true;
            thirdSelect.value = "";
        }
    } else if (level === 2) {
        // Nivel 2 -> Nivel 3: Usa categoryTree local
        updateSelectElementLv3(txId, val, null);
    }
}

function updateSelectElementLv2(txId, type, selectedId) {
    const select = document.getElementById(`lv2-${txId}`);
    if (!select) return;

    // Filtra raízes do tipo especificado
    const children = categoryTree.filter(c => !c.parent_id && c.transaction_type === type);
    select.innerHTML = '<option value="">Grupo</option>';

    children.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.name;
        if (selectedId && String(c.id).toLowerCase() === String(selectedId).toLowerCase()) {
            opt.selected = true;
        }
        select.appendChild(opt);
    });

    select.disabled = false;
}

function updateSelectElementLv3(txId, parentId, selectedId) {
    const select = document.getElementById(`lv3-${txId}`);
    if (!select) return;

    // Filtra filhos do parent especificado
    const children = categoryTree.filter(c =>
        c.parent_id && String(c.parent_id).toLowerCase() === String(parentId).toLowerCase()
    );
    select.innerHTML = '<option value="">Categoria</option>';

    children.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.name;
        if (selectedId && String(c.id).toLowerCase() === String(selectedId).toLowerCase()) {
            opt.selected = true;
        }
        select.appendChild(opt);
    });

    select.disabled = (children.length === 0);
}

function updateVisuals(txId, catId) {
    const card = document.getElementById(`tx-card-${txId}`);
    if (!catId) return;

    const cat = categoryTree.find(c => String(c.id).toLowerCase() === String(catId).toLowerCase());
    if (!cat || !card) return;

    if (cat.color) {
        card.style.borderLeft = `6px solid ${cat.color}`;
    }
}

/**
 * Atualiza os dados da transação via API com feedback visual de alta densidade.
 */
async function updateTx(txId, payload) {
    const card = document.getElementById(`tx-card-${txId}`);

    // 1. Feedback Visual: Indica que o salvamento iniciou
    if (card) {
        card.classList.add('saving');
        card.classList.remove('saved');
    }

    try {
        // 2. Chamada para o Backend
        const response = await fetch(`/api/internal/finance/transactions/${txId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            // 3. Sucesso: Aplica animação de confirmação
            if (card) {
                card.classList.remove('saving');
                card.classList.add('saved');

                // Remove a classe de animação após 1.5s
                setTimeout(() => card.classList.remove('saved'), 1500);
            }

            // 4. Se a alteração foi de categoria, atualizamos o badge de status e os visuais
            if (payload.category_id) {
                updateVisuals(txId, payload.category_id);
                const statusBadge = document.getElementById(`status-${txId}`);
                if (statusBadge) {
                    statusBadge.innerHTML = '👤 Revisado';
                    statusBadge.className = 'status-badge user';
                }
            }
        } else {
            throw new Error('Falha ao salvar');
        }
    } catch (error) {
        console.error("Erro Dragon Finance:", error);
        if (card) {
            card.classList.remove('saving');
            card.style.borderColor = 'var(--negative)';
        }
    }
}
