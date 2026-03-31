/* ============================================================
   app.js — What Should We Eat? — Frontend Logic
   ============================================================ */

const API = '';  // same origin

// ── Auth Helper ────────────────────────────────────────────────
function getAuthHeaders(extra = {}) {
  const token = window.WSWEAuth ? window.WSWEAuth.token : null;
  const h = { ...extra };
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}

function isLoggedIn() {
  return !!(window.WSWEAuth && window.WSWEAuth.token);
}

// ── State ──────────────────────────────────────────────────────
let selectedRecipes = [];   // current meal plan (from API)
let activeTags = new Set();
let allTags = [];
let currentFilters = {};    // remember filters used for reroll

// ── DOM refs ───────────────────────────────────────────────────
const $tagSelector = document.getElementById('tag-selector');
const $recipeCount = document.getElementById('recipe-count');
const $maxKcal = document.getElementById('max-kcal');
const $maxTime = document.getElementById('max-time');
const $btnRoll = document.getElementById('btn-roll');
const $btnRerollAll = document.getElementById('btn-reroll-all');
const $recipesGrid = document.getElementById('recipes-grid');
const $recipesSection = document.getElementById('recipes-section');
const $recipeBadge = document.getElementById('recipe-badge');
const $shoppingSection = document.getElementById('shopping-section');
const $shoppingList = document.getElementById('shopping-list');
const $shopBadge = document.getElementById('shop-badge');
const $toast = document.getElementById('toast');
const $btnKitchen = document.getElementById('btn-kitchen');


// ── Init ───────────────────────────────────────────────────────
async function init() {
  // Wait until auth is ready, then load if logged in
  window.addEventListener('wswe_auth_changed', async () => {
    if (isLoggedIn()) {
      await loadTags();
      await loadMealPlan();
    } else {
      selectedRecipes = [];
      allTags = [];
      renderRecipes();
      $recipesSection.style.display = 'none';
      $shoppingSection.style.display = 'none';
      $btnRerollAll.style.display = 'none';
      $btnKitchen.style.display = 'none';
      $tagSelector.innerHTML = '';
    }
  });

  // Initial load if already logged in (token restored from storage)
  if (isLoggedIn()) {
    await loadTags();
    await loadMealPlan();
  }

  $btnRoll.addEventListener('click', rollRecipes);
  $btnRerollAll.addEventListener('click', clearAll);
  $btnKitchen.addEventListener('click', () => { window.location.href = '/kitchen.html'; });
}

// ── Tags ───────────────────────────────────────────────────────
async function loadTags() {
  try {
    const res = await fetch(`${API}/tags`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    allTags = await res.json();
    renderTags();
  } catch (e) {
    console.error('Failed to load tags', e);
  }
}

function renderTags() {
  $tagSelector.innerHTML = allTags.map(t => `
    <button class="tag-pill ${activeTags.has(t.name) ? 'active' : ''}"
            data-tag="${t.name}">
      ${t.name}
    </button>
  `).join('');

  $tagSelector.querySelectorAll('.tag-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      const tag = btn.dataset.tag;
      if (activeTags.has(tag)) activeTags.delete(tag);
      else activeTags.add(tag);
      btn.classList.toggle('active');
    });
  });
}

// ── Build filter params ────────────────────────────────────────
function getFilters() {
  const filters = {
    count: parseInt($recipeCount.value) || 5,
    tag_names: [...activeTags],
  };
  const kcal = parseInt($maxKcal.value);
  const time = parseInt($maxTime.value);
  if (!isNaN(kcal) && kcal > 0) filters.max_kcal = kcal;
  if (!isNaN(time) && time > 0) filters.max_total_time = time;
  return filters;
}

