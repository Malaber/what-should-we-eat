const I18n = {
  lang: 'en', // will be overwritten in init()
  translations: {},

  async init() {
    // Check localStorage or fallback to navigator languages
    let preferredLang = localStorage.getItem('app_lang');
    if (!preferredLang) {
      const userLang = navigator.language || navigator.userLanguage || "en";
      preferredLang = userLang.startsWith('de') ? 'de' : 'en';
    }

    if (preferredLang !== 'en' && preferredLang !== 'de') {
      preferredLang = 'en';
    }

    this.lang = preferredLang;
    await this.loadTranslations(this.lang);
    this.updateDOM();
    window.dispatchEvent(new CustomEvent('i18n:loaded'));
  },

  async loadTranslations(lang) {
    try {
      const resp = await fetch(`/locales/${lang}.json`);
      if (resp.ok) {
        this.translations = await resp.json();
      } else {
        console.warn(`Could not load translations for lang ${lang}`);
        if(lang !== 'en') {
          // fallback to en
          this.lang = 'en';
          await this.loadTranslations('en');
        }
      }
    } catch (e) {
      console.error("I18n Load Error:", e);
    }
  },

  setLang(lang) {
    this.lang = lang;
    localStorage.setItem('app_lang', lang);
    this.init(); // reload and update
  },

  t(key, fallback) {
    if (this.translations[key] !== undefined) {
      return this.translations[key];
    }
    // Handle API backend error translations
    // e.g., if key starts with "error." or similar, we just use fallback
    return fallback || key;
  },

  updateDOM() {
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(el => {
      const key = el.getAttribute('data-i18n');
      const val = this.t(key);
      if (val !== key) {
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
          if (el.hasAttribute('placeholder')) {
             el.placeholder = val;
          }
        } else {
           el.innerHTML = val;
        }
      }
    });

    // Handle language switchers (set their value to current language)
    const switchers = document.querySelectorAll('.lang-switcher');
    switchers.forEach(s => {
      s.value = this.lang;
    });
  }
};

document.addEventListener('DOMContentLoaded', () => {
    // Inject lang switcher if not exists in nav
    const navLinks = document.getElementById('nav-links');
    if (navLinks && !document.getElementById('lang-switcher')) {
        const select = document.createElement('select');
        select.id = 'lang-switcher';
        select.className = 'lang-switcher';
        select.style.marginLeft = 'auto'; // push to right
        select.style.padding = '4px 8px';
        select.style.borderRadius = '6px';
        select.style.border = '1px solid var(--border)';
        select.style.background = 'var(--bg-soft)';
        select.style.cursor = 'pointer';
        select.style.fontFamily = 'inherit';
        select.style.fontSize = '14px';
        
        select.innerHTML = `
            <option value="en">🇬🇧 EN</option>
            <option value="de">🇩🇪 DE</option>
        `;
        select.addEventListener('change', (e) => {
            I18n.setLang(e.target.value);
        });
        navLinks.appendChild(select);
    }

    I18n.init(); // init will update DOM
});

// Expose globally
window.I18n = I18n;
window.t = I18n.t.bind(I18n);
