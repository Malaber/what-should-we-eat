import {publicKeyFromJSON, credentialToJSON} from '/auth/assets/fastpasskey.js';
const $ = id => document.getElementById(id);
let action;
async function api(path, body) {
  const r = await fetch(`/auth/${path}`, body ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)} : {});
  const data = await r.json();
  if (!r.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Could not update passkeys.');
  return data;
}
async function refresh() {
  const keys = await api('passkeys'); $('keys').replaceChildren();
  for (const key of keys) {
    const row = document.createElement('section'); const title = document.createElement('h2'); title.textContent = key.name; row.append(title);
    const dates = document.createElement('p'); dates.className = 'help'; dates.textContent = key.last_used_at ? `Last used ${new Date(key.last_used_at).toLocaleString()}` : 'Not used since enrollment'; row.append(dates);
    for (const kind of ['rename','delete']) { const b = document.createElement('button'); b.textContent = kind === 'rename' ? 'Rename' : 'Delete…'; b.onclick = () => show(kind, key); row.append(b); }
    $('keys').append(row);
  }
}
function show(kind, key) {
  action = {action:kind, key_id:key?.id};
  $('action-title').textContent = {add:'Add a passkey',rename:'Rename passkey',delete:'Delete this passkey?',replace:'Replace every passkey?',delete_all:'Delete all passkeys?'}[kind];
  $('action-copy').textContent = kind === 'delete_all' ? 'You will be signed out on every device. Your recipes stay, but you will need an administrator enrollment link to sign in again. This cannot be undone.' : kind === 'replace' ? 'Existing keys will be removed only after the new passkey is created successfully.' : 'Confirm with a passkey belonging to this account.';
  $('name-label').hidden = ['delete','delete_all'].includes(kind); $('key-name').value = key?.name || ''; $('key-name').required = !$('name-label').hidden;
  $('confirm-label').hidden = kind !== 'delete_all'; $('confirmation').value = ''; $('confirmation').required = kind === 'delete_all';
  $('action-dialog').showModal();
}
$('add').onclick = () => show('add'); $('replace').onclick = () => show('replace'); $('delete-all').onclick = () => show('delete_all'); $('cancel').onclick = () => $('action-dialog').close();
$('action-form').onsubmit = async event => {
  event.preventDefault(); $('error').textContent = ''; $('status').textContent = '';
  const buttons = [...document.querySelectorAll('button')]; buttons.forEach(b => b.disabled = true);
  try {
    const options = await api('passkeys/action/options', {...action, name:$('key-name').value || 'Passkey', confirmation:$('confirmation').value});
    const proof = await navigator.credentials.get({publicKey:publicKeyFromJSON(options)});
    const result = await api('passkeys/action/verify', {credential:credentialToJSON(proof)});
    if (result.options) {
      const key = await navigator.credentials.create({publicKey:publicKeyFromJSON(result.options)});
      await api('passkeys/register/verify', {credential:credentialToJSON(key)});
    }
    $('action-dialog').close();
    if (result.signed_out) { localStorage.removeItem('wswe_token'); location.assign('/auth/login'); return; }
    $('status').textContent = 'Passkeys updated.'; await refresh();
  } catch (error) { $('action-dialog').close(); $('error').textContent = error.name === 'NotAllowedError' ? 'Cancelled. Your passkeys were not changed.' : error.message; }
  finally { buttons.forEach(b => b.disabled = false); }
};
refresh().catch(error => $('error').textContent = error.message);
