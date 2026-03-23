/* ============================================================
   manage.js — What Should We Eat? — Recipe Management
   ============================================================ */

const API = '';  // same origin

// ── State ──────────────────────────────────────────────────────
let allRecipes = [];
let allTags = [];
let editRecipeId = null;

// Form DOM refs
const $modalOverlay = document.getElementById('edit-modal');
const $deleteModal = document.getElementById('delete-modal');
const $manageGrid = document.getElementById('manage-grid');
const $listBadge = document.getElementById('list-badge');
const $recipeSearch = document.getElementById('recipe-search');

const $recipeForm = document.getElementById('recipe-form');
const $modalTitle = document.getElementById('modal-title');
const $recipeName = document.getElementById('recipe-name');
const $recipeKcal = document.getElementById('recipe-kcal');
const $recipeActiveTime = document.getElementById('recipe-active-time');
const $recipeTotalTime = document.getElementById('recipe-total-time');

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
  await loadTags();
  await loadRecipes();

  // Search
  $recipeSearch.addEventListener('input', handleSearch);

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

  // Delete modal
  document.getElementById('btn-cancel-delete').addEventListener('click', () => {
    $deleteModal.style.display = 'none';
  });
  document.getElementById('btn-confirm-delete').addEventListener('click', performDelete);
}

// ── Data Fetching ──────────────────────────────────────────────
async function loadTags() {
  try {
    const res = await fetch(`${API}/tags`);
    allTags = await res.json();
  } catch (e) {
    console.error('Failed to load tags', e);
  }
}

async function loadRecipes() {
  try {
    const res = await fetch(`${API}/recipes`);
    allRecipes = await res.json();
    renderRecipes();
  } catch (e) {
    console.error('Failed to load recipes', e);
    toast('Failed to load recipes.');
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
        <div class="icon">🍳</div>
        <p>No recipes found.</p>
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
        ${r.kcal_per_serving ? `<span class="meta-chip"><span class="icon">🔥</span> ${r.kcal_per_serving} kcal</span>` : ''}
        ${r.active_cooking_time_min ? `<span class="meta-chip"><span class="icon">👨‍🍳</span> ${r.active_cooking_time_min} min active</span>` : ''}
        ${r.total_time_min ? `<span class="meta-chip"><span class="icon">⏱️</span> ${r.total_time_min} min total</span>` : ''}
      </div>
      <div class="recipe-card-tags">
        ${r.tags.map(t => `<span class="recipe-tag">${esc(t.name)}</span>`).join('')}
      </div>
      <div class="recipe-card-footer">
        <button class="btn btn-secondary btn-sm" onclick="editRecipe(${r.id})">✏️ Edit</button>
        <button class="btn btn-secondary btn-sm" onclick="promptDelete(${r.id}, '${escJs(r.name)}')" style="color:#d9534f; border-color:#d9534f55;">🗑️ Delete</button>
      </div>
    </div>
  `).join('');
}


// ── Modals & Forms ─────────────────────────────────────────────
function openCreateModal() {
  editRecipeId = null;
  $modalTitle.textContent = "Create New Recipe";
  $recipeForm.reset();
  selectedTags.clear();
  renderEditTags();
  
  $ingredientsList.innerHTML = '';
  $stepsList.innerHTML = '';
  addIngredientRow();
  addStepRow();

  $modalOverlay.style.display = 'flex';
}

function closeEditModal(e) {
  if (e) e.preventDefault();
  $modalOverlay.style.display = 'none';
}

function editRecipe(id) {
  const r = allRecipes.find(x => x.id === id);
  if (!r) return;

  editRecipeId = id;
  $modalTitle.textContent = "Edit Recipe";
  
  $recipeName.value = r.name || '';
  $recipeKcal.value = r.kcal_per_serving || '';
  $recipeActiveTime.value = r.active_cooking_time_min || '';
  $recipeTotalTime.value = r.total_time_min || '';

  selectedTags = new Set(r.tags.map(t => t.name));
  renderEditTags();

  $ingredientsList.innerHTML = '';
  r.ingredients.forEach(ing => addIngredientRow(ing.name, ing.quantity, ing.unit));
  if (r.ingredients.length === 0) addIngredientRow();

  $stepsList.innerHTML = '';
  const sortedSteps = [...(r.instruction_steps || [])].sort((a,b) => a.step_number - b.step_number);
  sortedSteps.forEach(st => addStepRow(st.description, st.duration_min));
  if (sortedSteps.length === 0) addStepRow();

  $modalOverlay.style.display = 'flex';
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

window.toggleTag = function(name) {
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
    <input type="text" placeholder="Name (e.g. Tomato)" class="ing-name" value="${esc(name)}" style="flex:2;" />
    <input type="number" placeholder="Qty" class="ing-qty" step="any" value="${qty}" style="flex:1;" />
    <input type="text" placeholder="Unit (g, tbsp...)" class="ing-unit" value="${esc(unit)}" style="flex:1;" />
    <button type="button" class="btn-icon" onclick="this.parentElement.remove()">✕</button>
  `;
  $ingredientsList.appendChild(div);
}

function addStepRow(desc = '', dur = '') {
  const div = document.createElement('div');
  div.className = 'editor-row step-row';
  div.innerHTML = `
    <input type="text" placeholder="Description..." class="step-desc" value="${esc(desc)}" style="flex:3;" />
    <input type="number" placeholder="Time (min)" class="step-dur" value="${dur}" style="max-width:100px;" />
    <button type="button" class="btn-icon" onclick="this.parentElement.remove()">✕</button>
  `;
  $stepsList.appendChild(div);
}


// ── Save Recipe ────────────────────────────────────────────────
async function saveRecipe(e) {
  e.preventDefault();
  
  const name = $recipeName.value.trim();
  if (!name) {
    toast('Recipe name is required.');
    return;
  }

  const recipeData = {
    name: name,
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
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(recipeData)
    });

    if (!res.ok) throw new Error('Failed to save');

    toast(editRecipeId ? 'Recipe updated!' : 'Recipe created!');
    closeEditModal();
    
    // Purge local layout cache so landing page reflects changes safely
    syncLocalLandingState(editRecipeId, true);
    
    await loadTags();
    await loadRecipes();
  } catch(e) {
    console.error(e);
    toast('Error saving recipe.');
  }
}


