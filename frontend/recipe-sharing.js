// Uses existing signed-in recipe page token; links themselves never contain credentials.
async function shareRecipe(id) {
  try {
    const response = await fetch('/recipe-shares', {method:'POST', headers:getAuthHeaders({'Content-Type':'application/json'}), body:JSON.stringify({recipe_id:id,hours:24})});
    if (!response.ok) throw new Error(window.t('share.failed'));
    const share = await response.json();
    const dialog = document.createElement('dialog'); dialog.className = 'auth-surface';
    const title = document.createElement('h2'); title.id = 'share-title'; dialog.setAttribute('aria-labelledby', title.id); title.textContent = window.t('share.title');
    const info = document.createElement('p'); info.textContent = window.t('share.warning') + ' ' + new Date(share.expires_at).toLocaleString(window.I18n.lang);
    const field = document.createElement('input'); field.value = share.url; field.readOnly = true; field.setAttribute('aria-label',window.t('share.copy'));
    const copy = document.createElement('button'); copy.textContent = window.t('share.copy'); copy.onclick = async () => { try { await navigator.clipboard.writeText(share.url); copy.textContent = window.t('share.copied'); } catch { field.select(); } };
    const done = document.createElement('button'); done.textContent = window.t('share.done'); done.onclick = () => dialog.close();
    dialog.append(title,info,field,copy,done); dialog.onclose=()=>dialog.remove(); document.body.append(dialog);dialog.showModal();
  } catch (error) { toast(error.message); }
}
async function manageRecipeLinks() {
  const response = await fetch('/recipe-shares', {headers:getAuthHeaders()});
  if (!response.ok) { toast(window.t('share.failed')); return; }
  const dialog=document.createElement('dialog'); dialog.className='auth-surface'; dialog.setAttribute('aria-label', window.t('share.title'));
  for (const share of await response.json()) {
    const row=document.createElement('p'); row.textContent=share.name+' · '+new Date(share.expires_at).toLocaleString(window.I18n.lang);
    const revoke=document.createElement('button');revoke.textContent=window.t(share.revoked?'share.revoked':'share.revoke');revoke.disabled=share.revoked;
    revoke.onclick=async()=>{const result=await fetch('/recipe-shares/'+encodeURIComponent(share.id),{method:'DELETE',headers:getAuthHeaders()});if(result.ok){revoke.disabled=true;revoke.textContent=window.t('share.revoked');}else toast(window.t('share.failed'));};
    dialog.append(row,revoke);
  }
  const done=document.createElement('button');done.textContent=window.t('share.done');done.onclick=()=>dialog.close();dialog.append(done);dialog.onclose=()=>dialog.remove();document.body.append(dialog);dialog.showModal();
}