// ── Load Meal Plan from API ────────────────────────────────────
async function loadMealPlan() {
  if (!isLoggedIn()) return;
  try {
    const res = await fetch(`${API}/meal-plan`, { headers: getAuthHeaders() });
    if (!res.ok) return;
    const data = await res.json();
    selectedRecipes = data.items.map(item => ({
      ...item.recipe,
      _cooked: item.is_cooked,
    }));
    if (selectedRecipes.length > 0) {
      renderRecipes();
      loadShoppingList();
      $recipesSection.style.display = '';
      $shoppingSection.style.display = '';
      $btnRerollAll.style.display = '';
      $btnKitchen.style.display = '';
    } else {
      $recipesSection.style.display = 'none';
      $shoppingSection.style.display = 'none';
      $btnRerollAll.style.display = 'none';
      $btnKitchen.style.display = 'none';
    }
  } catch (e) {
    console.error('Failed to load meal plan', e);
  }
}

// ── Roll Recipes ───────────────────────────────────────────────
async function rollRecipes() {
  if (!isLoggedIn()) {
    toast('Please log in to roll recipes.');
    return;
  }

  const filters = getFilters();
  currentFilters = filters;
  $btnRoll.innerHTML = '<span class="spinner"></span> Rolling…';
  $btnRoll.disabled = true;

  try {
    const excludeIds = selectedRecipes.map(r => r.id);
    const body = { ...filters, exclude_ids: excludeIds };

    const res = await fetch(`${API}/recipes/random`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(body),
    });
    const recipes = await res.json();

    if (recipes.length === 0) {
      toast('No more recipes match your filters — try broadening them.');
      return;
    }

    // Add to meal plan via API
    const newIds = recipes.map(r => r.id);
    await fetch(`${API}/meal-plan/add`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ recipe_ids: newIds }),
    });

    // Reload from API for consistency
    await loadMealPlan();

    toast(`🎲 Added ${recipes.length} recipe${recipes.length > 1 ? 's' : ''}!`);
  } catch (e) {
    toast('Something went wrong — is the API running?');
    console.error(e);
  } finally {
    $btnRoll.innerHTML = '🎲 Roll Recipes';
    $btnRoll.disabled = false;
  }
}

