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
let selectedTags = new Set();

// Dynamic Lists
const $ingredientsList = document.getElementById('ingredients-list');
const $stepsList = document.getElementById('steps-list');

// Toast
const $toast = document.getElementById('toast');


// ── Init ───────────────────────────────────────────────────────
async function init() {
  // Attach all event listeners synchronously so UI is responsive
  // Search
  $recipeSearch.addEventListener('input', handleSearch);

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
  document.getElementById('btn-add-tag').addEventListener('click', addNewTag);
  $newTagInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addNewTag();
    }
  });

  // Dynamic lists handlers
  document.getElementById('btn-add-ingredient').addEventListener('click', () => addIngredientRow());
  document.getElementById('btn-add-step').addEventListener('click', () => addStepRow());

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
    allTags = await res.json();
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
function handleSearch(e) {
  const query = e.target.value.toLowerCase().trim();
  if (!query) {
    renderRecipes(allRecipes);
    return;
  }

  const filtered = allRecipes.filter(r => {
    const matchName = (r.name || '').toLowerCase().includes(query);
    const matchTags = r.tags.some(t => t.name.toLowerCase().includes(query));
    // Provide fallback array for ingredients just in case
    const matchIngs = (r.ingredients || []).some(ing => (ing.name || '').toLowerCase().includes(query));
    return matchName || matchTags || matchIngs;
  });
  renderRecipes(filtered);
}

function renderRecipes(recipesToRender = allRecipes) {
  $listBadge.textContent = recipesToRender.length;

  if (recipesToRender.length === 0) {
    $manageGrid.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <div class="icon">🧅</div>
        <p>${window.t("ui.0")}</p>
      </div>
    `;
    return;
  }

  $manageGrid.innerHTML = recipesToRender.map((r, i) => `
    <div class="recipe-card" style="animation-delay: ${i * 0.03}s">
      <div class="recipe-card-header">
        <h3>${esc(r.name)}</h3>
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
        <button class="btn btn-secondary btn-sm" onclick="promptDelete(${r.id}, '${escJs(r.name)}')">${window.t("ui.2")}</button>
      </div>
    </div>
  `).join('');
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
  renderEditTags();

  $ingredientsList.innerHTML = '';
  r.ingredients.forEach(ing => addIngredientRow(ing.name, ing.quantity, ing.unit));
  if (r.ingredients.length === 0) addIngredientRow();

  $stepsList.innerHTML = '';
  const sortedSteps = [...(r.instruction_steps || [])].sort((a, b) => a.step_number - b.step_number);
  sortedSteps.forEach(st => addStepRow(st.description, st.duration_min));
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
    addIngredientRow(ing.name, ing.quantity ?? '', ing.unit || '');
  });
  if ((recipe.ingredients || []).length === 0) addIngredientRow();

  $stepsList.innerHTML = '';
  (recipe.instruction_steps || []).forEach(step => {
    addStepRow(step.description, step.duration_min ?? '');
  });
  if ((recipe.instruction_steps || []).length === 0) addStepRow();
}


// ── Tags in Edit Form ──────────────────────────────────────────
function renderEditTags() {
  // Combine all system tags with any custom tags currently selected
  const allKnownTags = new Set([...allTags.map(t => t.name), ...selectedTags]);

  $editTagSelector.innerHTML = Array.from(allKnownTags).map(tName => `
    <button type="button" class="tag-pill ${selectedTags.has(tName) ? 'active' : ''}"
            onclick="toggleTag('${escJs(tName)}')">
      ${esc(tName)}
    </button>
  `).join('');
}

window.toggleTag = function (name) {
  if (selectedTags.has(name)) selectedTags.delete(name);
  else selectedTags.add(name);
  renderEditTags();
};

function addNewTag() {
  const val = $newTagInput.value.trim();
  if (!val) return;
  selectedTags.add(val);
  $newTagInput.value = '';
  renderEditTags();
}


// ── Dynamic Rows ───────────────────────────────────────────────
function addIngredientRow(name = '', qty = '', unit = '') {
  const div = document.createElement('div');
  div.className = 'editor-row ingredient-row';
  div.innerHTML = `
    <input type="text" placeholder="${window.t('feedback.31')}" class="ing-name" value="${esc(name)}" style="flex:2;" />
    <input type="number" placeholder="${window.t('feedback.32')}" class="ing-qty" step="any" value="${qty}" style="flex:1;" />
    <input type="text" placeholder="${window.t('feedback.33')}" class="ing-unit" value="${esc(unit)}" style="flex:1;" />
    <button type="button" class="btn-icon" onclick="this.parentElement.remove()">✕</button>
  `;
  $ingredientsList.appendChild(div);
}

function addStepRow(desc = '', dur = '') {
  const div = document.createElement('div');
  div.className = 'editor-row step-row';
  div.innerHTML = `
    <input type="text" placeholder="${window.t('feedback.34')}" class="step-desc" value="${esc(desc)}" style="flex:3;" />
    <input type="number" placeholder="${window.t('feedback.35')}" class="step-dur" value="${dur}" style="max-width:100px;" />
    <button type="button" class="btn-icon" onclick="this.parentElement.remove()">✕</button>
  `;
  $stepsList.appendChild(div);
}


// ── Save Recipe ────────────────────────────────────────────────
async function saveRecipe(e) {
  e.preventDefault();

  const name = $recipeName.value.trim();
  if (!name) {
    toast(window.t('feedback.12'));
    return;
  }

  const recipeData = {
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

window.promptDelete = function (id, name) {
  recipeToDelete = id;
  document.getElementById('delete-recipe-name').textContent = name;
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
  return d.innerHTML;
}

function escJs(str) {
  if (!str) return '';
  return str.replace(/'/g, "\\'");
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
