/* ============================================================
   manage.js — Onionary — Recipe Management
   ============================================================ */

const API = '';  // same origin

// ── Auth Helper ────────────────────────────────────────────────
function getAuthHeaders(extra = {}) {
  const token = window.WSWEAuth ? window.WSWEAuth.token : null;
  const h = { ...extra };
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}

// ── State ──────────────────────────────────────────────────────
let allRecipes = [];
let allTags = [];
let editRecipeId = null;
let recipeModalMode = 'manual';

// Form DOM refs
const $modalOverlay = document.getElementById('edit-modal');
const $deleteModal = document.getElementById('delete-modal');
const $manageGrid = document.getElementById('manage-grid');
const $listBadge = document.getElementById('list-badge');
const $recipeSearch = document.getElementById('recipe-search');

const $recipeForm = document.getElementById('recipe-form');
const $modalTitle = document.getElementById('modal-title');
const $recipeName = document.getElementById('recipe-name');
const $recipeIcon = document.getElementById('recipe-icon');
const $recipeServings = document.getElementById('recipe-servings');
const $recipeKcal = document.getElementById('recipe-kcal');
const $recipeActiveTime = document.getElementById('recipe-active-time');
const $recipeTotalTime = document.getElementById('recipe-total-time');
const $recipeNotes = document.getElementById('recipe-notes');
const $recipeModeSwitch = document.getElementById('recipe-mode-switch');
const $btnModeManual = document.getElementById('btn-mode-manual');
const $btnModeImport = document.getElementById('btn-mode-import');
const $importPanel = document.getElementById('import-panel');
const $importSource = document.getElementById('import-source');
const $importUrl = document.getElementById('import-url');
const $importHtml = document.getElementById('import-html');
const $importHtmlFallback = document.getElementById('import-html-fallback');
const $importStatus = document.getElementById('import-status');
const $btnImportRecipe = document.getElementById('btn-import-recipe');
const $btnSaveRecipe = document.getElementById('btn-save-recipe');
const $btnCancelModal = document.getElementById('btn-cancel-modal');

// Tags
const $editTagSelector = document.getElementById('edit-tag-selector');
const $newTagInput = document.getElementById('new-tag-input');
const $tagSuggestions = document.getElementById('tag-suggestions');
let selectedTags = new Set();

// Dynamic Lists
const $ingredientsList = document.getElementById('ingredients-list');
const $stepsList = document.getElementById('steps-list');
const $orderDialog = document.getElementById('recipe-order');
const $orderRows = document.getElementById('recipe-order-rows');
const $groupName = document.getElementById('recipe-group-name');
let orderList;
let orderGroups;
let draggingRow;

// Toast
const $toast = document.getElementById('toast');


// ── Init ───────────────────────────────────────────────────────
async function init() {
  // Attach all event listeners synchronously so UI is responsive
  // Search
  $recipeSearch.addEventListener('input', filterCards);

  // Auth sync
  window.addEventListener('wswe_auth_changed', async () => {
    await loadTags();
    await loadRecipes();
  });

  // Modal close handlers
  document.getElementById('btn-close-modal').addEventListener('click', closeEditModal);
  document.getElementById('btn-cancel-modal').addEventListener('click', closeEditModal);
  document.getElementById('btn-create-recipe').addEventListener('click', openCreateModal);

  // Tag add
  document.getElementById('btn-add-tag').addEventListener('click', () => addNewTag());
  $newTagInput.addEventListener('input', renderTagSuggestions);
  $newTagInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addNewTag();
    }
  });

  // Dynamic lists handlers
  document.getElementById('btn-add-ingredient').addEventListener('click', () => addIngredientRow());
  document.getElementById('btn-add-step').addEventListener('click', () => addStepRow());
  document.getElementById('reorder-ingredients').addEventListener('click', () => openOrder($ingredientsList, 'recipe.order-ingredients'));
  document.getElementById('reorder-steps').addEventListener('click', () => openOrder($stepsList, 'recipe.order-steps'));
  document.getElementById('recipe-group-form').addEventListener('submit', event => {
    event.preventDefault();
    const name = $groupName.value.trim();
    if (!name) return;
    orderGroups.add(name);
    $groupName.value = '';
    renderOrder();
  });
  $orderDialog.addEventListener('close', () => updateGroupHeadings(orderList));

  // Save recipe
  document.getElementById('btn-save-recipe').addEventListener('click', saveRecipe);
  $btnModeManual.addEventListener('click', () => setRecipeModalMode('manual'));
  $btnModeImport.addEventListener('click', () => setRecipeModalMode('import'));
  $btnImportRecipe.addEventListener('click', importRecipeIntoForm);

  // Delete modal
  document.getElementById('btn-cancel-delete').addEventListener('click', () => {
    $deleteModal.style.display = 'none';
    recipeToDelete = null;
  });
  document.getElementById('btn-confirm-delete').addEventListener('click', performDelete);

  // Now perform initial data load asynchronously
  await loadTags();
  await loadRecipes();
}

