/* ============================================================
   kitchen.js — What Should We Eat? — Kitchen Logic
   ============================================================ */

// ── State ──────────────────────────────────────────────────────
let kitchenRecipes = [];

// ── DOM refs ───────────────────────────────────────────────────
const $emptyState     = document.getElementById('empty-state');
const $kitchenSection = document.getElementById('kitchen-section');
const $kitchenGrid    = document.getElementById('kitchen-grid');

const $modal          = document.getElementById('meal-modal');
const $btnCloseModal  = document.getElementById('btn-close-modal');
const $modalTitle     = document.getElementById('modal-title');
const $modalMeta      = document.getElementById('modal-meta');
const $modalIngredients = document.getElementById('modal-ingredients');
const $modalInstructions = document.getElementById('modal-instructions');
const $btnToggleCooked = document.getElementById('btn-toggle-cooked');

let activeRecipeId = null;

// ── Auth State & DOM ───────────────────────────────────────────
let authToken = localStorage.getItem('wswe_token') || null;
let currentUser = null;

const $authControls = document.getElementById('auth-controls');
const $userControls = document.getElementById('user-controls');
const $userGreeting = document.getElementById('user-greeting');
const $btnShowLogin = document.getElementById('btn-show-login');
const $btnShowSignup = document.getElementById('btn-show-signup');
const $btnLogout = document.getElementById('btn-logout');

const $loginModal = document.getElementById('login-modal');
const $signupModal = document.getElementById('signup-modal');
const $btnCloseLogin = document.getElementById('btn-close-login');
const $btnCloseSignup = document.getElementById('btn-close-signup');

const $loginForm = document.getElementById('login-form');
const $signupForm = document.getElementById('signup-form');
const $loginError = document.getElementById('login-error');
const $signupError = document.getElementById('signup-error');

const $linkToSignup = document.getElementById('link-to-signup');
const $linkToLogin = document.getElementById('link-to-login');

// ── Init ───────────────────────────────────────────────────────
function init() {
  initAuth();
  restoreState();
  
  $btnCloseModal.addEventListener('click', closeModal);
  $btnToggleCooked.addEventListener('click', handleToggleCooked);

  // Cross-tab synchronization
  window.addEventListener('storage', (e) => {
    if (e.key === 'wswe_recipes') {
      restoreState();
      // If modal is open for a deleted recipe, close it
      if (activeRecipeId && !kitchenRecipes.find(r => r.id === activeRecipeId)) {
        closeModal();
      }
    }
  });
}

function restoreState() {
  if (authToken) {
    // If logged in, fetch recipes from the server
    fetchUserRecipes();
  } else {
    // If not logged in, load from local storage
    try {
      const saved = localStorage.getItem('wswe_recipes');
      if (saved) {
        kitchenRecipes = JSON.parse(saved);
      } else {
        kitchenRecipes = [];
      }
    } catch {
      kitchenRecipes = [];
    }
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

function saveState() {
  localStorage.setItem('wswe_recipes', JSON.stringify(kitchenRecipes));
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
        ${r.active_cooking_time_min ? `<span class="meta-chip"><span class="icon">👨‍🍳</span> ${r.active_cooking_time_min} min</span>` : ''}
        ${r.total_time_min ? `<span class="meta-chip"><span class="icon">⏱️</span> ${r.total_time_min} min</span>` : ''}
      </div>
      <div class="recipe-card-tags" style="pointer-events:none;">
        ${r.tags.map(t => `<span class="recipe-tag">${esc(t.name)}</span>`).join('')}
      </div>
      ${r._cooked ? `<div style="margin-top:12px; font-weight:bold; color:var(--text-light); text-align:center;">✓ Cooked</div>` : ''}
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
  if (recipe.active_cooking_time_min) metaHTML.push(`<span class="meta-chip"><span class="icon">👨‍🍳</span> ${recipe.active_cooking_time_min} min active</span>`);
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
    $btnToggleCooked.innerHTML = '↺ Undo "Cooked" Status';
    $btnToggleCooked.className = 'btn btn-secondary';
    $btnToggleCooked.style.padding = '16px 32px';
    $btnToggleCooked.style.fontSize = '1.2rem';
    $btnToggleCooked.style.width = '100%';
    $btnToggleCooked.style.maxWidth = '400px';
  } else {
    $btnToggleCooked.innerHTML = '✅ Mark as Cooked';
    $btnToggleCooked.className = 'btn btn-primary';
    $btnToggleCooked.style.padding = '16px 32px';
    $btnToggleCooked.style.fontSize = '1.2rem';
    $btnToggleCooked.style.width = '100%';
    $btnToggleCooked.style.maxWidth = '400px';
  }
}

function handleToggleCooked() {
  if (!activeRecipeId) return;
  const recipe = kitchenRecipes.find(r => r.id === activeRecipeId);
  if (!recipe) return;

  recipe._cooked = !recipe._cooked;
  saveState();
  renderGrid();
  
  // Close the modal automatically if marking as cooked. Stay open if undoing.
  if (recipe._cooked) {
    closeModal();
  } else {
    updateCookedButtonState(recipe._cooked);
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
