'use strict';

// ========== Utilities ==========
const qs = (sel, root = document) => root.querySelector(sel);
const qsa = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const show = (el) => el && el.classList.remove('hidden');
const hide = (el) => el && el.classList.add('hidden');

// Role label mapping (backend may use OBSERVER internally)
const roleLabel = (r) => ({ OBSERVER: 'OVERLOOKER' }[r] || r || '');

// Token storage
const tokens = {
  get access() { return localStorage.getItem('abx_access') || ''; },
  set access(v) { localStorage.setItem('abx_access', v || ''); },
  get refresh() { return localStorage.getItem('abx_refresh') || ''; },
  set refresh(v) { localStorage.setItem('abx_refresh', v || ''); },
  clear() { localStorage.removeItem('abx_access'); localStorage.removeItem('abx_refresh'); }
};

// API helper with auto-refresh
async function api(path, opts = {}) {
  const headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
  if (tokens.access) headers['Authorization'] = `Bearer ${tokens.access}`;
  const res = await fetch(path, { ...opts, headers });
  if (res.status !== 401) return res;
  // Try refresh once
  if (!tokens.refresh) return res;
  const rf = await fetch('/api/auth/token/refresh/', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: tokens.refresh })
  });
  if (!rf.ok) return res; // refresh failed
  const data = await rf.json();
  if (data.access) tokens.access = data.access;
  // retry original
  const headers2 = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
  if (tokens.access) headers2['Authorization'] = `Bearer ${tokens.access}`;
  return fetch(path, { ...opts, headers: headers2 });
}

function switchTier(tier) {
  const t1 = qs('#tier-1-facade');
  const t2 = qs('#tier-2-login');
  const t3 = qs('#tier-3-abacus');
  if (tier === 'facade') { show(t1); hide(t2); hide(t3); }
  else if (tier === 'login') { hide(t1); show(t2); hide(t3); }
  else if (tier === 'abacus') { hide(t1); hide(t2); show(t3); }
}

function showFacadePage(page) {
  qsa('[id^="facade-page-"]').forEach((p) => hide(p));
  show(qs(`#facade-page-${page}`));
}

function openModal(contentHtml) {
  const modal = qs('#abacus-modal');
  const content = qs('#modal-content');
  if (content) content.innerHTML = contentHtml || '';
  show(modal);
}
function closeModal() { hide(qs('#abacus-modal')); }

function showMessage(msg, type = 'info') {
  const mc = qs('#message-container');
  if (!mc) return;
  const el = document.createElement('div');
  el.className = `m-2 px-3 py-2 rounded text-sm ${type === 'error' ? 'bg-red-700 text-white' : 'bg-gray-800 text-gray-200'}`;
  el.textContent = msg;
  mc.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

function handleNavigation(page) {
  const area = qs('#abacus-content-area');
  if (!area) return;
  area.innerHTML = `
    <div class="space-y-2">
      <h2 class="text-xl font-bold text-gray-100 capitalize">${page}</h2>
      <p class="text-gray-400">Content for "${page}" goes here.</p>
    </div>`;
}

async function login(username, password) {
  const res = await fetch('/api/auth/token/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Authentication failed');
  }
  const data = await res.json();
  // simplejwt returns access/refresh; backend adds role, username
  tokens.access = data.access || '';
  tokens.refresh = data.refresh || '';
  return data;
}

function logout() { tokens.clear(); }

window.addEventListener('DOMContentLoaded', () => {
  showFacadePage('home');

  // Hidden trigger: click the keyhole dot to reveal login
  const keyhole = qs('#keyhole');
  if (keyhole) keyhole.addEventListener('click', () => switchTier('login'));

  // Login form → authenticate via JWT
  const loginForm = qs('#login-form');
  const loginError = qs('#login-error');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = qs('#username')?.value?.trim();
      const passphrase = qs('#passphrase')?.value?.trim();
      if (!username || !passphrase) {
        if (loginError) { loginError.textContent = 'Please enter username and passphrase.'; show(loginError); }
        return;
      }
      try {
        if (loginError) hide(loginError);
        const data = await login(username, passphrase);
        const r = roleLabel(data.role);
        switchTier('abacus');
        showMessage(`Welcome, ${data.display_name || username} (${r}).`, 'info');
      } catch (err) {
        if (loginError) { loginError.textContent = err.message; show(loginError); }
      }
    });
  }

  // Global click delegation
  document.addEventListener('click', (event) => {
    const target = event.target.closest('[data-action]');
    if (!target) return;
    const action = target.getAttribute('data-action');
    if (!action) return;

    switch (action) {
      case 'navigate-facade': {
        const page = target.getAttribute('data-page') || 'home';
        showFacadePage(page);
        break;
      }
      case 'back-to-facade': {
        switchTier('facade');
        break;
      }
      case 'navigate': {
        const page = target.getAttribute('data-page') || 'dashboard';
        handleNavigation(page);
        break;
      }
      case 'open-notifications': {
        openModal('<div class="text-gray-200">No new notifications.</div>');
        break;
      }
      case 'close-modal': {
        closeModal();
        break;
      }
      case 'logout': {
        logout();
        switchTier('facade');
        closeModal();
        hide(qs('#shutdown-overlay'));
        showMessage('Logged out.');
        break;
      }
      case 'panic': {
        show(qs('#shutdown-overlay'));
        break;
      }
      default: break;
    }
  });

  // Escape to close modal/overlay
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { closeModal(); hide(qs('#shutdown-overlay')); }
  });
});