// ── Data Fetching ──────────────────────────────────────────────
async function loadTags() {
  try {
    const res = await fetch(`${API}/tags`, { headers: getAuthHeaders() });
    if (res.ok) allTags = await res.json();
  } catch (e) {
    console.error('Failed to load tags', e);
  }
}

async function loadRecipes() {
  try {
    const res = await fetch(`${API}/recipes`, { headers: getAuthHeaders() });
    allRecipes = await res.json();
    renderRecipes();
  } catch (e) {
    console.error('Failed to load recipes', e);
    toast(window.t('feedback.0'));
  }
}

// ── Search & Render ────────────────────────────────────────────
function filterCards() {
  const query = $recipeSearch.value.toLowerCase().trim();
  let count = 0;
  for (const [index, card] of [...$manageGrid.querySelectorAll('.recipe-card')].entries()) {
    const recipe = allRecipes[index];
    const fields = [recipe.name, ...recipe.tags.map(tag => tag.name), ...recipe.ingredients.map(item => item.name)];
    card.hidden = !fields.some(value => value.toLowerCase().includes(query));
    if (!card.hidden) count++;
  }
  $listBadge.textContent = count;
  $manageGrid.querySelector('.empty-state').hidden = count > 0;
}

function renderRecipes() {
  $manageGrid.innerHTML = allRecipes.map(r => `
    <div class="recipe-card">
      <div class="recipe-card-header">
        <h3>${r.icon ? `<span aria-hidden="true">${esc(r.icon)}</span> ` : ''}${esc(r.name)}</h3>
      </div>
      <div class="recipe-card-meta">
        <span class="meta-chip">${window.t("recipe.servings")}: ${Number(r.servings || 1).toLocaleString(window.I18n.lang, {maximumFractionDigits: 2})}</span>
        ${r.kcal_per_serving ? `<span class="meta-chip"><span class="icon">🔥</span> ${r.kcal_per_serving} kcal</span>` : ''}
        ${r.active_cooking_time_min ? `<span class="meta-chip"><span class="icon">🧅</span> ${r.active_cooking_time_min} ${window.t('feedback.39')}</span>` : ''}
        ${r.total_time_min ? `<span class="meta-chip"><span class="icon">⏱️</span> ${r.total_time_min} ${window.t('feedback.40')}</span>` : ''}
      </div>
      <div class="recipe-card-tags">
        ${r.tags.map(t => `<span class="recipe-tag">${esc(t.name)}</span>`).join('')}
      </div>
      <div class="recipe-card-footer">
        <button class="btn btn-secondary btn-sm" onclick="shareRecipe(${r.id})">${window.t("share.title")}</button>
        <button class="btn btn-secondary btn-sm" onclick="editRecipe(${r.id})">${window.t("ui.1")}</button>
        <button class="btn btn-secondary btn-sm" onclick="promptDelete(${r.id})">${window.t("ui.2")}</button>
      </div>
    </div>
  `).join('') + `<div class="empty-state" style="grid-column: 1 / -1"><div class="icon">🧅</div><p>${window.t('ui.0')}</p></div>`;
  filterCards();
}


