// ============================================================
// auth.js — Shared Authentication Logic
// ============================================================

const authHTML = `
  <div id="auth-controls" style="display: flex; gap: 12px; align-items: center;">
    <button id="btn-show-login" class="btn btn-secondary btn-sm" style="border-radius: var(--radius-pill);">Sign in with passkey</button>
    <button id="btn-show-signup" class="btn btn-primary btn-sm" style="border-radius: var(--radius-pill);">Sign Up</button>
  </div>
  <div id="user-controls" style="display: none; gap: 12px; align-items: center;">
    <a href="/auth/security">Passkeys</a>
    <span id="user-greeting" style="font-size: 0.9rem; font-weight: 600; color: var(--orange-dark);"></span>
    <button id="btn-logout" class="btn btn-secondary btn-sm" style="border-radius: var(--radius-pill); border-color: var(--orange-pale);">Log Out</button>
  </div>
`;

const authTheme = document.createElement('link');
authTheme.rel = 'stylesheet'; authTheme.href = '/auth-theme.css'; document.head.append(authTheme);
const loginGateHTML = `
  <div id="login-gate" class="auth-surface">
    <div class="auth-card">
      <div class="mark" aria-hidden="true">🧅</div>
      <p class="eyebrow">YOUR COOKING COMPANION</p>
      <h2>Welcome to Onionary.</h2>
      <p>Your recipes. Your kitchen. Pick up where you left off.</p>
      <button id="gate-login">Sign in with a passkey</button>
      <button id="gate-signup">New here? Create an account</button>
      <p class="help">Use Face ID, Touch ID, a security key, or your password manager.</p>
    </div>
  </div>
`;

class AuthHandler {
  constructor() {
    this.token = localStorage.getItem('wswe_token') || null;
    this.user = null;
    this.init();
  }

  async init() {
    const mount = document.getElementById('auth-mount');
    if (!mount) return;

    mount.innerHTML = authHTML;


    this.cacheDOM();
    this.bindEvents();

    if (this.token) {
      await this.fetchCurrentUser();
    }

    // Show login gate if not authenticated
    this.updateLoginGate();
  }

  cacheDOM() {
    this.$authControls = document.getElementById('auth-controls');
    this.$userControls = document.getElementById('user-controls');
    this.$userGreeting = document.getElementById('user-greeting');
  }

  bindEvents() {
    document.getElementById('btn-show-login').onclick = () => location.assign('/auth/login');
    document.getElementById('btn-show-signup').onclick = () => location.assign('/auth/login');
    document.getElementById('btn-logout').onclick = () => this.handleLogout();
  }

  async fetchCurrentUser() {
    try {
      const res = await fetch('/users/me', {
        headers: { 'Authorization': `Bearer ${this.token}` }
      });
      if (res.ok) {
        this.user = await res.json();
        this.updateAuthUI();
      } else {
        this.handleLogout(false); // don't emit event on boot fail
      }
    } catch (err) {
      console.error(err);
    }
  }

  updateAuthUI() {
    if (this.user) {
      this.$authControls.style.display = 'none';
      this.$userControls.style.display = 'flex';
      this.$userGreeting.textContent = `Hi, ${this.user.name || this.user.email}`;
    } else {
      this.$authControls.style.display = 'flex';
      this.$userControls.style.display = 'none';
    }
    this.updateLoginGate();
    window.dispatchEvent(new CustomEvent('wswe_auth_changed', { detail: { token: this.token } }));
  }

  updateLoginGate() {
    const existing = document.getElementById('login-gate');
    if (this.user) {
      // Logged in — remove gate
      if (existing) existing.remove();
    } else {
      // Not logged in — show gate
      if (!existing) {
        document.body.insertAdjacentHTML('beforeend', loginGateHTML);
        document.getElementById('gate-login').onclick = () => location.assign('/auth/login');
        document.getElementById('gate-signup').onclick = () => location.assign('/auth/login');
      }
    }
  }

  handleLogout(emit = true) {
    fetch('/auth/logout', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'}).catch(() => {});
    this.token = null;
    this.user = null;
    localStorage.removeItem('wswe_token');

    this.$authControls.style.display = 'flex';
    this.$userControls.style.display = 'none';
    this.updateLoginGate();

    if (emit) {
      window.dispatchEvent(new CustomEvent('wswe_auth_changed', { detail: { token: null } }));
    }
  }
}

window.WSWEAuth = new AuthHandler();

// ── Burger menu toggle ──────────────────────────────────────────
(function initBurgerMenu() {
  const burger = document.getElementById('burger-btn');
  const navLinks = document.getElementById('nav-links');
  if (!burger || !navLinks) return;

  burger.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = navLinks.classList.toggle('open');
    burger.textContent = isOpen ? '✕' : '☰';
    burger.setAttribute('aria-expanded', isOpen);
    document.body.style.overflow = isOpen ? 'hidden' : '';
  });

  // Close menu when a nav link is clicked
  navLinks.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('open');
      burger.textContent = '☰';
      document.body.style.overflow = '';
    });
  });

  // Close menu when clicking outside
  document.addEventListener('click', (e) => {
    if (!navLinks.contains(e.target) && !burger.contains(e.target)) {
      if (navLinks.classList.contains('open')) {
        navLinks.classList.remove('open');
        burger.textContent = '☰';
        document.body.style.overflow = '';
      }
    }
  });
})();