// ── Clear All ──────────────────────────────────────────────────
async function clearAll() {
  try {
    await fetch(`${API}/meal-plan`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
  } catch (e) {
    console.error('Failed to clear meal plan', e);
  }
  selectedRecipes = [];
  renderRecipes();
  loadShoppingList();
  $recipesSection.style.display = 'none';
  $shoppingSection.style.display = 'none';
  $btnRerollAll.style.display = 'none';
  $btnKitchen.style.display = 'none';
}

// ── Re-roll Single ─────────────────────────────────────────────
async function rerollSingle(recipeId) {
  const excludeIds = selectedRecipes.map(r => r.id);
  const targetRecipe = selectedRecipes.find(r => r.id === recipeId);
  if (!targetRecipe) return;

  try {
    const body = {
      ...currentFilters,
      count: 1,
      exclude_ids: excludeIds,
    };

    const res = await fetch(`${API}/recipes/random`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(body),
    });
    const replacements = await res.json();

    if (replacements.length === 0) {
      toast('No other recipes available to swap in.');
      return;
    }

    // Remove old from plan, add new
    await fetch(`${API}/meal-plan/${recipeId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    await fetch(`${API}/meal-plan/add`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ recipe_ids: [replacements[0].id] }),
    });

    await loadMealPlan();
    toast(`🔄 Swapped in "${replacements[0].name}"`);
  } catch (e) {
    toast('Failed to re-roll — check the API.');
    console.error(e);
  }
}

// ── Remove Single ──────────────────────────────────────────────
async function removeSingle(recipeId) {
  try {
    await fetch(`${API}/meal-plan/${recipeId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
  } catch (e) {
    console.error('Failed to remove recipe from plan', e);
  }
  await loadMealPlan();
}

// ── Render Recipes ─────────────────────────────────────────────
function renderRecipes() {
  $recipeBadge.textContent = selectedRecipes.length;

  $recipesGrid.innerHTML = selectedRecipes.map((r, i) => `
    <div class="recipe-card" style="animation-delay: ${i * 0.06}s" id="card-${r.id}">
      <div class="recipe-card-header">
        <h3>${esc(r.name)}</h3>
        <div style="display:flex; gap:6px;">
          <button class="btn btn-icon" title="Re-roll this recipe" data-reroll="${r.id}">🔄</button>
          <button class="btn btn-icon" title="Remove from plan" data-remove="${r.id}">✕</button>
        </div>
      </div>
      <div class="recipe-card-meta">
        ${r.kcal_per_serving ? `<span class="meta-chip"><span class="icon">🔥</span> ${r.kcal_per_serving} kcal</span>` : ''}
        ${r.active_cooking_time_min ? `<span class="meta-chip"><span class="icon">🧄</span> ${r.active_cooking_time_min} min active</span>` : ''}
        ${r.total_time_min ? `<span class="meta-chip"><span class="icon">⏱️</span> ${r.total_time_min} min total</span>` : ''}
      </div>
      <div class="recipe-card-tags">
        ${r.tags.map(t => `<span class="recipe-tag">${esc(t.name)}</span>`).join('')}
      </div>
      ${r.instruction_steps && r.instruction_steps.length ? `
        <div class="recipe-card-footer">
          <button class="recipe-steps-toggle" data-toggle="steps-${r.id}">
            Show steps ▾
          </button>
          <span style="font-size:0.78rem;color:var(--text-light);">${r.instruction_steps.length} step${r.instruction_steps.length > 1 ? 's' : ''}</span>
        </div>
        <div class="recipe-steps" id="steps-${r.id}">
          <div class="recipe-steps-inner">
            ${r.instruction_steps
        .sort((a, b) => a.step_number - b.step_number)
        .map(s => `
                <div class="step-item">
                  <span class="step-num">${s.step_number}</span>
                  <span>${esc(s.description)}</span>
                  ${s.duration_min ? `<span class="step-dur">${s.duration_min} min</span>` : ''}
                </div>
              `).join('')}
          </div>
        </div>
      ` : ''}
    </div>
  `).join('');

  // Wire up action buttons
  $recipesGrid.querySelectorAll('[data-reroll]').forEach(btn => {
    btn.addEventListener('click', () => rerollSingle(parseInt(btn.dataset.reroll)));
  });
  $recipesGrid.querySelectorAll('[data-remove]').forEach(btn => {
    btn.addEventListener('click', () => removeSingle(parseInt(btn.dataset.remove)));
  });

  // Wire up step toggles
  $recipesGrid.querySelectorAll('.recipe-steps-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = document.getElementById(btn.dataset.toggle);
      const isOpen = target.classList.toggle('open');
      btn.textContent = isOpen ? 'Hide steps ▴' : 'Show steps ▾';
    });
  });
}

// ── Shopping List ──────────────────────────────────────────────
async function loadShoppingList() {
  const ids = selectedRecipes.map(r => r.id);
  if (!ids.length) return;

  try {
    const res = await fetch(`${API}/shopping-list`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(ids),
    });
    if (!res.ok) return;
    const data = await res.json();
    renderShoppingList(data.items);
  } catch (e) {
    console.error('Failed to load shopping list', e);
  }
}

function renderShoppingList(items) {
  $shopBadge.textContent = items.length;

  $shoppingList.innerHTML = items.map((item, i) => {
    const qty = item.total_quantity != null
      ? `${fmtQty(item.total_quantity)} ${item.unit || ''}`
      : '';
    return `
      <li class="shopping-item" data-idx="${i}">
        <span class="checkbox" data-check="${i}">✓</span>
        <span class="item-qty">${qty}</span>
        <span class="item-name">${esc(item.name)}</span>
      </li>
    `;
  }).join('');

  // Checkboxes
  $shoppingList.querySelectorAll('.checkbox').forEach(cb => {
    cb.addEventListener('click', () => {
      cb.classList.toggle('checked');
      cb.closest('.shopping-item').classList.toggle('checked-item');
    });
  });
}

// ── Helpers ────────────────────────────────────────────────────
function esc(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function fmtQty(n) {
  return Number.isInteger(n) ? n.toString() : n.toFixed(1);
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