// ── Modals & Forms ─────────────────────────────────────────────
function openCreateModal() {
  editRecipeId = null;
  $modalTitle.textContent = window.t('feedback.1');
  $recipeForm.reset();
  $importUrl.value = '';
  $importHtml.value = '';
  $importStatus.textContent = '';
  $importHtmlFallback.style.display = 'none';
  selectedTags.clear();
  $newTagInput.value = '';
  renderEditTags();

  $ingredientsList.innerHTML = '';
  $stepsList.innerHTML = '';
  addIngredientRow();
  addStepRow();
  $recipeModeSwitch.style.display = 'flex';
  setRecipeModalMode('manual');

  $modalOverlay.style.display = 'flex';
}

function closeEditModal(e) {
  if (e) e.preventDefault();
  $modalOverlay.style.display = 'none';
  setRecipeModalMode('manual');
}

function editRecipe(id) {
  const r = allRecipes.find(x => x.id === id);
  if (!r) return;

  editRecipeId = id;
  $recipeIcon.value = r.icon || '';
  $modalTitle.textContent = window.t('feedback.2');
  $recipeModeSwitch.style.display = 'none';
  $importStatus.textContent = '';
  $importHtmlFallback.style.display = 'none';

  $recipeName.value = r.name || '';
  $recipeNotes.value = r.notes || '';
  $recipeServings.value = r.servings || 1;
  $recipeKcal.value = r.kcal_per_serving || '';
  $recipeActiveTime.value = r.active_cooking_time_min || '';
  $recipeTotalTime.value = r.total_time_min || '';

  selectedTags = new Set(r.tags.map(t => t.name));
  $newTagInput.value = '';
  renderEditTags();

  $ingredientsList.innerHTML = '';
  r.ingredients.forEach(ing => addIngredientRow(ing.name, ing.quantity, ing.unit, ing.group_name));
  if (r.ingredients.length === 0) addIngredientRow();

  $stepsList.innerHTML = '';
  const sortedSteps = [...(r.instruction_steps || [])].sort((a, b) => a.step_number - b.step_number);
  sortedSteps.forEach(st => addStepRow(st.description, st.duration_min, st.group_name));
  if (sortedSteps.length === 0) addStepRow();

  $modalOverlay.style.display = 'flex';
}

function setRecipeModalMode(mode) {
  recipeModalMode = mode;
  const isImport = mode === 'import' && !editRecipeId;
  $importPanel.style.display = isImport ? 'block' : 'none';
  $recipeForm.style.display = isImport ? 'none' : 'block';
  $btnSaveRecipe.style.display = isImport ? 'none' : '';
  $btnCancelModal.textContent = isImport ? window.t('feedback.3') : window.t('feedback.4');
  $btnModeManual.classList.toggle('btn-primary', !isImport);
  $btnModeManual.classList.toggle('btn-secondary', isImport);
  $btnModeImport.classList.toggle('btn-primary', isImport);
  $btnModeImport.classList.toggle('btn-secondary', !isImport);
}

async function importRecipeIntoForm() {
  const source = $importSource.value;
  const url = $importUrl.value.trim();
  const html = $importHtml.value.trim();

  if (!url && !html) {
    toast(window.t('feedback.5'));
    return;
  }

  $btnImportRecipe.disabled = true;
  $btnImportRecipe.innerHTML = '<span class="spinner"></span> ' + window.t('feedback.30');
  $importStatus.textContent = window.t('feedback.6');

  try {
    const payload = {
      source,
      url: url || null,
      html: html || null,
    };

    const res = await fetch(source === "onionary" ? `${API}/recipe-shares/preview` : `${API}/recipes/import/parse/html`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(getApiErrorMessage(data));
    }

    applyImportedRecipe(data);
    setRecipeModalMode('manual');
    $importStatus.textContent = window.t('feedback.7');
    toast(window.t('feedback.8'));
  } catch (e) {
    console.error(e);
    $importHtmlFallback.style.display = 'block';
    $importStatus.textContent = e.message || window.t('feedback.9');
    toast(window.t('feedback.10'));
  } finally {
    $btnImportRecipe.disabled = false;
    $btnImportRecipe.textContent = window.t('feedback.11');
  }
}

