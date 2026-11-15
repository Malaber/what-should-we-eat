const section = document.getElementById('recipe');
const cookButton = document.getElementById('cook-now');
const copyButton = document.getElementById('copy');
const status = document.getElementById('status');
const storageKey = 'onionary.shared-cooking';
let link;
let generation = 0;

copyButton.onclick = async () => {
  try { await navigator.clipboard.writeText(link); status.textContent = window.t('share.copied'); }
  catch { status.textContent = link; }
};

function readProgress() {
  try {
    const states = JSON.parse(localStorage.getItem(storageKey));
    return Array.isArray(states) ? states : [];
  } catch { return []; }
}

function saveProgress(key, active, checked) {
  if (!key) return;
  const recent = readProgress().filter(state => state?.key !== key).slice(0, 19);
  try { localStorage.setItem(storageKey, JSON.stringify([{key, active, checked: [...checked]}, ...recent])); }
  catch { /* The current checklist still works when storage is unavailable. */ }
}

function element(tag, text) {
  const node = document.createElement(tag);
  if (text) node.textContent = text;
  return node;
}

function renderRecipe(recipe, active, checked, persist) {
  const ingredients = recipe.ingredients || [];
  const steps = [...(recipe.instruction_steps || [])].sort((a, b) => a.step_number - b.step_number);
  section.replaceChildren(element('h2', recipe.name));
  if (recipe.notes) section.append(element('p', recipe.notes));
  for (const [key, rows, text] of [
    ['ingredients', ingredients, ingredient => [ingredient.quantity, ingredient.unit, ingredient.name].filter(value => value != null && value !== '').join(' ')],
    ['steps', steps, step => resolveIngredientPlaceholders(step.description, ingredients)],
  ]) {
    section.append(element('h3', window.t(`share.${key}`)));
    let group;
    let list;
    for (const [index, row] of rows.entries()) {
      if (!list || group !== row.group_name) {
        group = row.group_name;
        if (group) section.append(element('h4', group));
        list = element(key === 'steps' ? 'ol' : 'ul');
        list.className = 'shared-recipe-list';
        if (key === 'steps') list.start = index + 1;
        section.append(list);
      }
      const item = element('li');
      if (!active) item.textContent = text(row);
      else {
        const id = `${key}-${index}`;
        const label = element('label');
        const checkbox = element('input');
        checkbox.type = 'checkbox';
        checkbox.checked = checked.has(id);
        checkbox.onchange = () => {
          if (checkbox.checked) checked.add(id);
          else checked.delete(id);
          persist();
        };
        label.append(checkbox, element('span', text(row)));
        item.append(label);
      }
      list.append(item);
    }
  }
}

async function loadCopy() {
  const current = ++generation;
  const token = location.hash.slice(1) || history.state?.onionaryCopy || '';
  history.replaceState({onionaryCopy: token}, '', location.pathname);
  link = new URL(`${location.pathname}#${encodeURIComponent(token)}`, location.origin).href;
  section.replaceChildren();
  cookButton.hidden = true;
  copyButton.hidden = true;
  status.textContent = '';
  const error = document.getElementById('error');
  error.textContent = '';
  try {
    const response = await fetch('/recipe-shares/resolve', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({token}),
    });
    if (!response.ok) throw new Error(window.t('share.unavailable'));
    const {recipe} = await response.json();
    // Persist only a digest and check IDs. Reads still require a live share.
    const digest = await crypto.subtle?.digest('SHA-256', new TextEncoder().encode(token));
    const key = digest && Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
    if (current !== generation) return;
    const saved = readProgress().find(state => state?.key === key);
    let active = saved?.active === true;
    const checked = new Set(Array.isArray(saved?.checked) ? saved.checked : []);
    const persist = () => saveProgress(key, active, checked);
    const show = () => {
      renderRecipe(recipe, active, checked, persist);
      cookButton.textContent = window.t(active ? 'share.stop-cooking' : 'share.cook');
      cookButton.setAttribute('aria-pressed', String(active));
    };
    cookButton.onclick = () => { active = !active; persist(); show(); };
    show();
    cookButton.hidden = false;
    copyButton.hidden = false;
  } catch (failure) {
    if (current === generation) error.textContent = failure.message;
  }
}
window.addEventListener('hashchange', loadCopy);
loadCopy();
