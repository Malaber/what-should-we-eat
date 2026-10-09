let link = location.href;
let generation = 0;
document.getElementById('copy').onclick = async () => {
  try { await navigator.clipboard.writeText(link); document.getElementById('status').textContent = window.t('share.copied'); }
  catch { document.getElementById('status').textContent = link; }
};
async function loadCopy() {
  const current = ++generation;
  link = location.href;
  const token = location.hash.slice(1);
  history.replaceState(null, "", location.pathname);
  document.getElementById("recipe").replaceChildren();
  document.getElementById("error").textContent = "";
  try {
    const response = await fetch('/recipe-shares/resolve', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({token})});
    if (!response.ok) throw new Error(window.t('share.unavailable'));
    const {recipe} = await response.json();
    if (current !== generation) return;
    const section = document.getElementById('recipe');
    const heading = document.createElement('h2'); heading.textContent = recipe.name; section.append(heading);
    const notes = document.createElement('p'); notes.textContent = recipe.notes || ''; section.append(notes);
    for (const value of [...recipe.ingredients.map(i => [i.quantity, i.unit, i.name].filter(x => x != null).join(' ')), ...recipe.instruction_steps.map(s => s.description)]) {
      const p = document.createElement('p'); p.textContent = value; section.append(p);
    }
  } catch (error) { if (current === generation) document.getElementById('error').textContent = error.message; }
}
window.addEventListener('hashchange', loadCopy);
loadCopy();
