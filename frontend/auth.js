// ============================================================
// auth.js — Shared Authentication Logic
// ============================================================

const authHTML = `
  <div id="auth-controls" style="display: flex; gap: 12px; align-items: center;">
    <button id="btn-show-login" class="btn btn-secondary btn-sm" style="border-radius: var(--radius-pill);">Log In</button>
    <button id="btn-show-signup" class="btn btn-primary btn-sm" style="border-radius: var(--radius-pill);">Sign Up</button>
  </div>
  <div id="user-controls" style="display: none; gap: 12px; align-items: center;">
    <span id="user-greeting" style="font-size: 0.9rem; font-weight: 600; color: var(--orange-dark);"></span>
    <button id="btn-logout" class="btn btn-secondary btn-sm" style="border-radius: var(--radius-pill); border-color: var(--orange-pale);">Log Out</button>
  </div>
`;

const modalsHTML = `
  <div class="modal-overlay" id="login-modal" style="display:none; z-index:9000;">
    <div class="modal modal-sm" style="padding: 32px; text-align: center; position: relative;">
      <button class="btn btn-icon btn-close-auth" id="btn-close-login" style="position: absolute; top: 16px; right: 16px; box-shadow: none; border: none;">✕</button>
      <div style="font-size: 3rem; margin-bottom: 12px;">👋</div>
      <h2 style="font-family: var(--font-display); font-size: 2rem; margin-bottom: 8px; color: var(--text);">Welcome Back</h2>
      <p style="color: var(--text-muted); margin-bottom: 24px; font-size: 0.95rem;">Log in to access your household recipes.</p>
      
      <form id="login-form" style="display: flex; flex-direction: column; gap: 16px; text-align: left;">
        <div class="control-group">
          <label for="login-email">Email</label>
          <input type="email" id="login-email" required placeholder="chef@example.com" />
        </div>
        <div class="control-group">
          <label for="login-password">Password</label>
          <input type="password" id="login-password" required placeholder="••••••••" />
        </div>
        <div id="login-error" style="color: #d32f2f; font-size: 0.85rem; font-weight: 600; display: none; text-align: center;"></div>
        <button type="submit" class="btn btn-primary" style="margin-top: 8px; width: 100%; font-size: 1.05rem; padding: 14px;">Log In</button>
      </form>
      <p style="margin-top: 24px; font-size: 0.9rem; color: var(--text-muted);">
        Don't have an account? <a href="#" id="link-to-signup" style="color: var(--orange-dark); font-weight: 600; text-decoration: none;">Sign up here</a>
      </p>
    </div>
  </div>

  <div class="modal-overlay" id="signup-modal" style="display:none; z-index:9000;">
    <div class="modal modal-sm" style="padding: 32px; text-align: center; position: relative;">
      <button class="btn btn-icon btn-close-auth" id="btn-close-signup" style="position: absolute; top: 16px; right: 16px; box-shadow: none; border: none;">✕</button>
      <div style="font-size: 3rem; margin-bottom: 12px;">✨</div>
      <h2 style="font-family: var(--font-display); font-size: 2rem; margin-bottom: 8px; color: var(--text);">Join the Kitchen</h2>
      <p style="color: var(--text-muted); margin-bottom: 24px; font-size: 0.95rem;">Create an account to start your own household.</p>
      
      <form id="signup-form" style="display: flex; flex-direction: column; gap: 16px; text-align: left;">
        <div class="control-group">
          <label for="signup-name">Name (Optional)</label>
          <input type="text" id="signup-name" placeholder="Gordon Ramsay" />
        </div>
        <div class="control-group">
          <label for="signup-email">Email</label>
          <input type="email" id="signup-email" required placeholder="chef@example.com" />
        </div>
        <div class="control-group">
          <label for="signup-password">Password</label>
          <input type="password" id="signup-password" required placeholder="••••••••" minlength="8" />
        </div>
        <div id="signup-error" style="color: #d32f2f; font-size: 0.85rem; font-weight: 600; display: none; text-align: center;"></div>
        <button type="submit" class="btn btn-primary" style="margin-top: 8px; width: 100%; font-size: 1.05rem; padding: 14px;">Create Account</button>
      </form>
      <p style="margin-top: 24px; font-size: 0.9rem; color: var(--text-muted);">
        Already have an account? <a href="#" id="link-to-login" style="color: var(--green-dark); font-weight: 600; text-decoration: none;">Log in here</a>
      </p>
    </div>
  </div>
`;

