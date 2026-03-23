/* ============================================================
   app.js — What Should We Eat? — Frontend Logic
   ============================================================ */

const API = '';  // same origin

// ── State ──────────────────────────────────────────────────────
let selectedRecipes = [];   // current meal plan
let activeTags = new Set();
let allTags = [];
let currentFilters = {};    // remember filters used for reroll

// ── DOM refs ───────────────────────────────────────────────────
const $tagSelector   = document.getElementById('tag-selector');
const $recipeCount   = document.getElementById('recipe-count');
const $maxKcal       = document.getElementById('max-kcal');
const $maxTime       = document.getElementById('max-time');
const $btnRoll       = document.getElementById('btn-roll');
const $btnRerollAll  = document.getElementById('btn-reroll-all');
const $recipesGrid   = document.getElementById('recipes-grid');
const $recipesSection= document.getElementById('recipes-section');
const $recipeBadge   = document.getElementById('recipe-badge');
const $shoppingSection = document.getElementById('shopping-section');
const $shoppingList  = document.getElementById('shopping-list');
const $shopBadge     = document.getElementById('shop-badge');
const $toast         = document.getElementById('toast');
const $btnKitchen    = document.getElementById('btn-kitchen');


// ── Init ───────────────────────────────────────────────────────
async function init() {
  await loadTags();
  restoreState();

  $btnRoll.addEventListener('click', rollRecipes);
  $btnRerollAll.addEventListener('click', clearAll);
  $btnKitchen.addEventListener('click', () => { window.location.href = '/kitchen.html'; });

  // Cross-tab synchronization so deleted recipes disappear
  window.addEventListener('storage', (e) => {
    if (e.key === 'wswe_recipes') {
      try {
        const saved = localStorage.getItem('wswe_recipes');
        if (saved) {
          selectedRecipes = JSON.parse(saved);
          renderRecipes();
          loadShoppingList();
          if (selectedRecipes.length === 0) {
            $recipesSection.style.display = 'none';
            $shoppingSection.style.display = 'none';
            $btnRerollAll.style.display = 'none';
          }
        }
      } catch(err) {}
    }
  });
}

// ── Tags ───────────────────────────────────────────────────────
async function loadTags() {
  try {
    const res = await fetch(`${API}/tags`);
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

// ── Roll Recipes ───────────────────────────────────────────────
async function rollRecipes() {
  const filters = getFilters();
  currentFilters = filters; // mostly for UI restoration
  $btnRoll.innerHTML = '<span class="spinner"></span> Rolling…';
  $btnRoll.disabled = true;

  try {
    const excludeIds = selectedRecipes.map(r => r.id);
    const body = { ...filters, exclude_ids: excludeIds };

    const res = await fetch(`${API}/recipes/random`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const recipes = await res.json();

    if (recipes.length === 0) {
      toast('No more recipes match your filters — try broadening them.');
      return;
    }

    // Attach the filters used to each recipe for later single-rerolls
    recipes.forEach(r => {
      r._filters = JSON.parse(JSON.stringify(filters));
    });

    selectedRecipes = [...selectedRecipes, ...recipes];
    renderRecipes();
    await loadShoppingList();
    saveState();

    $recipesSection.style.display = '';
    $shoppingSection.style.display = '';
    $btnRerollAll.style.display = '';
    $btnKitchen.style.display = '';

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
function clearAll() {
  selectedRecipes = [];
  renderRecipes();
  loadShoppingList();
  saveState();
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

  const filtersToUse = targetRecipe._filters || currentFilters;

  try {
    const body = {
      ...filtersToUse,
      count: 1,
      exclude_ids: excludeIds,
    };

    const res = await fetch(`${API}/recipes/random`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const replacements = await res.json();

    if (replacements.length === 0) {
      toast('No other recipes available to swap in.');
      return;
    }

    const idx = selectedRecipes.findIndex(r => r.id === recipeId);
    if (idx !== -1) {
      replacements[0]._filters = filtersToUse; // Inherit the filters
      selectedRecipes[idx] = replacements[0];
      renderRecipes();
      await loadShoppingList();
      saveState();
      toast(`🔄 Swapped in "${replacements[0].name}"`);
    }
  } catch (e) {
    toast('Failed to re-roll — check the API.');
    console.error(e);
  }
}

// ── Remove Single ──────────────────────────────────────────────
function removeSingle(recipeId) {
  selectedRecipes = selectedRecipes.filter(r => r.id !== recipeId);
  renderRecipes();
  loadShoppingList();
  saveState();
  if (selectedRecipes.length === 0) {
    $recipesSection.style.display = 'none';
    $shoppingSection.style.display = 'none';
    $btnRerollAll.style.display = 'none';
    $btnKitchen.style.display = 'none';
  }
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
        ${r.active_cooking_time_min ? `<span class="meta-chip"><span class="icon">👨‍🍳</span> ${r.active_cooking_time_min} min active</span>` : ''}
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
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ids),
    });
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

// ── Persistence (localStorage) ─────────────────────────────────
function saveState() {
  localStorage.setItem('wswe_recipes', JSON.stringify(selectedRecipes));
  localStorage.setItem('wswe_filters', JSON.stringify(currentFilters));
}

function restoreState() {
  try {
    const saved = localStorage.getItem('wswe_recipes');
    const savedFilters = localStorage.getItem('wswe_filters');
    if (saved) {
      selectedRecipes = JSON.parse(saved);
      if (selectedRecipes.length) {
        renderRecipes();
        loadShoppingList();
        $recipesSection.style.display = '';
        $shoppingSection.style.display = '';
        $btnRerollAll.style.display = '';
        $btnKitchen.style.display = '';
      }
    }
    if (savedFilters) {
      currentFilters = JSON.parse(savedFilters);
      // Restore filter UI
      if (currentFilters.count) $recipeCount.value = currentFilters.count;
      if (currentFilters.max_kcal) $maxKcal.value = currentFilters.max_kcal;
      if (currentFilters.max_total_time) $maxTime.value = currentFilters.max_total_time;
      if (currentFilters.tag_names) {
        currentFilters.tag_names.forEach(t => activeTags.add(t));
      }
    }
  } catch { /* ignore corrupt state */ }
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
