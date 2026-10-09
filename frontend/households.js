/* ============================================================
   households.js — Onionary — Households Page Logic
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
let households = [];
let activeHouseholdId = null;
let personalHouseholdId = null;
let pendingLeaveId = null;

// ── DOM refs ───────────────────────────────────────────────────
const $grid         = document.getElementById('households-grid');
const $empty        = document.getElementById('hh-empty');
const $btnCreate    = document.getElementById('btn-create-household');
const $btnJoin      = document.getElementById('btn-join-household');
const $btnImport    = document.getElementById('btn-import-recipes');
const $createModal  = document.getElementById('create-modal');
const $joinModal    = document.getElementById('join-modal');
const $importModal  = document.getElementById('import-modal');
const $leaveModal   = document.getElementById('leave-modal');
const $createForm   = document.getElementById('create-form');
const $joinForm     = document.getElementById('join-form');
const $importForm   = document.getElementById('import-form');
const $createName   = document.getElementById('create-name');
const $joinCode     = document.getElementById('join-code');
const $importCode   = document.getElementById('import-code');
const $createError  = document.getElementById('create-error');
const $joinError    = document.getElementById('join-error');
const $importError  = document.getElementById('import-error');
const $leaveName    = document.getElementById('leave-household-name');

// ── Init ───────────────────────────────────────────────────────
function init() {
  window.addEventListener('wswe_auth_changed', () => {
    if (isLoggedIn()) {
      loadHouseholds();
    } else {
      households = [];
      renderGrid();
    }
  });

  if (isLoggedIn()) {
    loadHouseholds();
  } else {
    renderGrid();
  }

  // Button handlers
  $btnCreate.addEventListener('click', () => openModal($createModal));
  $btnJoin.addEventListener('click', () => openModal($joinModal));
  $btnImport.addEventListener('click', () => openModal($importModal));

  document.getElementById('btn-close-create').addEventListener('click', () => closeModal($createModal));
  document.getElementById('btn-close-join').addEventListener('click', () => closeModal($joinModal));
  document.getElementById('btn-close-import').addEventListener('click', () => closeModal($importModal));

  // Leave modal handlers
  document.getElementById('btn-cancel-leave').addEventListener('click', () => closeModal($leaveModal));
  document.getElementById('btn-confirm-leave').addEventListener('click', confirmLeave);

  // Close modals on overlay click
  [$createModal, $joinModal, $importModal, $leaveModal].forEach(m => {
    m.addEventListener('click', (e) => {
      if (e.target === m) closeModal(m);
    });
  });

  // Form handlers
  $createForm.addEventListener('submit', handleCreate);
  $joinForm.addEventListener('submit', handleJoin);
  $importForm.addEventListener('submit', handleImport);
}

// ── Load from API ──────────────────────────────────────────────
async function loadHouseholds() {
  try {
    // Get user info for active/personal household
    const meRes = await fetch(`${API}/users/me`, { headers: getAuthHeaders() });
    if (!meRes.ok) throw new Error(window.t('feedback.20'));
    const me = await meRes.json();
    activeHouseholdId = me.active_household_id;
    personalHouseholdId = me.personal_household_id;

    // Get household list
    const res = await fetch(`${API}/households`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error(window.t('feedback.21'));
    households = await res.json();

    renderGrid();
  } catch (err) {
    console.error('Error loading households:', err);
  }
}

// ── Render ──────────────────────────────────────────────────────
function renderGrid() {
  if (!households.length) {
    $grid.style.display = 'none';
    $empty.style.display = '';
    return;
  }
  $grid.style.display = '';
  $empty.style.display = 'none';

  // Sort: active first, then alphabetical
  const sorted = [...households].sort((a, b) => {
    if (a.id === activeHouseholdId) return -1;
    if (b.id === activeHouseholdId) return 1;
    return a.name.localeCompare(b.name);
  });

  $grid.innerHTML = sorted.map((h, i) => {
    const isActive = h.id === activeHouseholdId;
    const isPersonal = h.id === personalHouseholdId;
    const icon = isPersonal ? '👤' : '👨‍👩‍👧‍👦';
    const delay = i * 0.06;

    return `
      <div class="hh-card ${isActive ? 'hh-card--active' : ''}" style="animation-delay: ${delay}s" data-id="${h.id}">
        <div class="hh-card-glow"></div>
        <div class="hh-card-content">
          <div class="hh-card-icon">${icon}</div>
          <div class="hh-card-info">
            <h3 class="hh-card-name">${h.name}</h3>
            <span class="hh-card-id" style="font-family: monospace; letter-spacing: 0.1em;">Code: ${h.invite_code}</span>
          </div>
          ${isActive
            ? `<div class="hh-badge hh-badge--active">${window.t("ui.7")}</div>`
            : `<button class="btn btn-primary btn-sm hh-switch-btn" data-id="${h.id}">${window.t("ui.6")}</button>`
          }
        </div>
        <div class="hh-card-footer">
          ${isActive
            ? `<span class="hh-status-dot"></span><span style="color: var(--green-dark); font-weight: 600; font-size: 0.82rem;">${window.t("ui.4")}</span>`
            : `<span style="color: var(--text-light); font-size: 0.82rem;">${window.t("ui.3")}</span>`
          }
          ${!isPersonal
            ? `<button class="btn btn-sm hh-leave-btn" data-id="${h.id}" title="${window.t('feedback.38')}" style="margin-left: auto; padding: 6px 12px; background: none; border: 1px solid var(--border); color: var(--text-light); font-size: 0.78rem;">${window.t("ui.5")}</button>`
            : ''
          }
        </div>
      </div>
    `;
  }).join('');

  // Wire up switch buttons
  $grid.querySelectorAll('.hh-switch-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      handleSwitch(parseInt(btn.dataset.id));
    });
  });

  // Wire up leave buttons
  $grid.querySelectorAll('.hh-leave-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      handleLeave(parseInt(btn.dataset.id));
    });
  });
}

// ── Switch Household ───────────────────────────────────────────
async function handleSwitch(householdId) {
  try {
    const res = await fetch(`${API}/households/switch/${householdId}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      showToast(err.detail || window.t('feedback.22'), 'error');
      return;
    }
    const user = await res.json();
    activeHouseholdId = user.active_household_id;
    renderGrid();
    showToast(window.t('feedback.switched').replace('{name}', households.find(h => h.id === householdId)?.name || ''), 'success');

    // Dispatch auth change so other tabs/listeners know
    window.dispatchEvent(new Event('wswe_auth_changed'));
  } catch (err) {
    console.error('Switch error:', err);
    showToast(window.t('Failed to switch household'), 'error');
  }
}

// ── Create Household ───────────────────────────────────────────
async function handleCreate(e) {
  e.preventDefault();
  $createError.style.display = 'none';

  const name = $createName.value.trim();
  if (!name) return;

  try {
    const res = await fetch(`${API}/households`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ name }),
    });
    if (!res.ok) {
      const err = await res.json();
      $createError.textContent = err.detail || window.t('feedback.23');
      $createError.style.display = '';
      return;
    }
    closeModal($createModal);
    $createForm.reset();
    showToast(window.t('feedback.created').replace('{name}', name), 'success');
    await loadHouseholds();
  } catch (err) {
    $createError.textContent = window.t('feedback.24');
    $createError.style.display = '';
  }
}

// ── Join Household ─────────────────────────────────────────────
async function handleJoin(e) {
  e.preventDefault();
  $joinError.style.display = 'none';

  const code = $joinCode.value.trim().toUpperCase();
  if (!code || code.length !== 6) {
    $joinError.textContent = window.t('feedback.25');
    $joinError.style.display = '';
    return;
  }

  try {
    const res = await fetch(`${API}/households/join/${code}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      $joinError.textContent = err.detail || window.t('feedback.26');
      $joinError.style.display = '';
      return;
    }
    const user = await res.json();
    activeHouseholdId = user.active_household_id;
    closeModal($joinModal);
    $joinForm.reset();
    showToast(window.t('Joined household!'), 'success');
    await loadHouseholds();
  } catch (err) {
    $joinError.textContent = window.t('feedback.24');
    $joinError.style.display = '';
  }
}

// ── Import Recipes ─────────────────────────────────────────────
async function handleImport(e) {
  e.preventDefault();
  $importError.style.display = 'none';

  const code = $importCode.value.trim().toUpperCase();
  if (!code || code.length !== 6) {
    $importError.textContent = window.t('feedback.25');
    $importError.style.display = '';
    return;
  }

  try {
    const res = await fetch(`${API}/recipes/import/${code}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      $importError.textContent = err.detail || window.t('feedback.26');
      $importError.style.display = '';
      return;
    }
    const result = await res.json();
    
    if (result.imported_count === 0) {
      $importError.textContent = window.t('feedback.27');
      $importError.style.display = '';
      return;
    }

    closeModal($importModal);
    $importForm.reset();
    showToast(window.t('feedback.imported').replace('{count}', result.imported_count), 'success');
  } catch (err) {
    $importError.textContent = window.t('feedback.24');
    $importError.style.display = '';
  }
}

// ── Leave Household ────────────────────────────────────────────
function handleLeave(householdId) {
  const name = households.find(h => h.id === householdId)?.name || 'this household';
  pendingLeaveId = householdId;
  $leaveName.textContent = name;
  openModal($leaveModal);
}

async function confirmLeave() {
  if (!pendingLeaveId) return;
  const householdId = pendingLeaveId;
  const name = households.find(h => h.id === householdId)?.name || 'this household';
  closeModal($leaveModal);
  pendingLeaveId = null;

  try {
    const res = await fetch(`${API}/households/leave/${householdId}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      showToast(err.detail || window.t('feedback.28'), 'error');
      return;
    }
    const user = await res.json();
    activeHouseholdId = user.active_household_id;
    showToast(window.t('feedback.left').replace('{name}', name), 'success');
    await loadHouseholds();
    window.dispatchEvent(new Event('wswe_auth_changed'));
  } catch (err) {
    showToast(window.t('Failed to leave household'), 'error');
  }
}

// ── Modal helpers ──────────────────────────────────────────────
function openModal(el)  { el.style.display = 'flex'; }
function closeModal(el) { el.style.display = 'none'; }

// ── Toast ──────────────────────────────────────────────────────
function showToast(msg, type = 'success') {
  let toast = document.getElementById('hh-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'hh-toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.background = type === 'error' ? '#d32f2f' : 'var(--text)';
  toast.classList.add('show');
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.remove('show'), 3000);
}

// ── Boot ───────────────────────────────────────────────────────
init();