const loginGateHTML = `
  <div id="login-gate" style="position:fixed; inset:0; z-index:8000; background:rgba(0,0,0,0.55); backdrop-filter:blur(6px); display:flex; align-items:center; justify-content:center;">
    <div style="background:var(--bg-card, #fff); border-radius:20px; padding:48px 40px; text-align:center; max-width:400px; width:90%; box-shadow:0 20px 60px rgba(0,0,0,0.3);">
      <div style="font-size:4rem; margin-bottom:16px;">🍳</div>
      <h2 style="font-family:var(--font-display, inherit); font-size:1.8rem; margin-bottom:8px;">Welcome!</h2>
      <p style="color:var(--text-muted, #888); margin-bottom:28px; font-size:1rem; line-height:1.5;">Log in or create an account to start planning your meals.</p>
      <div style="display:flex; gap:12px; justify-content:center;">
        <button id="gate-login" class="btn btn-primary" style="padding:12px 28px; font-size:1rem;">Log In</button>
        <button id="gate-signup" class="btn btn-secondary" style="padding:12px 28px; font-size:1rem;">Sign Up</button>
      </div>
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
    document.body.insertAdjacentHTML('beforeend', modalsHTML);

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
    this.$loginModal = document.getElementById('login-modal');
    this.$signupModal = document.getElementById('signup-modal');
    this.$loginError = document.getElementById('login-error');
    this.$signupError = document.getElementById('signup-error');
  }

  bindEvents() {
    document.getElementById('btn-show-login').addEventListener('click', () => { this.$loginModal.style.display = 'flex'; this.$signupModal.style.display = 'none'; });
    document.getElementById('btn-show-signup').addEventListener('click', () => { this.$signupModal.style.display = 'flex'; this.$loginModal.style.display = 'none'; });
    document.getElementById('btn-close-login').addEventListener('click', () => { this.$loginModal.style.display = 'none'; });
    document.getElementById('btn-close-signup').addEventListener('click', () => { this.$signupModal.style.display = 'none'; });
    document.getElementById('link-to-signup').addEventListener('click', (e) => { e.preventDefault(); this.$loginModal.style.display = 'none'; this.$signupModal.style.display = 'flex'; });
    document.getElementById('link-to-login').addEventListener('click', (e) => { e.preventDefault(); this.$signupModal.style.display = 'none'; this.$loginModal.style.display = 'flex'; });
    document.getElementById('btn-logout').addEventListener('click', () => this.handleLogout());

    document.getElementById('login-form').addEventListener('submit', (e) => this.handleLogin(e));
    document.getElementById('signup-form').addEventListener('submit', (e) => this.handleSignup(e));
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
        document.getElementById('gate-login').addEventListener('click', () => {
          document.getElementById('login-gate').style.display = 'none';
          this.$loginModal.style.display = 'flex';
        });
        document.getElementById('gate-signup').addEventListener('click', () => {
          document.getElementById('login-gate').style.display = 'none';
          this.$signupModal.style.display = 'flex';
        });
      }
    }
  }

  async handleLogin(e) {
    e.preventDefault();
    this.$loginError.style.display = 'none';
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    try {
      const res = await fetch('/users/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });
      
      if (res.ok) {
        const data = await res.json();
        this.token = data.access_token;
        localStorage.setItem('wswe_token', this.token);
        this.$loginModal.style.display = 'none';
        await this.fetchCurrentUser();
      } else {
        const err = await res.json();
        this.$loginError.textContent = err.detail || 'Login failed';
        this.$loginError.style.display = 'block';
      }
    } catch (err) {
      this.$loginError.textContent = 'Network error';
      this.$loginError.style.display = 'block';
    }
  }

  async handleSignup(e) {
    e.preventDefault();
    this.$signupError.style.display = 'none';
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;

    try {
      const res = await fetch('/users/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name })
      });
      
      if (res.ok) {
        document.getElementById('login-email').value = email;
        document.getElementById('login-password').value = password;
        this.$signupModal.style.display = 'none';
        this.handleLogin(new Event('submit'));
      } else {
        const err = await res.json();
        this.$signupError.textContent = err.detail || 'Signup failed';
        this.$signupError.style.display = 'block';
      }
    } catch (err) {
      this.$signupError.textContent = 'Network error';
      this.$signupError.style.display = 'block';
    }
  }

  handleLogout(emit = true) {
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