function getApiErrorMessage(data) {
  if (!data) return 'Could not parse recipe';
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail)) {
    const first = data.detail[0];
    if (first && typeof first.msg === 'string') return first.msg;
  }
  return 'Could not parse recipe';
}

function applyImportedRecipe(recipe) {
  $recipeIcon.value = recipe.icon || '';
  $recipeName.value = recipe.name || '';
  $recipeNotes.value = recipe.notes || '';
  $recipeServings.value = recipe.servings || 1;
  $recipeKcal.value = recipe.kcal_per_serving || '';
  $recipeActiveTime.value = recipe.active_cooking_time_min || '';
  $recipeTotalTime.value = recipe.total_time_min || '';

  selectedTags = new Set(recipe.tags || []);
  renderEditTags();

  $ingredientsList.innerHTML = '';
  (recipe.ingredients || []).forEach(ing => {
    addIngredientRow(ing.name, ing.quantity ?? '', ing.unit || '', ing.group_name || '');
  });
  if ((recipe.ingredients || []).length === 0) addIngredientRow();

  $stepsList.innerHTML = '';
  (recipe.instruction_steps || []).forEach(step => {
    addStepRow(step.description, step.duration_min ?? '', step.group_name || '');
  });
  if ((recipe.instruction_steps || []).length === 0) addStepRow();
}


// ── Tags in Edit Form ──────────────────────────────────────────
function renderEditTags() {
  $editTagSelector.replaceChildren(...Array.from(selectedTags, name => {
    const chip = tagButton(`${name} ×`, () => {
      selectedTags.delete(name);
      renderEditTags();
      $newTagInput.focus();
    });
    chip.classList.add('active');
    chip.setAttribute('aria-label', `${window.t('recipe.remove-tag')} ${name}`);
    return chip;
  }));
  renderTagSuggestions();
}

function tagButton(label, action) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'tag-pill';
  button.textContent = label;
  button.addEventListener('click', action);
  return button;
}

function renderTagSuggestions() {
  const query = $newTagInput.value.trim().toLocaleLowerCase();
  const selected = new Set([...selectedTags].map(name => name.toLocaleLowerCase()));
  const suggestions = query ? allTags.filter(({name}) => {
    const key = name.toLocaleLowerCase();
    return key.includes(query) && !selected.has(key);
  }).slice(0, 6) : [];
  $tagSuggestions.hidden = suggestions.length === 0;
  $tagSuggestions.replaceChildren(...suggestions.map(({name}) => tagButton(name, () => addNewTag(name))));
}

function addNewTag(value = $newTagInput.value) {
  const name = value.trim();
  if (!name) return;
  const key = name.toLocaleLowerCase();
  const known = allTags.find(tag => tag.name.toLocaleLowerCase() === key);
  if (![...selectedTags].some(tag => tag.toLocaleLowerCase() === key)) selectedTags.add(known?.name || name);
  $newTagInput.value = '';
  renderEditTags();
  $newTagInput.focus();
}


// ── Dynamic Rows ───────────────────────────────────────────────
function addIngredientRow(name = '', qty = '', unit = '', group = '') {
  const div = document.createElement('div');
  div.className = 'editor-row ingredient-row';
  div.dataset.group = group || '';
  div.innerHTML = `
    <input type="text" aria-label="${window.t('feedback.31')}" placeholder="${window.t('feedback.31')}" class="ing-name" value="${esc(name)}" />
    <input type="number" aria-label="${window.t('feedback.32')}" placeholder="${window.t('feedback.32')}" class="ing-qty" step="any" value="${esc(qty ?? '')}" />
    <input type="text" aria-label="${window.t('feedback.33')}" placeholder="${window.t('feedback.33')}" class="ing-unit" value="${esc(unit)}" />
  `;
  appendRow($ingredientsList, div);
}

function addStepRow(desc = '', dur = '', group = '') {
  const div = document.createElement('div');
  div.className = 'editor-row step-row';
  div.dataset.group = group || '';
  div.innerHTML = `
    <textarea aria-label="${window.t('feedback.34')}" placeholder="${window.t('feedback.34')}" class="step-desc" rows="2">${esc(desc)}</textarea>
    <input type="number" aria-label="${window.t('feedback.35')}" placeholder="${window.t('feedback.35')}" class="step-dur" value="${esc(dur ?? '')}" />
  `;
  appendRow($stepsList, div);
}