// ── Delete ─────────────────────────────────────────────────────
let recipeToDelete = null;

window.promptDelete = function(id, name) {
  recipeToDelete = id;
  document.getElementById('delete-recipe-name').textContent = name;
  $deleteModal.style.display = 'flex';
};

async function performDelete() {
  if (!recipeToDelete) return;
  
  try {
    const res = await fetch(`${API}/recipes/${recipeToDelete}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Delete failed');
    
    toast('Recipe deleted.');
    syncLocalLandingState(recipeToDelete, false); // remove from landing selection
    
    await loadTags();
    await loadRecipes();
  } catch(e) {
    console.error(e);
    toast('Error deleting recipe.');
  } finally {
    $deleteModal.style.display = 'none';
    recipeToDelete = null;
  }
}

// Ensure landing page local selection clears out removed/heavily modified recipes
function syncLocalLandingState(recipeId, isUpdate=false) {
  try {
    const saved = localStorage.getItem('wswe_recipes');
    if (!saved || !recipeId) return;
    
    let selected = JSON.parse(saved);
    if (!Array.isArray(selected)) return;
    
    // If a recipe is deleted, remove it from the frontend active selection
    if (!isUpdate) {
      selected = selected.filter(r => r.id !== recipeId);
      localStorage.setItem('wswe_recipes', JSON.stringify(selected));
    } else {
      // If it's an update, the easiest strategy so we don't hold stale data is to just remove it
      // so the user re-rolls, or we could fetch the newly updated format and replace it. 
      // Easiest robust method: remove so landing page fetches new.
      selected = selected.filter(r => r.id !== recipeId);
      localStorage.setItem('wswe_recipes', JSON.stringify(selected));
    }
  } catch(e) {}
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
