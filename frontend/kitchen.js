/* ============================================================
   kitchen.js — What Should We Eat? — Kitchen Logic
   ============================================================ */

const API = '';

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
let kitchenRecipes = [];  // [{...recipe, _cooked: bool}]

// ── DOM refs ───────────────────────────────────────────────────
const $emptyState = document.getElementById('empty-state');
const $kitchenSection = document.getElementById('kitchen-section');
const $kitchenGrid = document.getElementById('kitchen-grid');

const $modal = document.getElementById('meal-modal');
const $btnCloseModal = document.getElementById('btn-close-modal');
const $modalTitle = document.getElementById('modal-title');
const $modalMeta = document.getElementById('modal-meta');
const $modalIngredients = document.getElementById('modal-ingredients');
const $modalInstructions = document.getElementById('modal-instructions');
const $btnToggleCooked = document.getElementById('btn-toggle-cooked');

let activeRecipeId = null;

// ── Init ───────────────────────────────────────────────────────
function init() {
  window.addEventListener('wswe_auth_changed', () => {
    if (isLoggedIn()) {
      loadMealPlan();
    } else {
      kitchenRecipes = [];
      updateGridVisibility();
    }
  });

  if (isLoggedIn()) {
    loadMealPlan();
  } else {
    updateGridVisibility();
  }

  if ($btnCloseModal) $btnCloseModal.addEventListener('click', closeModal);
  if ($btnToggleCooked) $btnToggleCooked.addEventListener('click', handleToggleCooked);

  window.addEventListener('i18n:loaded', () => {
    if (kitchenRecipes.length > 0) renderGrid();
    if (activeRecipeId) openModal(activeRecipeId);
  });
}

// ── Load from API ──────────────────────────────────────────────
async function loadMealPlan() {
  try {
    const res = await fetch(`${API}/meal-plan`, { headers: getAuthHeaders() });
    if (!res.ok) {
      kitchenRecipes = [];
      updateGridVisibility();
      return;
    }
    const data = await res.json();
    kitchenRecipes = data.items.map(item => ({
      ...item.recipe,
      _cooked: item.is_cooked,
    }));
    updateGridVisibility();
  } catch (e) {
    console.error('Failed to load meal plan', e);
    kitchenRecipes = [];
    updateGridVisibility();
  }
}

function updateGridVisibility() {
  if (kitchenRecipes.length === 0) {
    $emptyState.style.display = '';
    $kitchenSection.style.display = 'none';
  } else {
    $emptyState.style.display = 'none';
    $kitchenSection.style.display = '';
    renderGrid();
  }
}

// ── Render ─────────────────────────────────────────────────────
function renderGrid() {
  // Sort: Uncooked first, Cooked last.
  const sorted = [...kitchenRecipes].sort((a, b) => {
    const aCooked = !!a._cooked;
    const bCooked = !!b._cooked;
    if (aCooked === bCooked) return 0;
    return aCooked ? 1 : -1;
  });

  $kitchenGrid.innerHTML = sorted.map((r, i) => `
    <div class="recipe-card ${r._cooked ? 'cooked-card' : ''}" style="animation-delay: ${i * 0.05}s; cursor: pointer;" data-id="${r.id}">
      <div class="recipe-card-header" style="pointer-events:none;">
        <h3>${esc(r.name)}</h3>
      </div>
      <div class="recipe-card-meta" style="pointer-events:none;">
        ${r.kcal_per_serving ? `<span class="meta-chip"><span class="icon">🔥</span> ${r.kcal_per_serving} kcal</span>` : ''}
        ${r.active_cooking_time_min ? `<span class="meta-chip"><span class="icon">🧄</span> ${r.active_cooking_time_min} min</span>` : ''}
        ${r.total_time_min ? `<span class="meta-chip"><span class="icon">⏱️</span> ${r.total_time_min} min</span>` : ''}
      </div>
      <div class="recipe-card-tags" style="pointer-events:none;">
        ${r.tags.map(t => `<span class="recipe-tag">${esc(t.name)}</span>`).join('')}
      </div>
      ${r._cooked ? `<div style="margin-top:12px; font-weight:bold; color:var(--text-light); text-align:center;">${window.t('kitchen.cooked', '✓ Cooked')}</div>` : ''}
    </div>
  `).join('');

  // Wire up clicks
  $kitchenGrid.querySelectorAll('.recipe-card').forEach(card => {
    card.addEventListener('click', () => {
      openModal(parseInt(card.dataset.id));
    });
  });
}

