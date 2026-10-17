/* ========================================================================
   Databaes Pay — payment screen
   Request/response shapes are specified in ./API.md. Keep the two in sync.
   ===================================================================== */

/* ────────────────────────────────────────────────────────────────────────
   CONFIG
   ──────────────────────────────────────────────────────────────────────── */

/** Where the scoring API lives. Switch API_BASE to API_BASES.local for testing. */
const API_BASES = {
  vm:    'http://148.100.98.249:8000',   // LinuxONE VM
  local: 'http://localhost:8000',        // local backend
};

/** Active base URL. Change this line to point the whole app somewhere else. */
const API_BASE = API_BASES.vm;

/** Start with the fake backend on? Handy before the real API is deployed. */
const MOCK_MODE_DEFAULT = false;

/** Give up on a request after this long (ms) rather than hanging on a dead host. */
const REQUEST_TIMEOUT_MS = 8000;

const CURRENCY = 'GBP';
const CURRENCY_SYMBOL = '£';

/* ────────────────────────────────────────────────────────────────────────
   STATE
   ──────────────────────────────────────────────────────────────────────── */

const state = {
  apiBase: API_BASE,
  mock: MOCK_MODE_DEFAULT,
  /** The payment awaiting a Confirm/Cancel decision, if any. */
  pending: null,
  /** Last submitted form values, so "Try again" can resubmit. */
  lastPayload: null,
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

/* ────────────────────────────────────────────────────────────────────────
   FORMATTING
   ──────────────────────────────────────────────────────────────────────── */

const moneyFmt = new Intl.NumberFormat('en-GB', {
  style: 'currency',
  currency: CURRENCY,
  minimumFractionDigits: 2,
});

function formatMoney(amount, currency) {
  if (typeof amount !== 'number' || !isFinite(amount)) return '—';
  if (currency && currency !== CURRENCY) {
    try {
      return new Intl.NumberFormat('en-GB', {
        style: 'currency', currency, minimumFractionDigits: 2,
      }).format(amount);
    } catch {
      return `${currency} ${amount.toFixed(2)}`;
    }
  }
  return moneyFmt.format(amount);
}

function formatTimestamp(iso) {
  const d = new Date(iso);
  if (isNaN(d)) return iso || '—';
  return d.toLocaleString('en-GB', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  });
}

/** Escape anything that came off the wire before it goes near innerHTML. */
function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