function editorRows(list) { return Array.from(list.querySelectorAll('.editor-row')); }

function appendRow(list, row) {
  const remove = orderButton('✕', window.t('recipe.remove-row'), () => {
    row.remove();
    updateGroupHeadings(list);
  });
  row.append(remove);
  list.append(row);
  updateGroupHeadings(list);
}

function updateGroupHeadings(list) {
  list.querySelectorAll('.editor-group').forEach(group => group.remove());
  let previous = '';
  for (const row of editorRows(list)) {
    const name = row.dataset.group;
    const grouped = name && name !== previous;
    row.classList.toggle('group-member', Boolean(name));
    if (grouped) {
      const heading = document.createElement('h4');
      heading.className = 'editor-group';
      heading.textContent = name;
      row.before(heading);
    }
    previous = name;
  }
}

function openOrder(list, title) {
  orderList = list;
  orderGroups = new Set(editorRows(list).map(row => row.dataset.group).filter(Boolean));
  document.getElementById('recipe-order-title').textContent = window.t(title);
  $groupName.value = '';
  renderOrder();
  $orderDialog.showModal();
}

function orderButton(symbol, label, action) {
  const button = document.createElement('button');
  button.className = 'btn-icon';
  button.type = 'button';
  button.textContent = symbol;
  button.setAttribute('aria-label', label);
  button.title = label;
  button.addEventListener('click', action);
  return button;
}

function renderOrder(focusRow, direction) {
  const rows = editorRows(orderList);
  const items = rows.map((row, index) => {
    const item = document.createElement('li');
    const title = document.createElement('span');
    title.textContent = row.querySelector('.ing-name,.step-desc').value.trim() || `${index + 1}`;
    const up = orderButton('↑', `${window.t('recipe.move-up')} ${title.textContent}`, () => move(rows[index - 1], true, 'up'));
    const down = orderButton('↓', `${window.t('recipe.move-down')} ${title.textContent}`, () => move(rows[index + 1], false, 'down'));
    up.disabled = index === 0;
    down.disabled = index === rows.length - 1;
    const handle = document.createElement('span');
    handle.className = 'order-grabber';
    handle.textContent = '☰';
    handle.draggable = true;
    handle.setAttribute('aria-hidden', 'true');
    handle.addEventListener('dragstart', event => {
      draggingRow = row;
      event.dataTransfer.setData('text/plain', title.textContent);
      event.dataTransfer.effectAllowed = 'move';
    });
    handle.addEventListener('dragend', () => { draggingRow = null; });
    item.addEventListener('dragover', event => { if (draggingRow) event.preventDefault(); });
    item.addEventListener('drop', event => {
      if (!draggingRow || draggingRow === row) return;
      event.preventDefault();
      if (rows.indexOf(draggingRow) < index) row.after(draggingRow);
      else row.before(draggingRow);
      draggingRow = null;
      updateGroupHeadings(orderList);
      renderOrder();
    });
    item.append(title);
    if (orderGroups.size) {
      const select = document.createElement('select');
      select.setAttribute('aria-label', `${window.t('recipe.group-name')} · ${title.textContent}`);
      select.add(new Option(window.t('recipe.ungrouped'), ''));
      for (const name of orderGroups) select.add(new Option(name, name));
      select.value = row.dataset.group;
      select.addEventListener('change', () => {
        row.dataset.group = select.value;
        const last = editorRows(orderList).findLast(other => other !== row && other.dataset.group === select.value);
        last?.after(row);
        updateGroupHeadings(orderList);
        renderOrder(row, 'group');
      });
      item.append(select);
    }
    item.append(up, down, handle);
    function move(neighbor, before, nextDirection) {
      if (!neighbor) return;
      if (before) neighbor.before(row);
      else neighbor.after(row);
      updateGroupHeadings(orderList);
      renderOrder(row, nextDirection);
    }
    return item;
  });
  $orderRows.replaceChildren(...items);
  if (focusRow) {
    const item = items[rows.indexOf(focusRow)];
    const [up, down] = item.querySelectorAll('button');
    const control = direction === 'group' ? item.querySelector('select') : direction === 'up' && !up.disabled ? up : !down.disabled ? down : up;
    control.focus();
  }
}