// ── Modal Logic ────────────────────────────────────────────────
function openModal(id) {
  const recipe = kitchenRecipes.find(r => r.id === id);
  if (!recipe) return;

  activeRecipeId = id;

  $modalTitle.textContent = recipe.name;

  // Meta
  const metaHTML = [];
  if (recipe.kcal_per_serving) metaHTML.push(`<span class="meta-chip"><span class="icon">🔥</span> ${recipe.kcal_per_serving} kcal</span>`);
  if (recipe.active_cooking_time_min) metaHTML.push(`<span class="meta-chip"><span class="icon">🧄</span> ${recipe.active_cooking_time_min} min active</span>`);
  if (recipe.total_time_min) metaHTML.push(`<span class="meta-chip"><span class="icon">⏱️</span> ${recipe.total_time_min} min total</span>`);
  $modalMeta.innerHTML = metaHTML.join('');

  // Ingredients
  $modalIngredients.innerHTML = (recipe.ingredients || []).map(ing => {
    const qty = ing.quantity != null ? `${fmtQty(ing.quantity)} ${ing.unit || ''}` : '';
    return `
      <li style="margin-bottom:8px;">
        <label style="display:flex; align-items:flex-start; gap:12px; cursor:pointer;">
          <input type="checkbox" style="width:24px; height:24px; margin-top:2px; accent-color:var(--orange); cursor:pointer;" />
          <span style="font-size:1.2rem; line-height:1.4; color:var(--text-dark);">
            ${qty ? `<strong>${qty}</strong>` : ''} ${esc(ing.name)}
          </span>
        </label>
      </li>
    `;
  }).join('');

  // Instructions
  $modalInstructions.innerHTML = (recipe.instruction_steps || [])
    .sort((a, b) => a.step_number - b.step_number)
    .map(s => `
      <div style="display:flex; gap:16px; background:var(--bg-card); padding:20px; border-radius:12px; border:1px solid var(--border);">
        <div style="flex-shrink:0; background:var(--orange); color:white; width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:1.2rem;">
          ${s.step_number}
        </div>
        <div style="flex:1;">
          <p style="margin:0; font-size:1.2rem; line-height:1.6; color:var(--text-dark);">${esc(s.description)}</p>
          ${s.duration_min ? `<div style="margin-top:12px; font-weight:bold; color:var(--orange-dark); background:var(--orange-pale); display:inline-block; padding:4px 12px; border-radius:20px; font-size:0.9rem;">⏱️ ${s.duration_min} min</div>` : ''}
        </div>
      </div>
    `).join('');

  // Button State
  updateCookedButtonState(recipe._cooked);

  $modal.style.display = 'flex';
  document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

function updateCookedButtonState(isCooked) {
  if (isCooked) {
    $btnToggleCooked.innerHTML = window.t('kitchen.undo_cooked', '↺ Undo "Cooked" Status');
    $btnToggleCooked.className = 'btn btn-secondary';
    $btnToggleCooked.style.padding = '16px 32px';
    $btnToggleCooked.style.fontSize = '1.2rem';
    $btnToggleCooked.style.width = '100%';
    $btnToggleCooked.style.maxWidth = '400px';
  } else {
    $btnToggleCooked.innerHTML = window.t('kitchen.mark_cooked', '✅ Mark as Cooked');
    $btnToggleCooked.className = 'btn btn-primary';
    $btnToggleCooked.style.padding = '16px 32px';
    $btnToggleCooked.style.fontSize = '1.2rem';
    $btnToggleCooked.style.width = '100%';
    $btnToggleCooked.style.maxWidth = '400px';
  }
}

async function handleToggleCooked() {
  if (!activeRecipeId) return;
  const recipe = kitchenRecipes.find(r => r.id === activeRecipeId);
  if (!recipe) return;

  const newState = !recipe._cooked;

  try {
    if (newState) {
      await fetch(`${API}/meal-plan/${activeRecipeId}/cooked`, {
        method: 'POST',
        headers: getAuthHeaders(),
      });
    } else {
      await fetch(`${API}/meal-plan/${activeRecipeId}/cooked`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
    }
    recipe._cooked = newState;
    renderGrid();

    if (newState) {
      closeModal();
    } else {
      updateCookedButtonState(newState);
    }
  } catch (e) {
    console.error('Failed to toggle cooked status', e);
  }
}

function closeModal() {
  $modal.style.display = 'none';
  document.body.style.overflow = '';
  activeRecipeId = null;
}

// ── Helpers ────────────────────────────────────────────────────
function esc(str) {
  if (!str) return '';
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function fmtQty(n) {
  return Number.isInteger(n) ? n.toString() : n.toFixed(1);
}

// ── Boot ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
