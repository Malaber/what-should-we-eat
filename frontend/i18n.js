// Dictionaries are generated from locales/*.json by the backend before this script.
(() => {
  let saved;
  try { saved = localStorage.getItem('app_lang'); } catch (_) {}
  const preferred = saved || (navigator.language || 'en').split('-')[0];
  const lang = preferred === 'de' ? 'de' : 'en';
  document.documentElement.lang = lang;
  // No fallback-language paint while parsing the document. Dynamic code already has t().
  document.documentElement.style.visibility = 'hidden';
  const I18n = {
    lang,
    translations: window.OnionaryTranslations?.[lang] || {},
    t(key) { return this.translations[key] ?? window.OnionaryTranslations?.en?.[key] ?? key; },
    updateDOM() {
      document.querySelectorAll('[data-i18n]').forEach(el => {
        const value = this.t(el.dataset.i18n);
        if (el.matches('input,textarea')) el.placeholder = value;
        else el.innerHTML = value;
      });
      document.querySelectorAll('.lang-switcher').forEach(el => { el.value = this.lang; });
    },
    setLang(value) {
      if (!['en','de','system'].includes(value)) return;
      try { if (value === 'system') localStorage.removeItem('app_lang'); else localStorage.setItem('app_lang', value); } catch (_) {}
      location.reload();
    }
  };
  window.I18n = I18n;
  window.t = I18n.t.bind(I18n);
  document.addEventListener('DOMContentLoaded', () => {
    const nav = document.getElementById('nav-links');
    if (nav && !document.getElementById('lang-switcher')) {
      const select = document.createElement('select'); select.id = 'lang-switcher'; select.className = 'lang-switcher'; select.setAttribute('aria-label','Language / Sprache');
      for (const [value,label] of [['en','EN'],['de','DE'],['system','System']]) select.add(new Option(label,value));
      select.onchange = () => I18n.setLang(select.value); nav.append(select);
    }
    I18n.updateDOM();
    document.documentElement.style.visibility = '';
    window.dispatchEvent(new CustomEvent('i18n:loaded'));
  });
})();