// ── Save Recipe ────────────────────────────────────────────────
async function saveRecipe(e) {
  e.preventDefault();

  const name = $recipeName.value.trim();
  if (!name) {
    toast(window.t('feedback.12'));
    return;
  }

  const icon = $recipeIcon.value.trim();
  const glyphs = [...new Intl.Segmenter().segment(icon)];
  if (icon && (glyphs.length !== 1 || !/(?:\p{Extended_Pictographic}|\p{Regional_Indicator}|\u20e3)/u.test(icon))) {
    toast(window.t('recipe.icon-invalid'));
    $recipeIcon.focus();
    return;
  }
  if ($newTagInput.value.trim()) addNewTag();

  const recipeData = {
    icon: icon || null,
    name: name,
    notes: $recipeNotes.value.trim() || null,
    servings: Number($recipeServings.value),
    kcal_per_serving: parseFloat($recipeKcal.value) || null,
    active_cooking_time_min: parseInt($recipeActiveTime.value) || null,
    total_time_min: parseInt($recipeTotalTime.value) || null,
    tags: Array.from(selectedTags),
    ingredients: [],
    instruction_steps: []
  };

  // Extract ingredients
  document.querySelectorAll('.ingredient-row').forEach(row => {
    const n = row.querySelector('.ing-name').value.trim();
    if (!n) return;
    const q = parseFloat(row.querySelector('.ing-qty').value);
    const u = row.querySelector('.ing-unit').value.trim();
    recipeData.ingredients.push({
      name: n,
      group_name: row.dataset.group || null,
      quantity: isNaN(q) ? null : q,
      unit: u || null
    });
  });

  // Extract steps
  let stepNum = 1;
  document.querySelectorAll('.step-row').forEach(row => {
    const d = row.querySelector('.step-desc').value.trim();
    if (!d) return;
    const dur = parseInt(row.querySelector('.step-dur').value);
    recipeData.instruction_steps.push({
      step_number: stepNum++,
      description: d,
      group_name: row.dataset.group || null,
      duration_min: isNaN(dur) ? null : dur
    });
  });

  try {
    const method = editRecipeId ? 'PUT' : 'POST';
    const url = editRecipeId ? `${API}/recipes/${editRecipeId}` : `${API}/recipes`;

    const res = await fetch(url, {
      method: method,
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(recipeData)
    });

    if (!res.ok) throw new Error(window.t('feedback.13'));

    toast(editRecipeId ? window.t('feedback.14') : window.t('feedback.15'));
    closeEditModal();


    await loadTags();
    await loadRecipes();
  } catch (e) {
    console.error(e);
    toast(window.t('feedback.16'));
  }
}


// ── Delete ─────────────────────────────────────────────────────
let recipeToDelete = null;

window.promptDelete = function (id) {
  recipeToDelete = id;
  document.getElementById('delete-recipe-name').textContent = allRecipes.find(recipe => recipe.id === id)?.name || '';
  $deleteModal.style.display = 'flex';
};

async function performDelete() {
  if (!recipeToDelete) return;

  try {
    const res = await fetch(`${API}/recipes/${recipeToDelete}`, { method: 'DELETE', headers: getAuthHeaders() });
    if (!res.ok) throw new Error(window.t('feedback.17'));

    toast(window.t('feedback.18'));


    await loadTags();
    await loadRecipes();
  } catch (e) {
    console.error(e);
    toast(window.t('feedback.19'));
  } finally {
    $deleteModal.style.display = 'none';
    recipeToDelete = null;
  }
}




// ── Helpers ────────────────────────────────────────────────────
function esc(str) {
  if (!str) return '';
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

let toastTimer;
function toast(msg) {
  $toast.textContent = msg;
  $toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $toast.classList.remove('show'), 3000);
}

// ── Boot ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
