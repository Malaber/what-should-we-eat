import { publicKeyFromJSON, credentialToJSON } from '/auth/assets/fastpasskey.js';

const params = new URLSearchParams(location.search);
const enrollment = new URLSearchParams(location.hash.slice(1)).get('enroll');
if (enrollment) history.replaceState(null, '', location.pathname + location.search);
document.getElementById('server').textContent = `Signing in to ${location.host}`;
if (enrollment) {
  document.getElementById('enroll').hidden = false;
  document.getElementById('sign-in').hidden = true;
  document.getElementById('registration').hidden = true;
}

async function post(path, body) {
  const response = await fetch(`/auth/${path}`, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Sign-in failed. Please try again.');
  return data;
}

async function authenticate(kind, body = {}) {
  const error = document.getElementById('error'); error.textContent = '';
  document.querySelectorAll('button').forEach(b => b.disabled = true);
  try {
    if (!window.PublicKeyCredential) throw new Error('This browser does not support passkeys. Open in Safari or another current browser.');
    const options = await post(`${kind}/options`, body);
    const publicKey = publicKeyFromJSON(options);
    const credential = kind === 'login' ? await navigator.credentials.get({publicKey}) : await navigator.credentials.create({publicKey});
    if (!credential) throw new Error('No passkey selected.');
    const result = await post(`${kind}/verify`, {credential: credentialToJSON(credential)});
    if (params.has('state') && params.has('code_challenge')) {
      const query = new URLSearchParams({state: params.get('state'), code_challenge: params.get('code_challenge')});
      location.assign(`/auth/mobile/authorize?${query}`);
    } else {
      localStorage.setItem('wswe_token', result.access_token);
      location.assign('/');
    }
  } catch (err) {
    error.textContent = err.name === 'NotAllowedError' ? 'Passkey request cancelled. You can try again.' : err.message;
  } finally { document.querySelectorAll('button').forEach(b => b.disabled = false); }
}

document.getElementById('sign-in').onclick = () => authenticate('login');
document.getElementById('enroll').onclick = () => authenticate('enroll', {token: enrollment});
document.getElementById('register').onsubmit = event => {
  event.preventDefault(); authenticate('register', Object.fromEntries(new FormData(event.target)));
};
