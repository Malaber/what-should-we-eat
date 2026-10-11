import { publicKeyFromJSON, credentialToJSON } from '/auth/assets/fastpasskey.js';

async function post(path, body) {
  const response = await fetch(`/auth/${path}`, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : window.t('auth.failed'));
  return data;
}

export async function authenticate(kind, body = {}, options = {}) {
  const params = new URLSearchParams(location.search);
  const error = options.error || document.getElementById('error'); error.textContent = '';
  (options.root || document).querySelectorAll('button').forEach(b => b.disabled = true);
  try {
    if (!window.PublicKeyCredential) throw new Error(window.t('auth.unsupported'));
    const options = await post(`${kind}/options`, body);
    const publicKey = publicKeyFromJSON(options);
    const credential = kind === 'login' ? await navigator.credentials.get({publicKey}) : await navigator.credentials.create({publicKey});
    if (!credential) throw new Error(window.t('auth.none'));
    const result = await post(`${kind}/verify`, {credential: credentialToJSON(credential)});
    if (params.has('state') && params.has('code_challenge')) {
      const query = new URLSearchParams({state: params.get('state'), code_challenge: params.get('code_challenge')});
      location.assign(`/auth/mobile/authorize?${query}`);
    } else {
      localStorage.setItem('wswe_token', result.access_token);
      if (options.onSuccess) { await options.onSuccess(result); return; }
      location.assign(params.get('next') === 'security' ? '/auth/security' : params.get('next') === 'admin' ? '/admin/' : '/');
    }
  } catch (err) {
    error.textContent = err.name === 'NotAllowedError' ? window.t('auth.cancelled') : err.message;
  } finally { (options.root || document).querySelectorAll('button').forEach(b => b.disabled = false); }
}