function newClientTxnId() {
  if (crypto.randomUUID) return `c_${crypto.randomUUID()}`;
  return `c_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
}

/* ────────────────────────────────────────────────────────────────────────
   HTTP
   ──────────────────────────────────────────────────────────────────────── */

/** An error we can show the user without leaking stack traces into the UI. */
class ApiError extends Error {
  constructor(message, { kind = 'network', status = null } = {}) {
    super(message);
    this.kind = kind;     // 'network' | 'http' | 'parse'
    this.status = status;
  }
}

async function request(path, { method = 'GET', body } = {}) {
  const url = `${state.apiBase}${path}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  let res;
  try {
    res = await fetch(url, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (err) {
    // fetch only rejects for transport-level problems: DNS, refused
    // connection, CORS rejection, or our own abort.
    const timedOut = err.name === 'AbortError';
    throw new ApiError(
      timedOut
        ? `No response within ${REQUEST_TIMEOUT_MS / 1000}s.`
        : 'The request could not be completed. The service may be down, or CORS may not be enabled on it.',
      { kind: 'network' },
    );
  } finally {
    clearTimeout(timer);
  }

  const raw = await res.text();
  let parsed = null;
  if (raw) {
    try {
      parsed = JSON.parse(raw);
    } catch {
      if (res.ok) throw new ApiError('The service replied with something that is not JSON.', { kind: 'parse' });
    }
  }

  if (!res.ok) {
    const msg = parsed?.error?.message || `The service returned HTTP ${res.status}.`;
    throw new ApiError(msg, { kind: 'http', status: res.status });
  }

  return parsed ?? {};
}

/* ────────────────────────────────────────────────────────────────────────
   MOCK BACKEND
   Fakes /score, /score/confirm and /audit so the UI can be built and
   demoed before the real API exists. Rules are deliberately simple and
   predictable: new payee + big amount is what trips it.
   ──────────────────────────────────────────────────────────────────────── */

const mockDb = {
  seq: 1,
  entries: [
    {
      txn_id: 'txn_mock_seed_2',
      timestamp: new Date(Date.now() - 36e5 * 5).toISOString(),
      amount: 42.8, currency: CURRENCY, payee: 'Northern Rail', new_payee: false,
      decision: 'allow', risk_score: 0.06, reasons: [], outcome: 'sent',
    },
    {
      txn_id: 'txn_mock_seed_1',
      timestamp: new Date(Date.now() - 36e5 * 29).toISOString(),
      amount: 3200, currency: CURRENCY, payee: 'QuickCash Transfers', new_payee: true,
      decision: 'review', risk_score: 0.91,
      reasons: [
        { code: 'NEW_PAYEE_HIGH_VALUE', message: 'First payment to this payee, and it is above your usual amount.', severity: 'high' },
        { code: 'PAYEE_NAME_RISK', message: 'This payee name resembles accounts reported in recent scam cases.', severity: 'high' },
      ],
      outcome: 'cancelled',
    },
  ],
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function mockScore(payload) {
  const reasons = [];
  const { amount, payee, new_payee: isNew } = payload;

  if (isNew && amount >= 1000) {
    reasons.push({
      code: 'NEW_PAYEE_HIGH_VALUE',
      message: 'First payment to this payee, and it is above your usual amount.',
      severity: 'high',
    });
  } else if (isNew) {
    reasons.push({
      code: 'NEW_PAYEE',
      message: 'You have not paid this payee before.',
      severity: 'medium',
    });
  }

  if (amount >= 5000) {
    reasons.push({
      code: 'AMOUNT_OUTLIER',
      message: 'This is far larger than your typical payment over the last 90 days.',
      severity: 'high',
    });
  }

  if (/\b(crypto|cash|invest|wallet|prize|refund)\b/i.test(payee || '')) {
    reasons.push({
      code: 'PAYEE_NAME_RISK',
      message: 'This payee name resembles accounts reported in recent scam cases.',
      severity: 'high',
    });
  }

  if (new Date().getHours() >= 23 || new Date().getHours() < 5) {
    reasons.push({
      code: 'UNUSUAL_HOUR',
      message: 'Payments at this hour are unusual for your account.',
      severity: 'low',
    });
  }

  const weights = { high: 0.42, medium: 0.2, low: 0.08 };
  const score = Math.min(0.97, reasons.reduce((sum, r) => sum + weights[r.severity], 0.04));
  const flagged = reasons.some((r) => r.severity === 'high') || score >= 0.5;

  const entry = {
    txn_id: `txn_mock_${String(mockDb.seq++).padStart(4, '0')}`,
    timestamp: new Date().toISOString(),
    amount, currency: payload.currency, payee, new_payee: isNew,
    decision: flagged ? 'review' : 'allow',
    risk_score: Number(score.toFixed(2)),
    reasons: flagged ? reasons : [],
    outcome: flagged ? 'pending' : 'sent',
  };
  mockDb.entries.unshift(entry);

  return {
    txn_id: entry.txn_id,
    decision: entry.decision,
    risk_score: entry.risk_score,
    reasons: entry.reasons,
    scored_at: entry.timestamp,
  };
}

function mockConfirm({ txn_id, action }) {
  const entry = mockDb.entries.find((e) => e.txn_id === txn_id);
  const status = action === 'confirm' ? 'sent' : 'cancelled';
  if (entry) entry.outcome = status;
  return { txn_id, status, recorded_at: new Date().toISOString() };
}

/* ────────────────────────────────────────────────────────────────────────
   API LAYER — routes to the real backend or the mock
   ──────────────────────────────────────────────────────────────────────── */

const api = {
  async score(payload) {
    if (state.mock) { await sleep(700); return mockScore(payload); }
    return request('/score', { method: 'POST', body: payload });
  },

  async confirm(txnId, action) {
    if (state.mock) { await sleep(500); return mockConfirm({ txn_id: txnId, action }); }
    return request('/score/confirm', { method: 'POST', body: { txn_id: txnId, action } });
  },

  async audit() {
    if (state.mock) { await sleep(500); return { entries: mockDb.entries.slice() }; }
    return request('/audit');
  },
};

/* ────────────────────────────────────────────────────────────────────────
   VIEW SWITCHING
   ──────────────────────────────────────────────────────────────────────── */

function setView(name) {
  $$('.view').forEach((v) => v.classList.toggle('is-active', v.id === `view-${name}`));
  $$('.tab').forEach((t) => {
    const on = t.dataset.view === name;
    t.classList.toggle('is-active', on);
    if (on) t.setAttribute('aria-current', 'page');
    else t.removeAttribute('aria-current');
  });
  if (name === 'audit') loadAudit();
}

/** Show exactly one pane of the pay view. */
function setPane(id) {
  ['pane-form', 'pane-sent', 'pane-paused', 'pane-cancelled', 'pane-error']
    .forEach((p) => { $(`#${p}`).hidden = p !== id; });
}

function setBusy(btn, busy) {
  btn.classList.toggle('is-busy', busy);
  btn.disabled = busy;
}

/* ────────────────────────────────────────────────────────────────────────
   FORM VALIDATION
   ──────────────────────────────────────────────────────────────────────── */

function showFieldError(inputId, message) {
  const input = $(`#${inputId}`);
  const slot = $(`#${inputId}-error`);
  input.classList.toggle('has-error', Boolean(message));
  slot.textContent = message || '';
  slot.hidden = !message;
}

/** Returns a /score payload, or null if the form is not valid. */
function readForm() {
  const rawAmount = $('#amount').value.trim().replace(/[,\s£]/g, '');
  const payee = $('#payee').value.trim();
  let ok = true;

  showFieldError('amount', '');
  showFieldError('payee', '');

  const amount = Number(rawAmount);
  if (!rawAmount) {
    showFieldError('amount', 'Enter an amount.');
    ok = false;
  } else if (!isFinite(amount) || amount <= 0) {
    showFieldError('amount', 'Enter an amount greater than zero.');
    ok = false;
  } else if (!/^\d+(\.\d{1,2})?$/.test(rawAmount)) {
    showFieldError('amount', 'Use at most two decimal places.');
    ok = false;
  }

  if (!payee) {
    showFieldError('payee', 'Enter who you are paying.');
    ok = false;
  }

  if (!ok) return null;

  return {
    client_txn_id: newClientTxnId(),
    amount: Number(amount.toFixed(2)),
    currency: CURRENCY,
    payee,
    new_payee: $('#new-payee').checked,
  };
}

/* ────────────────────────────────────────────────────────────────────────
   RENDERING
   ──────────────────────────────────────────────────────────────────────── */

function renderReceipt(el, payload) {
  el.innerHTML = `
    <dt>Amount</dt><dd>${esc(formatMoney(payload.amount, payload.currency))}</dd>
    <dt>Payee</dt><dd>${esc(payload.payee)}</dd>
    <dt>New payee</dt><dd>${payload.new_payee ? 'Yes' : 'No'}</dd>
  `;
}

function renderSent(payload) {
  $('#sent-summary').textContent =
    `${formatMoney(payload.amount, payload.currency)} is on its way to ${payload.payee}.`;
  renderReceipt($('#sent-receipt'), payload);
  setPane('pane-sent');
}

function renderPaused(payload, result) {
  renderReceipt($('#paused-receipt'), payload);

  const pct = Math.round((Number(result.risk_score) || 0) * 100);
  $('#risk-fill').style.width = `${pct}%`;
  $('#risk-value').textContent = `${pct}%`;

  const reasons = Array.isArray(result.reasons) ? result.reasons : [];
  const list = $('#reasons-list');

  if (reasons.length === 0) {
    // The contract requires reasons for a review, but never show a blank list.
    list.innerHTML = `<li><span class="sev sev-medium">flagged</span>
      <span class="reason-text"><span class="reason-msg">This payment was held for review.
      The service did not give a specific reason.</span></span></li>`;
  } else {
    list.innerHTML = reasons.map((r) => {
      const sev = ['high', 'medium', 'low'].includes(r.severity) ? r.severity : 'medium';
      return `<li>
        <span class="sev sev-${sev}">${esc(sev)}</span>
        <span class="reason-text">
          <span class="reason-msg">${esc(r.message || 'Flagged by the risk model.')}</span>
          ${r.code ? `<span class="reason-code">${esc(r.code)}</span>` : ''}
        </span>
      </li>`;
    }).join('');
  }

  setPane('pane-paused');
}

function renderError(err) {
  const httpish = err instanceof ApiError && err.kind !== 'network';
  $('#error-title').textContent = httpish
    ? 'The scoring service rejected that'
    : "Can't reach the scoring service";
  $('#error-detail').textContent = err.message;
  $('#error-base').textContent = state.apiBase;
  setPane('pane-error');
}

function renderAudit(entries) {
  const body = $('#audit-body');

  if (!entries.length) {
    body.innerHTML = '<p class="audit-placeholder">No payments scored yet.</p>';
    return;
  }

  body.innerHTML = `<div class="audit-list">${entries.map((e) => {
    const outcome = ['sent', 'cancelled', 'pending'].includes(e.outcome) ? e.outcome : 'pending';
    const decision = e.decision === 'allow' ? 'allow' : 'review';
    const reasons = Array.isArray(e.reasons) ? e.reasons : [];

    return `<article class="audit-row">
      <div class="audit-top">
        <span class="audit-payee">${esc(e.payee || 'Unknown payee')}</span>
        <span class="audit-amount">${esc(formatMoney(e.amount, e.currency))}</span>
      </div>
      <div class="audit-meta">
        <span class="badge badge-${outcome}">${esc(outcome)}</span>
        <span class="badge badge-${decision}">${decision === 'allow' ? 'low risk' : 'flagged'}</span>
        <span class="audit-dot">·</span>
        <time datetime="${esc(e.timestamp)}">${esc(formatTimestamp(e.timestamp))}</time>
        ${typeof e.risk_score === 'number'
          ? `<span class="audit-dot">·</span><span>score ${Math.round(e.risk_score * 100)}%</span>` : ''}
        ${e.new_payee ? '<span class="audit-dot">·</span><span>new payee</span>' : ''}
      </div>
      ${reasons.length ? `<ul class="audit-reasons">${
        reasons.map((r) => `<li><span>${esc(r.message || r.code || '')}</span></li>`).join('')
      }</ul>` : ''}
    </article>`;
  }).join('')}</div>`;
}

function renderAuditError(err) {
  $('#audit-body').innerHTML = `
    <div class="audit-error">
      <p><strong>Could not load the audit log</strong>${esc(err.message)}</p>
      <button class="btn btn-quiet btn-sm" data-action="audit-retry" type="button">Try again</button>
    </div>`;
}

/* ────────────────────────────────────────────────────────────────────────
   FLOWS
   ──────────────────────────────────────────────────────────────────────── */

async function submitPayment(payload, btn) {
  state.lastPayload = payload;
  setBusy(btn, true);

  try {
    const result = await api.score(payload);

    if (result.decision === 'review') {
      state.pending = { txnId: result.txn_id, payload };
      renderPaused(payload, result);
    } else {
      // Anything that is not an explicit review is treated as cleared.
      state.pending = null;
      renderSent(payload);
    }
    setApiStatus(state.mock ? 'mock' : 'up');
  } catch (err) {
    renderError(err);
    if (!state.mock) setApiStatus('down');
  } finally {
    setBusy(btn, false);
  }
}

async function resolvePending(action, btn) {
  if (!state.pending) return;
  const { txnId, payload } = state.pending;
  setBusy(btn, true);

  try {
    const result = await api.confirm(txnId, action);
    state.pending = null;
    if (result.status === 'cancelled' || action === 'cancel') setPane('pane-cancelled');
    else renderSent(payload);
  } catch (err) {
    renderError(err);
    if (!state.mock) setApiStatus('down');
  } finally {
    setBusy(btn, false);
  }
}

async function loadAudit() {
  const btn = $('#audit-refresh');
  setBusy(btn, true);
  $('#audit-body').innerHTML = '<p class="audit-placeholder">Loading…</p>';

  try {
    const data = await api.audit();
    const entries = Array.isArray(data?.entries) ? data.entries : [];
    renderAudit(entries);
    setApiStatus(state.mock ? 'mock' : 'up');
  } catch (err) {
    renderAuditError(err);
    if (!state.mock) setApiStatus('down');
  } finally {
    setBusy(btn, false);
  }
}

function resetForm() {
  state.pending = null;
  $('#payment-form').reset();
  showFieldError('amount', '');
  showFieldError('payee', '');
  setPane('pane-form');
  $('#amount').focus();
}

/* ────────────────────────────────────────────────────────────────────────
   DEV BAR
   ──────────────────────────────────────────────────────────────────────── */

function setApiStatus(stateName) {
  const labels = {
    mock: 'mock mode', up: 'connected', down: 'unreachable',
    probing: 'checking…', unknown: 'not checked',
  };
  const el = $('#api-status');
  el.dataset.state = stateName;
  $('#api-status-text').textContent = labels[stateName] || stateName;
}

/** Light touch of the API so the footer can show whether it is reachable. */
async function probeApi() {
  if (state.mock) { setApiStatus('mock'); return; }
  setApiStatus('probing');
  try {
    await api.audit();
    setApiStatus('up');
  } catch {
    setApiStatus('down');
  }
}

function buildApiSelect() {
  const sel = $('#api-base');
  sel.innerHTML = Object.entries(API_BASES)
    .map(([key, url]) => `<option value="${esc(url)}">${esc(key)} — ${esc(url)}</option>`)
    .join('');
  sel.value = state.apiBase;
}

/* ────────────────────────────────────────────────────────────────────────
   WIRING
   ──────────────────────────────────────────────────────────────────────── */

function init() {
  buildApiSelect();
  $('#mock-mode').checked = state.mock;
  $('#api-base').disabled = state.mock;

  $$('.tab').forEach((tab) => {
    tab.addEventListener('click', () => setView(tab.dataset.view));
  });

  $('#payment-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const payload = readForm();
    if (payload) submitPayment(payload, $('#submit-btn'));
  });

  // Pane buttons are static, so one delegated listener covers all of them.
  $('#view-pay').addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    switch (btn.dataset.action) {
      case 'reset':   resetForm(); break;
      case 'confirm': resolvePending('confirm', btn); break;
      case 'cancel':  resolvePending('cancel', btn); break;
      case 'retry':
        if (state.pending) resolvePending('confirm', btn);
        else if (state.lastPayload) submitPayment(state.lastPayload, btn);
        else resetForm();
        break;
    }
  });

  $('#view-audit').addEventListener('click', (e) => {
    if (e.target.closest('[data-action="audit-retry"]')) loadAudit();
  });

  $('#audit-refresh').addEventListener('click', loadAudit);

  $('#mock-mode').addEventListener('change', (e) => {
    state.mock = e.target.checked;
    $('#api-base').disabled = state.mock;
    setApiStatus(state.mock ? 'mock' : 'unknown');
    if ($('#view-audit').classList.contains('is-active')) loadAudit();
    else if (!state.mock) probeApi();
  });

  $('#api-base').addEventListener('change', (e) => {
    state.apiBase = e.target.value;
    probeApi();
  });

  setPane('pane-form');
  probeApi();
}

document.addEventListener('DOMContentLoaded', init);
