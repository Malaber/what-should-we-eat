import { authenticate } from '/passkey-ceremony.js';

const params = new URLSearchParams(location.search);
const enrollment = new URLSearchParams(location.hash.slice(1)).get('enroll');
if (enrollment) history.replaceState(null, '', location.pathname + location.search);
document.getElementById('server').textContent = window.t('auth.server').replace('{server}', location.host);
if (enrollment) {
  document.getElementById('enroll').hidden = false;
  document.getElementById('sign-in').hidden = true;
  document.getElementById('registration').hidden = true;
}

document.getElementById('sign-in').onclick = () => authenticate('login');
document.getElementById('enroll').onclick = () => authenticate('enroll', {token: enrollment});
document.getElementById('register').onsubmit = event => {
  event.preventDefault(); authenticate('register', Object.fromEntries(new FormData(event.target)));
};
