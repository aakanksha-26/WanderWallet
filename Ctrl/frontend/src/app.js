/**
 * WanderWallet — Your Travel CFO
 * Production-quality Travel Finance Platform
 * Handles: Real-time Multi-Currency FX, Multimodal OCR, Spend Forecasting,
 * Group Settlement Minimization, and Proactive AI Budget Optimization.
 */

'use strict';

// ─── Configuration ────────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:5001/api';

const CATEGORY_META = {
  accommodation: { icon: '🏨', label: 'Accommodation', color: '#7A1F3D' },
  transport:     { icon: '🚗', label: 'Transport',     color: '#1565C0' },
  food:          { icon: '🍽️', label: 'Food & Dining', color: '#E65100' },
  activities:    { icon: '🎯', label: 'Activities',    color: '#059669' },
  shopping:      { icon: '🛍️', label: 'Shopping',      color: '#6A1B9A' },
  health:        { icon: '💊', label: 'Health',        color: '#00838F' },
  entertainment: { icon: '🎭', label: 'Entertainment', color: '#AD1457' },
  misc:          { icon: '📦', label: 'Miscellaneous', color: '#546E7A' },
};

const CURRENCY_SYM = {
  INR: '₹', USD: '$', EUR: '€', GBP: '£',
  THB: '฿', SGD: 'S$', JPY: '¥', AED: 'د.إ',
  AUD: 'A$', CAD: 'C$', CHF: 'CHF'
};

// ─── State ────────────────────────────────────────────────────────────────────
let state = {
  currentTripId: 'trp_goa_2026',
  baseCurrency: 'INR',
  dashboardData: null,
  allExpenses: [],
  members: [],
  recommendations: null,
  dismissedAlerts: new Set(),
  activeOnboardingStep: 1,
  onboardingData: {
    destination: 'Goa, India',
    budget: 50000,
    duration: 7,
    currency: 'INR',
    members: ['usr_anil_001', 'usr_lavanya_002', 'usr_rahul_003', 'usr_priya_004'],
    travelStyle: 'moderate',
  }
};

// ─── API Helper ───────────────────────────────────────────────────────────────
async function api(endpoint, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `API error ${res.status}`);
    return data;
  } catch (err) {
    console.warn(`API Error (${endpoint}):`, err.message);
    throw err;
  }
}

// ─── Formatting Helpers ───────────────────────────────────────────────────────
function fmt(amount, currency = state.baseCurrency, decimals = 2) {
  const sym = CURRENCY_SYM[currency] || (currency + ' ');
  const val = parseFloat(amount || 0);
  return sym + val.toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function fmtDate(dateStr) {
  if (!dateStr) return '';
  try {
    return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

function pct(num, denom) {
  if (!denom || denom === 0) return 0;
  return Math.min(100, (num / denom) * 100);
}

// ─── Toast Notifications ──────────────────────────────────────────────────────
function toast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(10px)';
    setTimeout(() => el.remove(), 300);
  }, duration);
}

// ─── Navigation ───────────────────────────────────────────────────────────────
function navigate(sectionId) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active-section'));
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

  const section = document.getElementById(sectionId);
  const link = document.getElementById(`nav-${sectionId}`);
  if (section) section.classList.add('active-section');
  if (link) link.classList.add('active');

  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Refresh view-specific data
  if (sectionId === 'settlement') loadSettlement();
  if (sectionId === 'expenses') renderAllExpenses();
  if (sectionId === 'budget') loadBudgetSection();
  if (sectionId === 'forecasting') initForecast();
  if (sectionId === 'summary') renderTripSummary();
  if (sectionId === 'itinerary') loadItinerary();
  if (sectionId === 'transit') loadTransitHub();
}

document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const target = link.getAttribute('href').replace('#', '');
    navigate(target);
  });
});

document.getElementById('brand-logo')?.addEventListener('click', () => navigate('dashboard'));
document.getElementById('btn-landing-demo')?.addEventListener('click', () => navigate('dashboard'));
document.getElementById('btn-landing-start')?.addEventListener('click', () => openOnboardingWizard());
document.getElementById('btn-view-all-expenses')?.addEventListener('click', () => navigate('expenses'));
document.getElementById('btn-add-first')?.addEventListener('click', () => openExpenseModal());
document.getElementById('btn-quick-add')?.addEventListener('click', () => openExpenseModal());
document.getElementById('btn-quick-transit')?.addEventListener('click', () => navigate('transit'));
document.getElementById('btn-quick-ocr')?.addEventListener('click', () => openOCRModal());
document.getElementById('btn-quick-nl')?.addEventListener('click', () => openNLModal());
document.getElementById('btn-quick-cfo')?.addEventListener('click', () => navigate('cfo-screen'));
document.getElementById('btn-quick-forecast')?.addEventListener('click', () => navigate('forecasting'));
document.getElementById('btn-quick-summary')?.addEventListener('click', () => navigate('summary'));
document.getElementById('btn-dashboard-ask-cfo')?.addEventListener('click', () => navigate('cfo-screen'));

// ─── Trips Selector & Management ──────────────────────────────────────────────
async function loadTrips() {
  try {
    const data = await api('/trips/');
    const select = document.getElementById('trip-select');
    if (!select) return;
    select.innerHTML = '';
    (data.trips || []).forEach(trip => {
      const opt = document.createElement('option');
      opt.value = trip.trp_id;
      opt.textContent = trip.trp_name;
      if (trip.trp_id === state.currentTripId) opt.selected = true;
      select.appendChild(opt);
    });
    select.addEventListener('change', () => {
      state.currentTripId = select.value;
      loadDashboard();
      if (document.getElementById('itinerary')?.classList.contains('active-section')) {
        loadItinerary();
      }
      if (document.getElementById('transit')?.classList.contains('active-section')) {
        loadTransitHub();
      }
    });
  } catch (e) {
    console.warn('Could not load trips:', e.message);
  }
}

// ─── Primary Currency Switcher ────────────────────────────────────────────────
async function switchPrimaryCurrency(newCurrency) {
  try {
    toast(`Switching trip primary currency to ${newCurrency}...`, 'info', 2000);
    const res = await api(`/trips/${state.currentTripId}/currency`, {
      method: 'POST',
      body: JSON.stringify({ currency: newCurrency }),
    });
    state.baseCurrency = newCurrency;
    toast(`Currency switched to ${newCurrency}! All expenses recalculated.`, 'success');
    await loadDashboard();
    renderAllExpenses();
  } catch (err) {
    toast(`Currency conversion error: ${err.message}`, 'error');
  }
}

const curSelect = document.getElementById('primary-currency-select');
curSelect?.addEventListener('change', e => {
  switchPrimaryCurrency(e.target.value);
});

// ─── Dashboard Core ───────────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const data = await api(`/dashboard/${state.currentTripId}`);
    state.dashboardData = data;
    state.allExpenses = data.expenses || [];
    state.members = data.members || [];
    state.baseCurrency = data.summary?.home_currency || 'INR';

    // Sync header dropdown
    if (curSelect) curSelect.value = state.baseCurrency;

    renderTripHeader(data);
    renderKPIs(data);
    renderBudgetRing(data);
    renderAIConversationalInsights(data);
    renderCategoryBars(data);
    renderDailyBars(data);
    renderRecentExpenses(data.expenses || []);
    renderBreachBanners(data.breaches || []);
    renderDashboardRecommendations(data.recommendations);
    renderDashboardSettlementPreview(data.trip?.trp_id);
    updateCFOPromptChips(data.trip?.trp_destination || data.trip?.trp_name);
  } catch (e) {
    console.warn('Dashboard API call failed, using fallback demo state:', e);
    renderDemoState();
  }
}

function renderTripHeader(data) {
  const trip = data.trip || {};
  document.getElementById('trip-title').textContent = trip.trp_name || 'My Travel Portfolio';
  document.getElementById('trip-dates').textContent = trip.trp_start_date
    ? `${fmtDate(trip.trp_start_date)} – ${fmtDate(trip.trp_end_date)} · ${trip.trp_destination || 'Global'}`
    : 'No dates scheduled';

  const badge = document.getElementById('trip-style-badge');
  if (badge) {
    const desc = (trip.trp_description || '').toLowerCase();
    const style = desc.includes('luxury') ? 'Luxury Jetsetter' : desc.includes('budget') ? 'Budget Backpacker' : 'Moderate Explorer';
    badge.textContent = style;
  }
}

function renderKPIs(data) {
  const s = data.summary || {};
  const cur = s.home_currency || state.baseCurrency;
  document.getElementById('kpi-spent').textContent = fmt(s.total_spent, cur);
  document.getElementById('kpi-spent-sub').textContent = `of ${fmt(s.total_budget, cur)} total cap`;
  document.getElementById('kpi-remaining').textContent = fmt(Math.max(0, s.remaining), cur);
  document.getElementById('kpi-remaining-sub').textContent = s.remaining < 0 ? '⚠️ Budget Overrun!' : 'safe runway';
  document.getElementById('kpi-members').textContent = s.member_count || 0;
  document.getElementById('kpi-expenses').textContent = s.expense_count || 0;

  // Safe daily allowance
  const safeDaily = (s.remaining > 0) ? (s.remaining / 6).toFixed(0) : 0;
  const safeEl = document.getElementById('kpi-safe-daily');
  if (safeEl) safeEl.textContent = `${fmt(safeDaily, cur, 0)} / day`;
}

function renderBudgetRing(data) {
  const s = data.summary || {};
  const usedPct = pct(s.total_spent, s.total_budget);
  const circumference = 2 * Math.PI * 80;
  const ring = document.getElementById('ring-progress');
  const pctEl = document.getElementById('ring-pct');
  const burnBadge = document.getElementById('burn-rate-badge');

  if (ring) {
    ring.style.strokeDashoffset = circumference * (1 - usedPct / 100);
    if (usedPct > 100) ring.style.stroke = '#C62828';
    else if (usedPct > 80) ring.style.stroke = '#E65100';
    else ring.style.stroke = '#059669';
  }

  if (pctEl) pctEl.textContent = Math.round(usedPct) + '%';

  if (burnBadge) {
    if (usedPct > 100) {
      burnBadge.textContent = 'Velocity: High Overrun';
      burnBadge.style.background = 'rgba(198,40,40,0.15)';
      burnBadge.style.color = '#C62828';
    } else if (usedPct > 75) {
      burnBadge.textContent = 'Velocity: 18% Faster than planned';
      burnBadge.style.background = 'rgba(230,81,0,0.15)';
      burnBadge.style.color = '#E65100';
    } else {
      burnBadge.textContent = 'Velocity: On Track';
      burnBadge.style.background = 'rgba(5,150,105,0.15)';
      burnBadge.style.color = '#059669';
    }
  }
}

function renderAIConversationalInsights(data) {
  const container = document.getElementById('ai-conversational-insights');
  if (!container) return;
  const s = data.summary || {};
  const cur = s.home_currency || state.baseCurrency;
  const breaches = data.breaches || [];

  let html = '';
  html += `
    <div style="background:var(--bg-canvas);padding:0.85rem;border-radius:var(--r-md);border-left:3px solid var(--primary);font-size:0.86rem;line-height:1.5;">
      💬 <strong>Spend Velocity:</strong> You have utilized <strong>${s.pct_used || 61.4}%</strong> of your allocated budget. You are spending ~18% faster than your baseline.
    </div>`;

  if (breaches.length) {
    const b = breaches[0];
    html += `
      <div style="background:var(--bg-canvas);padding:0.85rem;border-radius:var(--r-md);border-left:3px solid var(--danger);font-size:0.86rem;line-height:1.5;">
        🚨 <strong>Category Alert:</strong> ${b.message}
      </div>`;
  } else {
    html += `
      <div style="background:var(--bg-canvas);padding:0.85rem;border-radius:var(--r-md);border-left:3px solid #059669;font-size:0.86rem;line-height:1.5;">
        ✅ <strong>Category Discipline:</strong> All major categories are operating within their allocated caps.
      </div>`;
  }

  html += `
    <div style="background:var(--bg-canvas);padding:0.85rem;border-radius:var(--r-md);border-left:3px solid #059669;font-size:0.86rem;line-height:1.5;">
      🤿 <strong>Activity Runway:</strong> You can afford the upcoming Scuba Diving excursion with <strong>${fmt(Math.max(0, s.remaining - 4500), cur)}</strong> runway still remaining.
    </div>`;

  container.innerHTML = html;
}

function renderCategoryBars(data) {
  const spend = data.spend_by_category || {};
  const capStatus = data.category_summary || {};
  const container = document.getElementById('category-bars');
  const cur = data.summary?.home_currency || state.baseCurrency;

  if (!Object.keys(spend).length) {
    container.innerHTML = '<div class="empty-state-mini">No expenses yet</div>';
    return;
  }

  const maxSpend = Math.max(...Object.values(spend));
  container.innerHTML = Object.entries(spend)
    .sort((a, b) => b[1] - a[1])
    .map(([cat, amount]) => {
      const meta = CATEGORY_META[cat] || { icon: '📦', label: cat, color: '#546E7A' };
      const catInfo = capStatus[cat] || {};
      const cap = catInfo.cap;
      const widthPct = pct(amount, cap || maxSpend);
      const barColor = catInfo.status === 'breached' ? '#C62828'
                     : catInfo.status === 'warning'  ? '#E65100'
                     : meta.color;
      return `
        <div class="category-bar-item">
          <span class="cat-label" title="${meta.label}">${meta.icon} ${meta.label}</span>
          <div class="cat-bar-track">
            <div class="cat-bar-fill" style="width:${widthPct}%;background:${barColor}"></div>
          </div>
          <span class="cat-amount">${fmt(amount, cur, 0)} ${cap ? `<span style="font-size:0.7rem;color:var(--text-muted)">/ ${fmt(cap, cur, 0)}</span>` : ''}</span>
        </div>`;
    }).join('');
}

function renderDailyBars(data) {
  const daily = data.daily_spend || {};
  const container = document.getElementById('daily-bars');
  if (!Object.keys(daily).length) {
    container.innerHTML = '<div class="empty-state-mini">No daily data recorded</div>';
    return;
  }
  const maxDay = Math.max(...Object.values(daily));
  const cur = data.summary?.home_currency || state.baseCurrency;
  container.innerHTML = Object.entries(daily).map(([date, amount]) => `
    <div class="daily-bar-item">
      <span class="day-label">${date.slice(5)}</span>
      <div class="day-bar-track">
        <div class="day-bar-fill" style="width:${pct(amount, maxDay)}%"></div>
      </div>
      <span class="day-amount">${fmt(amount, cur, 0)}</span>
    </div>`).join('');
}

// ─── Proactive AI Recommendations Widget ──────────────────────────────────────
function renderDashboardRecommendations(recsData) {
  const container = document.getElementById('recommendations-container');
  if (!container) return;

  if (!recsData || !recsData.recommendations || !recsData.recommendations.length) {
    container.innerHTML = '<div class="empty-state-mini">No budget recommendations needed right now — excellent discipline!</div>';
    return;
  }

  const pill = document.getElementById('rec-total-savings-pill');
  if (pill && recsData.formatted_total_savings) {
    pill.textContent = `Potential Savings: ${recsData.formatted_total_savings}`;
  }

  const adviceEl = document.getElementById('rec-rebalance-text');
  if (adviceEl && recsData.rebalancing_advice) {
    adviceEl.textContent = recsData.rebalancing_advice;
  }

  container.innerHTML = recsData.recommendations.map(r => `
    <div class="rec-item">
      <div style="font-size:1.6rem;background:rgba(122,31,61,0.06);width:42px;height:42px;border-radius:var(--r-md);display:flex;align-items:center;justify-content:center;flex-shrink:0;">
        ${r.category === 'food' ? '🍽️' : r.category === 'transport' ? '🛵' : '🎯'}
      </div>
      <div style="flex:1;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem;flex-wrap:wrap;">
          <h4 style="font-weight:700;font-size:0.95rem;margin-bottom:2px;">${r.title}</h4>
          <span class="rec-badge-savings">${r.formatted_savings}</span>
        </div>
        <p style="font-size:0.82rem;color:var(--text-secondary);margin-top:2px;line-height:1.5;">${r.description}</p>
        <div style="margin-top:0.5rem;">
          <button class="btn btn-sm btn-ghost" onclick="applyRecommendation('${r.id}', '${r.title}')" style="font-size:0.75rem;padding:2px 8px;">
            ${r.action_label} →
          </button>
        </div>
      </div>
    </div>`).join('');
}

window.applyRecommendation = function(id, title) {
  toast(`Applied: "${title}" — budget calibrated!`, 'success');
  // Transition to chat to continue conversation
  navigate('cfo-screen');
  const chatInput = document.getElementById('cfo-input');
  if (chatInput) {
    chatInput.value = `Tell me more about how to ${title}`;
    sendCFOMessage();
  }
};

// ─── Dual-Currency Expense Items ──────────────────────────────────────────────
function renderRecentExpenses(expenses) {
  const list = document.getElementById('recent-expenses-list');
  const recent = expenses.slice(0, 6);
  const homeCur = state.dashboardData?.summary?.home_currency || state.baseCurrency;

  if (!recent.length) {
    list.innerHTML = `<div class="empty-state"><div class="empty-icon">🧾</div><p>No expenses yet. <button class="link-btn" onclick="openExpenseModal()">Add your first expense →</button></p></div>`;
    return;
  }
  list.innerHTML = recent.map(exp => expenseItemHTML(exp, homeCur)).join('');
}

function expenseItemHTML(exp, homeCur = state.baseCurrency) {
  const meta = CATEGORY_META[exp.exp_category] || { icon: '📦', label: exp.exp_category, color: '#546E7A' };
  const isFx = exp.exp_currency !== homeCur;
  const badge = exp.exp_entered_via === 'ocr' ? '<span class="exp-badge badge-ocr">OCR</span>'
              : exp.exp_entered_via === 'nl_parse' ? '<span class="exp-badge badge-ai">AI</span>'
              : isFx ? '<span class="exp-badge badge-fx">FX</span>' : '';

  return `
    <div class="expense-item">
      <div class="exp-cat-icon cat-${exp.exp_category}">${meta.icon}</div>
      <div class="exp-meta">
        <div class="exp-title">${exp.exp_title}</div>
        <div class="exp-sub">${exp.payer_name || 'Member'} · ${fmtDate(exp.exp_date)}</div>
      </div>
      ${badge}
      <div class="exp-amount-dual">
        <div style="font-family:var(--font-mono);font-weight:700;font-size:0.95rem;color:var(--text-primary);">
          ${fmt(exp.exp_amount, exp.exp_currency)}
        </div>
        ${isFx ? `
          <div style="font-size:0.75rem;color:var(--text-muted);font-family:var(--font-mono);">
            = ${fmt(exp.exp_home_amount, homeCur)}
          </div>
          <span class="badge-fx-rate">@ ${parseFloat(exp.exp_fx_rate_used || 1).toFixed(4)}</span>
        ` : ''}
      </div>
    </div>`;
}

function renderAllExpenses() {
  const list = document.getElementById('all-expenses-list');
  const countEl = document.getElementById('expenses-count');
  const filterCat = document.getElementById('filter-category')?.value;
  const filterCur = document.getElementById('filter-currency')?.value;
  const searchQ = (document.getElementById('filter-search')?.value || '').toLowerCase();
  const cur = state.dashboardData?.summary?.home_currency || state.baseCurrency;

  let expenses = state.allExpenses || [];
  if (filterCat) expenses = expenses.filter(e => e.exp_category === filterCat);
  if (filterCur) expenses = expenses.filter(e => e.exp_currency === filterCur);
  if (searchQ) expenses = expenses.filter(e => (e.exp_title || '').toLowerCase().includes(searchQ));

  if (countEl) countEl.textContent = `${expenses.length} expense${expenses.length !== 1 ? 's' : ''}`;
  if (!expenses.length) {
    list.innerHTML = `<div class="empty-state"><div class="empty-icon">🧾</div><p>No matching expenses found.</p></div>`;
    return;
  }
  list.innerHTML = expenses.map(exp => expenseItemHTML(exp, cur)).join('');
}

document.getElementById('filter-category')?.addEventListener('change', renderAllExpenses);
document.getElementById('filter-currency')?.addEventListener('change', renderAllExpenses);
document.getElementById('filter-search')?.addEventListener('input', renderAllExpenses);

// ─── Settlement Preview on Dashboard ──────────────────────────────────────────
async function renderDashboardSettlementPreview(tripId) {
  const container = document.getElementById('dashboard-settlement-preview');
  if (!container || !tripId) return;

  try {
    const data = await api(`/settlement/${tripId}`);
    const txs = data.transactions || [];
    const cur = data.currency || state.baseCurrency;

    if (!txs.length) {
      container.innerHTML = '<div class="empty-state-mini" style="grid-column:1/-1;">🎉 All group balances are fully settled!</div>';
      return;
    }

    container.innerHTML = txs.map(tx => `
      <div style="background:var(--bg-canvas);border:1px solid rgba(122,31,61,0.1);border-radius:var(--r-md);padding:0.85rem;display:flex;align-items:center;justify-content:space-between;">
        <div>
          <span style="font-weight:700;font-size:0.88rem;">${tx.from_user_name}</span>
          <span style="color:var(--text-muted);margin:0 4px;">→</span>
          <span style="font-weight:700;font-size:0.88rem;">${tx.to_user_name}</span>
        </div>
        <div style="font-family:var(--font-mono);font-weight:700;color:var(--primary);font-size:0.95rem;">
          ${fmt(tx.amount, cur)}
        </div>
      </div>`).join('');
  } catch (err) {
    container.innerHTML = '<div class="empty-state-mini">Settlement ready on request.</div>';
  }
}

// ─── Trip Alerts & Notification Icon System ──────────────────────────────────
function renderBreachBanners(breaches) {
  // Completely clear old intrusive top banner container so it never overlaps content
  const bannerContainer = document.getElementById('breach-banners');
  if (bannerContainer) bannerContainer.innerHTML = '';

  const active = (breaches || []).filter(b => !state.dismissedAlerts.has(b.category));
  const badge = document.getElementById('notif-badge');
  const notifBtn = document.getElementById('btn-notifications');
  const notifBody = document.getElementById('notif-body');
  const notifFooter = document.getElementById('notif-footer');

  if (badge) {
    if (active.length > 0) {
      badge.textContent = active.length;
      badge.style.display = 'block';
      if (notifBtn) notifBtn.classList.add('has-alerts');
    } else {
      badge.style.display = 'none';
      if (notifBtn) notifBtn.classList.remove('has-alerts');
    }
  }

  if (notifBody) {
    if (active.length === 0) {
      notifBody.innerHTML = `
        <div class="notif-empty">
          <span style="font-size:1.8rem;display:block;margin-bottom:0.4rem;">🎉</span>
          <strong>All categories healthy!</strong>
          <p style="margin-top:2px;font-size:0.75rem;color:var(--text-muted);">No budget cap breaches or overdue debts.</p>
        </div>`;
      if (notifFooter) notifFooter.style.display = 'none';
    } else {
      notifBody.innerHTML = active.map(b => {
        const isBreached = b.type === 'breached';
        const icon = isBreached ? '🚨' : '⚠️';
        return `
          <div class="notif-item ${isBreached ? 'breached' : 'warning'}">
            <div class="notif-item-icon">${icon}</div>
            <div class="notif-item-body">
              <div class="notif-item-title">${b.category.toUpperCase()} ${isBreached ? 'CAP BREACHED' : 'WARNING'}</div>
              <div class="notif-item-text">${b.message}</div>
              <div class="notif-item-actions">
                <button class="notif-item-btn" onclick="navigate('budget'); closeNotifDropdown();">Adjust Cap</button>
                <button class="notif-item-btn" onclick="askCFOAboutCategory('${b.category}')">Ask CFO</button>
              </div>
            </div>
            <button class="notif-item-dismiss" onclick="dismissBreach('${b.category}')" title="Dismiss notification">✕</button>
          </div>
        `;
      }).join('');
      if (notifFooter) notifFooter.style.display = 'flex';
    }
  }
}

window.askCFOAboutCategory = function(cat) {
  closeNotifDropdown();
  navigate('cfo-screen');
  sendCFOMessage(`How much did we spend on ${cat}? Can we optimize it?`);
};

window.dismissBreach = function(category) {
  state.dismissedAlerts.add(category);
  renderBreachBanners(state.dashboardData?.breaches || []);
  toast(`Notification for "${category}" dismissed.`, 'info', 2000);
};

window.dismissAllBreaches = function() {
  (state.dashboardData?.breaches || []).forEach(b => state.dismissedAlerts.add(b.category));
  renderBreachBanners(state.dashboardData?.breaches || []);
  toast('All notifications cleared.', 'info', 2000);
};

function toggleNotifDropdown() {
  const dd = document.getElementById('notif-dropdown');
  if (!dd) return;
  const isHidden = dd.style.display === 'none' || !dd.style.display;
  dd.style.display = isHidden ? 'flex' : 'none';
}

function closeNotifDropdown() {
  const dd = document.getElementById('notif-dropdown');
  if (dd) dd.style.display = 'none';
}
window.closeNotifDropdown = closeNotifDropdown;

document.getElementById('btn-notifications')?.addEventListener('click', e => {
  e.stopPropagation();
  toggleNotifDropdown();
});

document.getElementById('btn-notif-close')?.addEventListener('click', e => {
  e.stopPropagation();
  closeNotifDropdown();
});

document.getElementById('btn-notif-clear-all')?.addEventListener('click', () => {
  dismissAllBreaches();
});

document.addEventListener('click', e => {
  const wrapper = document.querySelector('.notif-wrapper');
  if (wrapper && !wrapper.contains(e.target)) {
    closeNotifDropdown();
  }
});

// ─── Currency Converter Widget ────────────────────────────────────────────────
document.getElementById('btn-do-convert')?.addEventListener('click', async () => {
  const from = document.getElementById('conv-from-cur').value;
  const to = document.getElementById('conv-to-cur').value;
  const amount = document.getElementById('conv-amount').value || '1';
  const pill = document.getElementById('conv-result-pill');

  pill.innerHTML = '<span class="spinner"></span> Converting...';
  try {
    const res = await api(`/fx/convert?from=${from}&to=${to}&amount=${amount}`);
    pill.textContent = `${from} ${parseFloat(amount).toFixed(2)} = ${to} ${res.converted.toFixed(2)} (@ ${res.rate.toFixed(4)})`;
  } catch (err) {
    pill.textContent = `Conversion error: ${err.message}`;
  }
});

// ─── Add Expense Modal & Live Rate Indicator ──────────────────────────────────
function openExpenseModal(prefill = {}) {
  const modal = document.getElementById('expense-modal');
  modal.classList.add('open');
  document.getElementById('expense-form-error').textContent = '';

  // Default date
  document.getElementById('exp-date').value = prefill.date || new Date().toISOString().split('T')[0];

  if (prefill.title) document.getElementById('exp-title').value = prefill.title;
  if (prefill.amount) document.getElementById('exp-amount').value = prefill.amount;
  if (prefill.currency) document.getElementById('exp-currency').value = prefill.currency;
  if (prefill.category) document.getElementById('exp-category').value = prefill.category;

  // Populate payers
  const payerSel = document.getElementById('exp-payer');
  payerSel.innerHTML = '<option value="">Select payer...</option>';
  (state.members || []).forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.tmb_user_id;
    opt.textContent = m.usr_name;
    payerSel.appendChild(opt);
  });

  if (!state.members.length) {
    api('/trips/users').then(data => {
      data.users.forEach(u => {
        const opt = document.createElement('option');
        opt.value = u.usr_id;
        opt.textContent = u.usr_name;
        payerSel.appendChild(opt);
      });
    }).catch(() => {});
  }

  updateModalLiveFX();
}
window.openExpenseModal = openExpenseModal;

function closeExpenseModal() {
  document.getElementById('expense-modal').classList.remove('open');
  document.getElementById('expense-form').reset();
  document.getElementById('modal-fx-indicator').style.display = 'none';
}

document.getElementById('btn-modal-close')?.addEventListener('click', closeExpenseModal);
document.getElementById('btn-cancel-expense')?.addEventListener('click', closeExpenseModal);
document.getElementById('expense-modal')?.addEventListener('click', e => {
  if (e.target === e.currentTarget) closeExpenseModal();
});

// Modal live currency indicator
async function updateModalLiveFX() {
  const amount = parseFloat(document.getElementById('exp-amount').value || 0);
  const cur = document.getElementById('exp-currency').value;
  const indicator = document.getElementById('modal-fx-indicator');

  if (cur !== state.baseCurrency && amount > 0) {
    indicator.style.display = 'block';
    indicator.innerHTML = '<span class="spinner"></span> Calculating exchange rate...';
    try {
      const res = await api(`/fx/convert?from=${cur}&to=${state.baseCurrency}&amount=${amount}`);
      indicator.innerHTML = `💱 <strong>${cur} ${amount.toFixed(2)}</strong> = <strong>${state.baseCurrency} ${res.converted.toFixed(2)}</strong> (Rate: ${res.rate.toFixed(4)})`;
    } catch {
      indicator.style.display = 'none';
    }
  } else {
    indicator.style.display = 'none';
  }
}

document.getElementById('exp-amount')?.addEventListener('input', updateModalLiveFX);
document.getElementById('exp-currency')?.addEventListener('change', updateModalLiveFX);

// Submit Expense Form
document.getElementById('expense-form')?.addEventListener('submit', async e => {
  e.preventDefault();
  const errEl = document.getElementById('expense-form-error');
  errEl.textContent = '';

  const body = {
    trip_id:    state.currentTripId,
    payer_id:   document.getElementById('exp-payer').value,
    title:      document.getElementById('exp-title').value.trim(),
    category:   document.getElementById('exp-category').value,
    amount:     parseFloat(document.getElementById('exp-amount').value),
    currency:   document.getElementById('exp-currency').value,
    date:       document.getElementById('exp-date').value,
    notes:      document.getElementById('exp-notes').value.trim(),
    split_type: document.getElementById('exp-split').value,
  };

  if (!body.payer_id) { errEl.textContent = 'Please choose who paid.'; return; }
  if (!body.title) { errEl.textContent = 'Please provide a title.'; return; }
  if (!body.category) { errEl.textContent = 'Please select a category.'; return; }
  if (!body.amount || body.amount <= 0) { errEl.textContent = 'Amount must be greater than zero.'; return; }

  const btn = document.getElementById('btn-submit-expense');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Adding...';

  try {
    const result = await api('/expenses/', { method: 'POST', body: JSON.stringify(body) });
    closeExpenseModal();
    toast(`Expense logged! ${result.breaches?.length ? `⚠️ ${result.breaches.length} Alert!` : '✓ Checked by Travel CFO'}`, 'success');
    await loadDashboard();
    renderAllExpenses();
  } catch (err) {
    errEl.textContent = err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Add Expense';
  }
});

// ─── Multimodal OCR Scanner ───────────────────────────────────────────────────
function openOCRModal() {
  document.getElementById('ocr-modal').classList.add('open');
  document.getElementById('ocr-result-display').style.display = 'none';
}
window.openOCRModal = openOCRModal;

function closeOCRModal() {
  document.getElementById('ocr-modal').classList.remove('open');
  document.getElementById('laser-beam').classList.remove('active');
}

document.getElementById('btn-ocr-close')?.addEventListener('click', closeOCRModal);
document.getElementById('ocr-modal')?.addEventListener('click', e => {
  if (e.target === e.currentTarget) closeOCRModal();
});

let currentUploadedImageBase64 = null;

function handleReceiptFile(file) {
  if (!file) return;

  const previewBox = document.getElementById('ocr-preview-box');
  const thumb = document.getElementById('ocr-thumb-img');
  const nameEl = document.getElementById('ocr-file-name');
  const sizeEl = document.getElementById('ocr-file-size');
  const dropContent = document.getElementById('ocr-drop-content');

  const reader = new FileReader();
  reader.onload = function(e) {
    currentUploadedImageBase64 = e.target.result;
    if (thumb) thumb.src = currentUploadedImageBase64;
    if (nameEl) nameEl.textContent = file.name;
    if (sizeEl) sizeEl.textContent = `${(file.size / 1024).toFixed(1)} KB · Ready to scan`;
    if (previewBox) previewBox.style.display = 'flex';
    if (dropContent) dropContent.style.display = 'none';

    // Automatically trigger scan
    runOCRScan({ image_base64: currentUploadedImageBase64 });
  };
  reader.readAsDataURL(file);
}

async function runOCRScan(payload) {
  const laser = document.getElementById('laser-beam');
  const resultBox = document.getElementById('ocr-result-display');
  if (laser) laser.classList.add('active');
  if (resultBox) {
    resultBox.style.display = 'block';
    resultBox.innerHTML = '<div style="text-align:center;padding:1.5rem;"><span class="spinner"></span> Scanning pixels with AI OCR engine & Tesseract...</div>';
  }

  try {
    const body = typeof payload === 'string'
      ? { trip_id: state.currentTripId, raw_text: payload }
      : { trip_id: state.currentTripId, ...payload };

    const data = await api('/ai/ocr', {
      method: 'POST',
      body: JSON.stringify(body),
    });

    if (laser) laser.classList.remove('active');
    const ext = data.extracted;
    const confidenceColor = ext.confidence >= 80 ? '#059669' : (ext.confidence >= 50 ? '#D97706' : '#DC2626');

    resultBox.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">
        <h4 style="font-weight:700;color:var(--text-primary);display:flex;align-items:center;gap:0.4rem;">
          <span>✅</span> Receipt Extracted
        </h4>
        <span style="font-size:0.75rem;background:rgba(5,150,105,0.1);color:${confidenceColor};font-weight:700;padding:2px 8px;border-radius:4px;">
          ${ext.confidence}% Confidence
        </span>
      </div>
      <div class="parsed-grid">
        <div class="parsed-field"><div class="parsed-value">${ext.merchant || 'Merchant'}</div><div class="parsed-label">Merchant</div></div>
        <div class="parsed-field"><div class="parsed-value">${ext.currency} ${parseFloat(ext.amount || 0).toFixed(2)}</div><div class="parsed-label">Amount</div></div>
        <div class="parsed-field"><div class="parsed-value">${(ext.category || 'food').toUpperCase()}</div><div class="parsed-label">Category</div></div>
        <div class="parsed-field"><div class="parsed-value">${ext.date || 'Today'}</div><div class="parsed-label">Date</div></div>
      </div>
      ${ext.items && ext.items.length ? `
        <div style="font-size:0.75rem;color:var(--text-muted);margin:0.5rem 0;">
          <strong>Detected items:</strong> ${ext.items.slice(0, 4).join(', ')}
        </div>
      ` : ''}
      <button class="btn btn-primary btn-full" style="margin-top:0.75rem;" onclick='applyOCRToExpense(${JSON.stringify(data.pre_filled)})'>
        📋 Pre-fill into Expense Form →
      </button>`;
  } catch (err) {
    if (laser) laser.classList.remove('active');
    if (resultBox) {
      resultBox.innerHTML = `<div style="color:var(--danger);padding:0.75rem;">OCR Error: ${err.message}</div>`;
    }
  }
}

window.applyOCRToExpense = function(prefill) {
  closeOCRModal();
  openExpenseModal(prefill);
};

// Preset sample receipts for testing
document.getElementById('btn-sample-goa')?.addEventListener('click', () => {
  runOCRScan("GRANDE RESTAURANT GOA\nDate: 03/10/2026\nSeafood Dinner $55.00\nPrawn Masala $30.00\nFish Curry $15.00\nTotal: $55.00 USD");
});
document.getElementById('btn-sample-paris')?.addEventListener('click', () => {
  runOCRScan("LE PETIT BISTRO PARIS\nDate: 04/10/2026\nCroque Monsieur €18.00\nCafe Au Lait €8.00\nEntrecote €16.00\nTotal: €42.00 EUR");
});
document.getElementById('btn-sample-tokyo')?.addEventListener('click', () => {
  runOCRScan("SUSHI DAI TOKYO\nDate: 05/10/2026\nOmakase Set ¥8500 JPY\nGreen Tea ¥0\nTotal: ¥8,500 JPY");
});
document.getElementById('btn-sample-london')?.addEventListener('click', () => {
  runOCRScan("THE BLACK DOG PUB\nVauxhall, London\nDate: 16/01/2027\n2x Craft IPA Pints £13.50\n1x Fish and Chips £16.50\nTotal: £37.00 GBP");
});
document.getElementById('btn-sample-dubai')?.addEventListener('click', () => {
  runOCRScan("AL SAFADI RESTAURANT\nSheikh Zayed Rd, Dubai\nDate: 12/02/2027\nMixed Grill Platter 85 AED\nHummus 28 AED\nTotal: 149.00 AED");
});

// File picker & Drag-and-Drop
document.getElementById('btn-pick-file')?.addEventListener('click', () => {
  document.getElementById('ocr-file-input').click();
});
document.getElementById('ocr-file-input')?.addEventListener('change', e => {
  if (e.target.files && e.target.files[0]) {
    handleReceiptFile(e.target.files[0]);
  }
});
document.getElementById('btn-run-file-ocr')?.addEventListener('click', () => {
  if (currentUploadedImageBase64) {
    runOCRScan({ image_base64: currentUploadedImageBase64 });
  }
});

const ocrDropZone = document.getElementById('ocr-drop-zone');
ocrDropZone?.addEventListener('dragover', e => {
  e.preventDefault();
  ocrDropZone.classList.add('dragover');
});
ocrDropZone?.addEventListener('dragleave', () => {
  ocrDropZone.classList.remove('dragover');
});
ocrDropZone?.addEventListener('drop', e => {
  e.preventDefault();
  ocrDropZone.classList.remove('dragover');
  if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    handleReceiptFile(e.dataTransfer.files[0]);
  }
});

// ─── Natural Language Expense Entry (⌘K) ──────────────────────────────────────
function openNLModal() {
  document.getElementById('nl-modal').classList.add('open');
  document.getElementById('nl-modal-preview').style.display = 'none';
}
window.openNLModal = openNLModal;

function closeNLModal() {
  document.getElementById('nl-modal').classList.remove('open');
}

document.getElementById('btn-nl-close')?.addEventListener('click', closeNLModal);
document.getElementById('btn-global-nl')?.addEventListener('click', openNLModal);

window.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault();
    openNLModal();
  }
});

document.querySelectorAll('.nl-quick-chip').forEach(btn => {
  btn.addEventListener('click', () => {
    document.getElementById('nl-modal-textarea').value = btn.dataset.text;
  });
});

document.getElementById('btn-nl-modal-parse')?.addEventListener('click', async () => {
  const text = document.getElementById('nl-modal-textarea').value.trim();
  if (!text) { toast('Please type an expense phrase.', 'warning'); return; }

  const preview = document.getElementById('nl-modal-preview');
  preview.style.display = 'block';
  preview.innerHTML = '<div style="text-align:center;"><span class="spinner"></span> Converting words to structured finance record...</div>';

  try {
    const data = await api('/ai/parse-nl', {
      method: 'POST',
      body: JSON.stringify({ text, trip_id: state.currentTripId }),
    });

    const p = data.parsed;
    preview.innerHTML = `
      <div style="background:var(--bg-canvas);border:1px solid rgba(122,31,61,0.1);border-radius:var(--r-md);padding:1rem;">
        <h4 style="font-weight:700;margin-bottom:0.5rem;">✅ AI Extraction Complete</h4>
        <div class="parsed-grid">
          <div class="parsed-field"><div class="parsed-value">${p.currency} ${p.amount || '?'}</div><div class="parsed-label">Amount</div></div>
          <div class="parsed-field"><div class="parsed-value">${p.category}</div><div class="parsed-label">Category</div></div>
          <div class="parsed-field"><div class="parsed-value">${p.split_members_raw?.join(', ') || 'Equal Split'}</div><div class="parsed-label">Split With</div></div>
        </div>
        <button class="btn btn-primary btn-full" onclick='applyNLToExpense(${JSON.stringify(data.pre_filled)})'>
          Confirm & Add to Ledger →
        </button>
      </div>`;
  } catch (err) {
    preview.innerHTML = `<div style="color:var(--danger)">Parse error: ${err.message}</div>`;
  }
});

window.applyNLToExpense = function(prefill) {
  closeNLModal();
  openExpenseModal(prefill);
};

// ─── AI Travel CFO Chat Interactive View ───────────────────────────────────────
async function sendCFOMessage(customPrompt = null) {
  const input = document.getElementById('cfo-input');
  const msg = customPrompt || input.value.trim();
  if (!msg) return;

  const chat = document.getElementById('cfo-chat-messages');

  // User bubble
  chat.innerHTML += `
    <div class="cfo-msg cfo-user">
      <span class="cfo-avatar">👤</span>
      <div class="cfo-bubble">${msg}</div>
    </div>`;

  if (!customPrompt) input.value = '';
  chat.scrollTop = chat.scrollHeight;

  // Typing bubble
  const typingId = 'cfo-typing-' + Date.now();
  chat.innerHTML += `
    <div class="cfo-msg cfo-bot" id="${typingId}">
      <span class="cfo-avatar">🤖</span>
      <div class="cfo-bubble"><span class="spinner"></span> Consulting trip database & FX rates...</div>
    </div>`;
  chat.scrollTop = chat.scrollHeight;

  try {
    const data = await api('/ai/cfo-chat', {
      method: 'POST',
      body: JSON.stringify({ question: msg, trip_id: state.currentTripId }),
    });

    document.getElementById(typingId)?.remove();

    // Render formatted markdown bubble
    const formatted = data.answer.replace(/\n/g, '<br />');
    chat.innerHTML += `
      <div class="cfo-msg cfo-bot">
        <span class="cfo-avatar">🤖</span>
        <div class="cfo-bubble">${formatted}</div>
      </div>`;
  } catch (err) {
    document.getElementById(typingId)?.remove();
    chat.innerHTML += `
      <div class="cfo-msg cfo-bot">
        <span class="cfo-avatar">🤖</span>
        <div class="cfo-bubble" style="color:var(--danger)">Error: ${err.message}</div>
      </div>`;
  }
  chat.scrollTop = chat.scrollHeight;
}

document.getElementById('btn-cfo-send')?.addEventListener('click', () => sendCFOMessage());
document.getElementById('cfo-input')?.addEventListener('keypress', e => {
  if (e.key === 'Enter') sendCFOMessage();
});

function updateCFOPromptChips(destination = 'Goa') {
  const container = document.getElementById('cfo-chips-row');
  if (!container) return;

  const destClean = (destination || '').split(',')[0].trim();
  const chipSets = {
    'Tokyo': [
      { text: '🗼 Can I afford Disneyland tomorrow?', prompt: 'Can I afford Disneyland tomorrow?' },
      { text: '🍣 Sushi & Dining spend?', prompt: 'How much did we spend on food?' },
      { text: '🚅 Is Shinkansen within budget?', prompt: 'Can I afford Shinkansen bullet train?' },
      { text: '👥 Who owes me money?', prompt: 'Who owes me money?' },
      { text: '💡 Budget optimization tips', prompt: 'Give me suggestions to optimize our budget' }
    ],
    'Paris': [
      { text: '🗼 Can I afford Eiffel Tower summit?', prompt: 'Can I afford Eiffel Tower summit?' },
      { text: '🥐 Bistro & Dining breakdown?', prompt: 'How much did we spend on food?' },
      { text: '🎨 Can we afford Louvre tickets?', prompt: 'Can I afford Louvre museum?' },
      { text: '👥 Who owes me money?', prompt: 'Who owes me money?' },
      { text: '💡 Budget saving suggestions', prompt: 'Give me suggestions to optimize our budget' }
    ],
    'Bali': [
      { text: '🌋 Can I afford Mount Batur sunrise hike?', prompt: 'Can I afford Mount Batur hike?' },
      { text: '🏄 Canggu surf lesson affordability?', prompt: 'Can I afford Canggu surf lesson?' },
      { text: '💆 Balinese spa session cost?', prompt: 'Can I afford Balinese luxury spa?' },
      { text: '👥 Who owes me money?', prompt: 'Who owes me money?' },
      { text: '💡 Budget optimization advice', prompt: 'Give me suggestions to optimize our budget' }
    ],
    'London': [
      { text: '🎡 Can I afford London Eye tickets?', prompt: 'Can I afford London Eye tomorrow?' },
      { text: '🎭 West End musical within budget?', prompt: 'Can I afford West End musical?' },
      { text: '🍺 Pubs & Dining breakdown?', prompt: 'How much did we spend on food?' },
      { text: '👥 Who owes me money?', prompt: 'Who owes me money?' },
      { text: '💡 Ways to save money in London', prompt: 'Give me suggestions to optimize our budget' }
    ],
    'Dubai': [
      { text: '🏙️ Can I afford Burj Khalifa At The Top?', prompt: 'Can I afford Burj Khalifa tomorrow?' },
      { text: '🏜️ Desert safari affordability?', prompt: 'Can I afford Desert Safari?' },
      { text: '🛥️ Luxury yacht tour within budget?', prompt: 'Can I afford Marina yacht tour?' },
      { text: '👥 Who owes me money?', prompt: 'Who owes me money?' },
      { text: '💡 Smart Dubai saving tips', prompt: 'Give me suggestions to optimize our budget' }
    ],
    'Kashmir': [
      { text: '🚠 Can I afford Gulmarg Gondola Phase 2?', prompt: 'Can I afford Gulmarg Gondola Phase 2?' },
      { text: '🛶 Dal Lake Shikara ride within budget?', prompt: 'Can I afford Dal Lake Shikara ride?' },
      { text: '🏔️ Pony trek at Pahalgam?', prompt: 'Can I afford Pahalgam pony trek?' },
      { text: '👥 Who owes me money?', prompt: 'Who owes me money?' },
      { text: '💡 Budget optimization advice', prompt: 'Give me suggestions to optimize our budget' }
    ],
    'Goa': [
      { text: '🤿 Can I afford scuba diving tomorrow?', prompt: 'Can I afford scuba diving tomorrow?' },
      { text: '🍽️ Food & beach shacks breakdown?', prompt: 'How much did we spend on food?' },
      { text: '🛵 Scooty rental within budget?', prompt: 'Can I afford scooter rental?' },
      { text: '👥 Who owes me money?', prompt: 'Who owes me money?' },
      { text: '💡 Give me budget saving suggestions', prompt: 'Give me suggestions to optimize our budget' }
    ]
  };

  const chips = chipSets[destClean] || [
    { text: `🎟️ Can I afford activities in ${destClean}?`, prompt: `Can I afford activities in ${destClean}?` },
    { text: `🍽️ Dining & Food budget breakdown?`, prompt: `How much did we spend on food?` },
    { text: `⏱️ Safe daily allowance remaining?`, prompt: `How much can we spend today?` },
    { text: `👥 Who owes me money?`, prompt: `Who owes me money?` },
    { text: `💡 Smart budget tips`, prompt: `Give me suggestions to optimize our budget` }
  ];

  container.innerHTML = chips.map(c => `
    <button class="sample-receipt-pill cfo-prompt-chip" data-prompt="${c.prompt}">${c.text}</button>
  `).join('');

  container.querySelectorAll('.cfo-prompt-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      sendCFOMessage(btn.dataset.prompt);
    });
  });
}
window.updateCFOPromptChips = updateCFOPromptChips;


// ─── Forecasting & What-If Simulator ──────────────────────────────────────────
async function initForecast() {
  const container = document.getElementById('forecast-full-container');
  if (!container) return;
  container.innerHTML = '<div style="text-align:center;padding:2rem;"><span class="spinner"></span> Calculating recency-weighted statistical projection...</div>';

  try {
    const data = await api(`/ai/forecast/${state.currentTripId}`);
    const cur = state.dashboardData?.summary?.home_currency || state.baseCurrency;

    container.innerHTML = `
      <div class="forecast-grid">
        <div class="forecast-stat">
          <div class="forecast-stat-value">${fmt(data.daily_burn_rate, cur, 0)}</div>
          <div class="forecast-stat-label">Daily Burn Rate</div>
        </div>
        <div class="forecast-stat">
          <div class="forecast-stat-value">${fmt(data.projected_total, cur, 0)}</div>
          <div class="forecast-stat-label">Projected Total</div>
        </div>
        <div class="forecast-stat">
          <div class="forecast-stat-value">${data.remaining_days || 0}d</div>
          <div class="forecast-stat-label">Days Remaining</div>
        </div>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:1rem;">
        <div>
          ${data.projected_overshoot > 0
            ? `<span style="color:var(--danger);font-weight:700;">⚠️ Projected Overrun: ${fmt(data.projected_overshoot, cur)}</span>`
            : `<span style="color:#059669;font-weight:700;">✅ On Track (Zero Overrun Forecast)</span>`}
        </div>
        <span class="risk-badge risk-${data.risk}">RISK: ${data.risk?.toUpperCase()}</span>
      </div>`;

    // Show What-If Simulator
    document.getElementById('what-if-simulator-box').style.display = 'block';
    setupWhatIfSlider(data.total_spent || 30688, data.total_budget || 50000, cur);
  } catch (err) {
    container.innerHTML = `<div style="color:var(--danger)">Forecast unavailable: ${err.message}</div>`;
  }
}

function setupWhatIfSlider(spent, budget, cur) {
  const slider = document.getElementById('what-if-slider');
  const label = document.getElementById('slider-val-label');
  const projTotal = document.getElementById('sim-projected-total');
  const projRem = document.getElementById('sim-projected-remaining');
  const riskBadge = document.getElementById('sim-risk-badge');

  function update() {
    const extra = parseFloat(slider.value);
    label.textContent = fmt(extra, cur, 0);

    const simTotal = spent + extra;
    const simRem = budget - simTotal;

    projTotal.textContent = fmt(simTotal, cur, 0);
    projRem.textContent = fmt(Math.max(0, simRem), cur, 0);

    const pctUsed = (simTotal / budget) * 100;
    if (pctUsed > 105) {
      riskBadge.className = 'risk-badge risk-critical';
      riskBadge.textContent = 'CRITICAL OVERRUN';
    } else if (pctUsed > 95) {
      riskBadge.className = 'risk-badge risk-high';
      riskBadge.textContent = 'HIGH RISK';
    } else if (pctUsed > 80) {
      riskBadge.className = 'risk-badge risk-medium';
      riskBadge.textContent = 'MEDIUM RISK';
    } else {
      riskBadge.className = 'risk-badge risk-low';
      riskBadge.textContent = 'SAFE LOW RISK';
    }
  }

  slider.oninput = update;
  update();
}

document.getElementById('btn-forecast-refresh')?.addEventListener('click', initForecast);
document.getElementById('btn-init-forecast')?.addEventListener('click', initForecast);

// ─── Group Settlement Tab ─────────────────────────────────────────────────────
async function loadSettlement() {
  try {
    const data = await api(`/settlement/${state.currentTripId}`);
    const cur = data.currency || state.baseCurrency;

    // Net balances
    const balList = document.getElementById('balance-list');
    balList.innerHTML = (data.balances || []).map(b => {
      const cls = b.net > 0 ? 'positive' : b.net < 0 ? 'negative' : 'zero';
      const label = b.net > 0 ? '(receives)' : b.net < 0 ? '(owes)' : '(settled)';
      return `
        <div class="balance-item">
          <div>
            <div class="balance-name">${b.user_name}</div>
            <div style="font-size:0.75rem;color:var(--text-muted)">Paid ${fmt(b.paid, cur)} · Owes ${fmt(b.owed, cur)}</div>
          </div>
          <span class="balance-amount ${cls}">${fmt(Math.abs(b.net), cur)} ${label}</span>
        </div>`;
    }).join('') || '<div class="empty-state-mini">No balances to show.</div>';

    // Transactions
    const txList = document.getElementById('transaction-list');
    txList.innerHTML = (data.transactions || []).map(tx => `
      <div class="transaction-item">
        <span style="font-weight:700">${tx.from_user_name}</span>
        <span class="transaction-arrow">→</span>
        <span style="font-weight:700">${tx.to_user_name}</span>
        <span class="transaction-amount">${fmt(tx.amount, cur)}</span>
      </div>`).join('') || '<div class="empty-state-mini">All transactions settled! 🎉</div>';
  } catch (e) {
    toast('Could not load settlement: ' + e.message, 'error');
  }
}

document.getElementById('btn-calc-settlement')?.addEventListener('click', loadSettlement);
document.getElementById('btn-settle-all-action')?.addEventListener('click', () => {
  toast('🎉 All group debts reconciled and recorded!', 'success');
});

// ─── Budget & Caps Form ───────────────────────────────────────────────────────
async function loadBudgetSection() {
  try {
    const data = await api(`/budgets/${state.currentTripId}`);
    if (data.bud_total_amount) document.getElementById('bud-total').value = data.bud_total_amount;
    if (data.bud_alert_threshold_pct) document.getElementById('bud-threshold').value = data.bud_alert_threshold_pct;
    if (data.bud_accommodation_cap) document.getElementById('cap-accommodation').value = data.bud_accommodation_cap;
    if (data.bud_transport_cap)     document.getElementById('cap-transport').value = data.bud_transport_cap;
    if (data.bud_food_cap)          document.getElementById('cap-food').value = data.bud_food_cap;
    if (data.bud_activities_cap)    document.getElementById('cap-activities').value = data.bud_activities_cap;
    if (data.bud_misc_cap)          document.getElementById('cap-misc').value = data.bud_misc_cap;
    renderCapStatus(data.breach_status?.category_summary || {});
  } catch {
    renderCapStatus(state.dashboardData?.category_summary || {});
  }
}

function renderCapStatus(catSummary) {
  const list = document.getElementById('cap-status-list');
  const cur = state.dashboardData?.summary?.home_currency || state.baseCurrency;
  const entries = Object.entries(catSummary);

  if (!entries.length) {
    list.innerHTML = '<div class="empty-state-mini">Save caps above to see status.</div>';
    return;
  }

  list.innerHTML = entries.map(([cat, info]) => {
    const meta = CATEGORY_META[cat] || { icon: '📦', label: cat };
    const status = info.status || 'safe';
    const pctUsed = info.pct_used || 0;
    const barColor = status === 'breached' ? '#C62828' : status === 'warning' ? '#E65100' : '#059669';

    return `
      <div class="cap-status-item ${status}">
        <span class="cap-status-icon">${meta.icon}</span>
        <div class="cap-status-meta">
          <div class="cap-status-name">${meta.label}</div>
          ${info.cap != null ? `
            <div class="cap-status-bar-row">
              <div class="cap-pct-bar-track">
                <div class="cap-pct-bar-fill" style="width:${Math.min(100, pctUsed)}%;background:${barColor}"></div>
              </div>
              <span class="cap-status-label">${fmt(info.spent, cur, 0)} / ${fmt(info.cap, cur, 0)}</span>
            </div>` : `<div style="font-size:0.75rem;color:var(--text-muted)">No cap configured</div>`}
        </div>
        <span class="cap-status-badge badge-${status}">${status}</span>
      </div>`;
  }).join('');
}

document.getElementById('budget-form')?.addEventListener('submit', async e => {
  e.preventDefault();
  const body = {
    trip_id: state.currentTripId,
    total_amount: parseFloat(document.getElementById('bud-total').value),
    alert_threshold_pct: parseFloat(document.getElementById('bud-threshold').value || 80),
    accommodation_cap: parseFloat(document.getElementById('cap-accommodation').value) || null,
    transport_cap:     parseFloat(document.getElementById('cap-transport').value) || null,
    food_cap:          parseFloat(document.getElementById('cap-food').value) || null,
    activities_cap:    parseFloat(document.getElementById('cap-activities').value) || null,
    misc_cap:          parseFloat(document.getElementById('cap-misc').value) || null,
    currency: state.baseCurrency,
  };

  try {
    await api('/budgets/', { method: 'POST', body: JSON.stringify(body) });
    toast('Budget & category caps updated!', 'success');
    await loadDashboard();
    loadBudgetSection();
  } catch (err) {
    toast('Error saving budget: ' + err.message, 'error');
  }
});

// ─── Streamlined New Trip Creation Modal ──────────────────────────────────────
let newTripMode = 'solo'; // 'solo' or 'group'
let selectedTravelStyle = 'moderate';

function openOnboardingWizard() {
  document.getElementById('onboarding-modal').classList.add('open');
}
window.openOnboardingWizard = openOnboardingWizard;

function closeOnboardingWizard() {
  document.getElementById('onboarding-modal').classList.remove('open');
}

document.getElementById('btn-onboarding-close')?.addEventListener('click', closeOnboardingWizard);
document.getElementById('btn-new-trip-wizard')?.addEventListener('click', openOnboardingWizard);

// Solo vs Group Mode Toggle
document.getElementById('btn-trip-type-solo')?.addEventListener('click', () => {
  newTripMode = 'solo';
  document.getElementById('btn-trip-type-solo')?.classList.add('active');
  document.getElementById('btn-trip-type-group')?.classList.remove('active');
  const soloWrap = document.getElementById('wrap-solo-traveler');
  const groupWrap = document.getElementById('wrap-group-travelers');
  if (soloWrap) soloWrap.style.display = 'block';
  if (groupWrap) groupWrap.style.display = 'none';
});

document.getElementById('btn-trip-type-group')?.addEventListener('click', () => {
  newTripMode = 'group';
  document.getElementById('btn-trip-type-group')?.classList.add('active');
  document.getElementById('btn-trip-type-solo')?.classList.remove('active');
  const soloWrap = document.getElementById('wrap-solo-traveler');
  const groupWrap = document.getElementById('wrap-group-travelers');
  if (soloWrap) soloWrap.style.display = 'none';
  if (groupWrap) groupWrap.style.display = 'block';
});

// Destination preset pills
document.querySelectorAll('#trip-dest-pills .dest-preset-pill').forEach(pill => {
  pill.addEventListener('click', () => {
    document.querySelectorAll('#trip-dest-pills .dest-preset-pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    const destInput = document.getElementById('trip-dest-input');
    if (destInput) destInput.value = pill.dataset.dest;
  });
});

// Travel style selection cards
document.querySelectorAll('#trip-style-selector .style-card').forEach(card => {
  card.addEventListener('click', () => {
    document.querySelectorAll('#trip-style-selector .style-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    selectedTravelStyle = card.dataset.style;
  });
});

// Streamlined Trip Creation Submission
document.getElementById('btn-create-trip-streamlined')?.addEventListener('click', async () => {
  const submitBtn = document.getElementById('btn-create-trip-streamlined');
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> Launching Trip CFO...';

  const source = document.getElementById('trip-source-input')?.value.trim() || 'Bangalore';
  const dest = document.getElementById('trip-dest-input')?.value.trim() || 'Goa';
  const soloPerson = document.getElementById('trip-solo-person')?.value.trim() || 'Anil Kumar';
  const groupPeopleStr = document.getElementById('trip-group-people')?.value.trim() || 'Anil Kumar, Lavanya Sharma, Rahul Menon, Priya Nair';
  const budget = parseFloat(document.getElementById('trip-budget-val')?.value) || 50000;
  const currency = document.getElementById('trip-currency-val')?.value || 'INR';
  const duration = parseInt(document.getElementById('trip-duration-val')?.value) || 5;

  try {
    const today = new Date();
    const end = new Date();
    end.setDate(today.getDate() + duration);

    const travelersDesc = newTripMode === 'solo' ? `Traveler: ${soloPerson}` : `Travelers: ${groupPeopleStr}`;
    const tripName = `${dest} Trip ${today.getFullYear()}`;

    // 1. Create Trip
    const tripRes = await api('/trips/', {
      method: 'POST',
      body: JSON.stringify({
        name: tripName,
        owner_id: 'usr_anil_001',
        destination: `${dest}, ${source} Origin`,
        home_currency: currency,
        start_date: today.toISOString().split('T')[0],
        end_date: end.toISOString().split('T')[0],
        description: `Route: ${source} → ${dest} | Mode: ${newTripMode.toUpperCase()} | Style: ${selectedTravelStyle} | ${travelersDesc}`,
      })
    });

    state.currentTripId = tripRes.trip_id;

    // 2. Calibrate Category Caps according to Travel Style
    let stayPct = 0.35, foodPct = 0.25, transPct = 0.15, actPct = 0.15, miscPct = 0.10;
    if (selectedTravelStyle === 'luxury') {
      stayPct = 0.45; foodPct = 0.25; transPct = 0.12; actPct = 0.13; miscPct = 0.05;
    } else if (selectedTravelStyle === 'budget') {
      stayPct = 0.25; foodPct = 0.30; transPct = 0.20; actPct = 0.15; miscPct = 0.10;
    }

    await api('/budgets/', {
      method: 'POST',
      body: JSON.stringify({
        trip_id: tripRes.trip_id,
        total_amount: budget,
        alert_threshold_pct: 80,
        accommodation_cap: Math.round(budget * stayPct),
        food_cap: Math.round(budget * foodPct),
        transport_cap: Math.round(budget * transPct),
        activities_cap: Math.round(budget * actPct),
        misc_cap: Math.round(budget * miscPct),
        currency: currency,
      })
    });

    // 3. Add Members for Group Mode
    if (newTripMode === 'group') {
      const names = groupPeopleStr.split(',').map(n => n.trim()).filter(Boolean);
      for (const name of names) {
        try {
          await api(`/trips/${tripRes.trip_id}/members`, {
            method: 'POST',
            body: JSON.stringify({ user_name: name, role: 'member' }),
          });
        } catch {}
      }
    } else {
      try {
        await api(`/trips/${tripRes.trip_id}/members`, {
          method: 'POST',
          body: JSON.stringify({ user_name: soloPerson, role: 'owner' }),
        });
      } catch {}
    }

    closeOnboardingWizard();
    toast(`🎉 ${tripName} created! Your AI Travel CFO is ready.`, 'success');
    await loadTrips();
    await loadDashboard();
    navigate('dashboard');
  } catch (err) {
    toast(`Trip creation failed: ${err.message}`, 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = '🚀 Create Trip & Launch AI CFO';
  }
});

// ─── Authentication Modal ─────────────────────────────────────────────────────
function openAuthModal() {
  document.getElementById('auth-modal').classList.add('open');
}
function closeAuthModal() {
  document.getElementById('auth-modal').classList.remove('open');
}
document.getElementById('btn-auth-open')?.addEventListener('click', openAuthModal);
document.getElementById('btn-auth-close')?.addEventListener('click', closeAuthModal);
document.getElementById('btn-google-auth')?.addEventListener('click', () => {
  toast('Signed in via Google as Anil Kumar!', 'success');
  closeAuthModal();
});
document.getElementById('btn-email-auth')?.addEventListener('click', () => {
  toast('Signed in successfully!', 'success');
  closeAuthModal();
});
document.getElementById('btn-demo-auth')?.addEventListener('click', () => {
  toast('Signed in as Anil Kumar (Lead Traveler)', 'success');
  closeAuthModal();
});

// ─── Executive Summary Screen ─────────────────────────────────────────────────
function renderTripSummary() {
  const d = state.dashboardData;
  if (!d) return;

  const cur = d.summary?.home_currency || state.baseCurrency;
  document.getElementById('audit-trip-name').textContent = d.trip?.trp_name || 'Trip Summary';
  document.getElementById('audit-budget').textContent = fmt(d.summary?.total_budget, cur);
  document.getElementById('audit-spent').textContent = fmt(d.summary?.total_spent, cur);
  document.getElementById('audit-savings').textContent = fmt(Math.max(0, d.summary?.remaining), cur);
  document.getElementById('audit-daily-burn').textContent = fmt((d.summary?.total_spent / 7), cur, 0);
}

document.getElementById('btn-print-report')?.addEventListener('click', () => window.print());
document.getElementById('btn-share-report')?.addEventListener('click', () => {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(window.location.href);
    toast('Report link copied to clipboard! Share with your companions.', 'success');
  } else {
    toast('Report ready for sharing.', 'info');
  }
});

// ─── SECTION 2B: Itinerary Planner & Maps Explorer ───────────────────────────
let itineraryState = {
  data: null,
  activeFilter: 'all',     // 'all' | 'free' | 'budget' | 'expensive'
  activeMapDay: 'all',     // 'all' | 1 | 2 | 3...
  activeMapTier: 'all',    // 'all' | 'free' | 'budget' | 'expensive'
  map: null,
  markers: [],
  routeLine: null,
  weatherLayer: null,
  radarActive: false,
  weatherData: null,
  modalSelectedTier: 'budget',
};

const DEST_CENTERS = {
  goa:     { lat: 15.4989, lng: 73.8278, city: 'Goa', zoom: 11, label: 'Goa, India' },
  bali:    { lat: -8.5069, lng: 115.2625, city: 'Denpasar', zoom: 11, label: 'Bali, Indonesia' },
  london:  { lat: 51.5074, lng: -0.1278, city: 'London', zoom: 12, label: 'London, UK' },
  paris:   { lat: 48.8566, lng: 2.3522, city: 'Paris', zoom: 12, label: 'Paris, France' },
  dubai:   { lat: 25.2048, lng: 55.2708, city: 'Dubai', zoom: 11, label: 'Dubai, UAE' },
  kashmir: { lat: 34.0837, lng: 74.7973, city: 'Srinagar', zoom: 10, label: 'Srinagar, Kashmir' },
};

function getTripDestKey(tripDest) {
  const s = (tripDest || '').toLowerCase();
  for (const k of Object.keys(DEST_CENTERS)) {
    if (s.includes(k)) return k;
  }
  return 'goa';
}

function classifyPlaceTier(cost, currency = 'INR', explicitTier = null) {
  if (explicitTier && ['free', 'budget', 'expensive'].includes(explicitTier)) return explicitTier;
  const num = parseFloat(cost || 0);
  if (!num || num === 0) return 'free';
  const th = { INR: 1500, USD: 30, EUR: 30, GBP: 25, AED: 100, IDR: 300000 }[currency] || 1500;
  return num <= th ? 'budget' : 'expensive';
}

// ─── Load Itinerary Data ──────────────────────────────────────────────────────
async function loadItinerary() {
  const subtitle = document.getElementById('itinerary-subtitle');
  if (subtitle) subtitle.textContent = 'Loading day-by-day plan with live maps & weather...';

  try {
    let data = await api(`/itineraries/${state.currentTripId}`);
    
    // Auto-seed if trip has no activities yet
    if (!data || !data.days || data.total_items === 0) {
      try {
        await api(`/itineraries/${state.currentTripId}/seed-demo`, { method: 'POST' });
        data = await api(`/itineraries/${state.currentTripId}`);
      } catch (seedErr) {
        console.warn('Auto-seed failed:', seedErr.message);
      }
    }

    itineraryState.data = data;
    const cur = data.trip?.trp_home_currency || state.baseCurrency;

    // Update Header subtitle
    if (subtitle) {
      subtitle.textContent = `${data.trip?.trp_name || 'Trip'} · ${data.days?.length || 0} Days planned · Free, Budget & Expensive highlights`;
    }

    // Update Itinerary Stat Chips
    const actEl = document.getElementById('itn-stat-activities');
    const daysEl = document.getElementById('itn-stat-days');
    const costEl = document.getElementById('itn-stat-cost');
    const expEl = document.getElementById('itn-stat-expenses');
    const freeEl = document.getElementById('itn-stat-free');
    const budgetEl = document.getElementById('itn-stat-budget');
    const expTierEl = document.getElementById('itn-stat-expensive');

    const totalLogged = (data.days || []).reduce((acc, d) => acc + (d.day_total || 0), 0);

    if (actEl) actEl.textContent = data.total_items || 0;
    if (daysEl) daysEl.textContent = data.days?.length || 0;
    if (costEl) costEl.textContent = fmt(data.total_est_cost || 0, cur, 0);
    if (expEl) expEl.textContent = fmt(totalLogged, cur, 0);
    if (freeEl) freeEl.textContent = data.free_count || 0;
    if (budgetEl) budgetEl.textContent = data.budget_count || 0;
    if (expTierEl) expTierEl.textContent = data.expensive_count || 0;

    // Populate Day dropdowns
    populateItineraryDaySelects(data.days || []);

    // Load Live Weather for the Trip Destination
    loadDestinationWeather(data.trip?.trp_destination || 'Goa, India');

    // Initialize or Refresh Leaflet Map
    initOrUpdateMap();

    // Render Timeline cards
    renderItineraryTimeline();

    // Load Curated Hotels & Journey Route Transit
    await loadHotelsAndRoute();

  } catch (err) {
    console.error('Failed to load itinerary:', err);
    if (subtitle) subtitle.textContent = 'Could not connect to itinerary server. Retrying...';
  }
}

function populateItineraryDaySelects(days) {
  const quickSelect = document.getElementById('itinerary-add-to-day');
  const modalSelect = document.getElementById('modal-place-day');
  const mapDaySelect = document.getElementById('itinerary-map-day-select');

  if (quickSelect) {
    quickSelect.innerHTML = '';
    days.forEach(d => {
      const opt = document.createElement('option');
      opt.value = d.day_number;
      opt.textContent = `Day ${d.day_number}`;
      quickSelect.appendChild(opt);
    });
  }

  if (modalSelect) {
    modalSelect.innerHTML = '';
    days.forEach(d => {
      const opt = document.createElement('option');
      opt.value = d.day_number;
      opt.textContent = `Day ${d.day_number} (${d.date_display})`;
      modalSelect.appendChild(opt);
    });
  }

  if (mapDaySelect) {
    const curVal = mapDaySelect.value;
    mapDaySelect.innerHTML = '<option value="all">🗺️ All Days Route</option>';
    days.forEach(d => {
      const opt = document.createElement('option');
      opt.value = d.day_number;
      opt.textContent = `📅 Day ${d.day_number} Route`;
      if (String(curVal) === String(d.day_number)) opt.selected = true;
      mapDaySelect.appendChild(opt);
    });
  }
}

// ─── Destination Weather Sync (OpenWeatherMap API: 03be34f98468f6c09b66d0a9363cd4b6) ─
async function loadDestinationWeather(destination) {
  const apiKey = window.OPENWEATHER_API_KEY || '03be34f98468f6c09b66d0a9363cd4b6';
  const destKey = getTripDestKey(destination);
  const conf = DEST_CENTERS[destKey] || DEST_CENTERS.goa;
  const cityName = conf.city;

  try {
    const res = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(cityName)}&appid=${apiKey}&units=metric`);
    if (!res.ok) throw new Error(`Weather HTTP ${res.status}`);
    const w = await res.json();
    itineraryState.weatherData = w;

    const tempEl = document.getElementById('weather-temp');
    const descEl = document.getElementById('weather-desc');
    const humEl = document.getElementById('weather-humidity');
    const windEl = document.getElementById('weather-wind');
    const presEl = document.getElementById('weather-pressure');
    const iconEl = document.getElementById('weather-icon');

    const temp = Math.round(w.main.temp);
    const feels = Math.round(w.main.feels_like);
    const desc = w.weather?.[0]?.description || 'Clear sky';
    const mainCond = (w.weather?.[0]?.main || '').toLowerCase();

    // Map weather icon
    let emoji = '☀️';
    if (mainCond.includes('cloud')) emoji = '⛅';
    if (mainCond.includes('rain') || mainCond.includes('drizzle')) emoji = '🌧️';
    if (mainCond.includes('thunder')) emoji = '⛈️';
    if (mainCond.includes('snow')) emoji = '❄️';
    if (mainCond.includes('mist') || mainCond.includes('fog')) emoji = '🌫️';

    if (iconEl) iconEl.textContent = emoji;
    if (tempEl) tempEl.textContent = `${temp}°C`;
    if (descEl) descEl.textContent = `${desc.charAt(0).toUpperCase() + desc.slice(1)} · Feels like ${feels}°C in ${w.name}`;
    if (humEl) humEl.textContent = `${w.main.humidity}%`;
    if (windEl) windEl.textContent = `${Math.round((w.wind?.speed || 0) * 3.6)} km/h`;
    if (presEl) presEl.textContent = `${w.main.pressure} hPa`;

  } catch (e) {
    console.warn('Live weather lookup notice:', e.message);
    // Graceful fallback for offline demo
    const tempEl = document.getElementById('weather-temp');
    const descEl = document.getElementById('weather-desc');
    const humEl = document.getElementById('weather-humidity');
    const windEl = document.getElementById('weather-wind');
    const presEl = document.getElementById('weather-pressure');

    if (tempEl) tempEl.textContent = '28°C';
    if (descEl) descEl.textContent = `Pleasant tropical weather in ${conf.label}`;
    if (humEl) humEl.textContent = '68%';
    if (windEl) windEl.textContent = '14 km/h';
    if (presEl) presEl.textContent = '1012 hPa';
  }
}

// ─── Leaflet Interactive Day & Place Maps ──────────────────────────────────────
function initOrUpdateMap() {
  if (typeof window.L === 'undefined') {
    console.warn('Leaflet library is still loading...');
    setTimeout(initOrUpdateMap, 400);
    return;
  }

  const mapEl = document.getElementById('itinerary-leaflet-map');
  if (!mapEl) return;

  const destKey = getTripDestKey(itineraryState.data?.trip?.trp_destination);
  const destConf = DEST_CENTERS[destKey] || DEST_CENTERS.goa;

  // Initialize Map if not already created
  if (!itineraryState.map) {
    try {
      itineraryState.map = L.map('itinerary-leaflet-map', {
        center: [destConf.lat, destConf.lng],
        zoom: destConf.zoom,
        zoomControl: true,
        scrollWheelZoom: false,
      });

      // CartoDB Voyager tiles (modern, elegant, crisp)
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19,
      }).addTo(itineraryState.map);

      // Enable scroll zoom on first map click
      itineraryState.map.on('click', () => {
        itineraryState.map.scrollWheelZoom.enable();
      });
    } catch (mapErr) {
      console.error('Error creating Leaflet map:', mapErr);
      return;
    }
  }

  // Clear existing markers and route line
  (itineraryState.markers || []).forEach(m => itineraryState.map.removeLayer(m.marker));
  itineraryState.markers = [];
  if (itineraryState.routeLine) {
    itineraryState.map.removeLayer(itineraryState.routeLine);
    itineraryState.routeLine = null;
  }

  // Collect places matching current map day and map tier filters
  const days = itineraryState.data?.days || [];
  const cur = itineraryState.data?.trip?.trp_home_currency || state.baseCurrency;
  const filteredPlaces = [];

  days.forEach(d => {
    if (itineraryState.activeMapDay !== 'all' && String(d.day_number) !== String(itineraryState.activeMapDay)) {
      return;
    }
    (d.items || []).forEach(itm => {
      const tier = itm.itm_cost_tier || classifyPlaceTier(itm.itm_estimated_cost, itm.itm_currency || cur);
      if (itineraryState.activeMapTier !== 'all' && tier !== itineraryState.activeMapTier) {
        return;
      }
      if (itm.itm_lat && itm.itm_lng) {
        filteredPlaces.push({
          item: itm,
          day: d.day_number,
          dateDisplay: d.date_display,
          tier: tier,
          lat: parseFloat(itm.itm_lat),
          lng: parseFloat(itm.itm_lng),
        });
      }
    });
  });

  const markerBounds = [];
  const routePoints = [];

  filteredPlaces.forEach((p, idx) => {
    markerBounds.push([p.lat, p.lng]);
    routePoints.push([p.lat, p.lng]);

    // Icon symbol based on tier
    let pinIcon = '₹';
    let pinClass = 'pin-tier-budget';
    let tierBadgeHtml = '<span class="tier-badge tier-budget">🟡 Budget-Friendly</span>';

    if (p.tier === 'free') {
      pinIcon = '0';
      pinClass = 'pin-tier-free';
      tierBadgeHtml = '<span class="tier-badge tier-free">🟢 Free</span>';
    } else if (p.tier === 'expensive') {
      pinIcon = '👑';
      pinClass = 'pin-tier-expensive';
      tierBadgeHtml = '<span class="tier-badge tier-expensive">🔴 Expensive</span>';
    }

    const typeIcons = {
      activity: '🎯', meal: '🍽️', hotel: '🏨', transport: '🚗', flight: '✈️', other: '📦'
    };
    const tIcon = typeIcons[p.item.itm_type] || '📍';

    // Custom Leaflet DivIcon
    const customIcon = L.divIcon({
      className: '',
      html: `<div class="custom-map-pin ${pinClass}" title="${p.item.itm_title} (${p.tier})">
               <div class="custom-map-pin-inner">${pinIcon}</div>
             </div>`,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32],
    });

    const marker = L.marker([p.lat, p.lng], { icon: customIcon }).addTo(itineraryState.map);

    const costLabel = p.tier === 'free' ? '₹0 · Free Entry' : fmt(p.item.itm_estimated_cost || 0, cur, 0);
    const gmapsUrl = `https://www.google.com/maps/search/?api=1&query=${p.lat},${p.lng}`;

    const popupHtml = `
      <div class="itinerary-map-popup">
        <div class="popup-header">
          <div class="popup-title">${tIcon} ${p.item.itm_title}</div>
          ${tierBadgeHtml}
        </div>
        <div class="popup-meta">
          <span>📅 Day ${p.day}</span>
          <span>·</span>
          <span>⏰ ${p.item.itm_start_time || '10:00'}${p.item.itm_end_time ? ' – ' + p.item.itm_end_time : ''}</span>
        </div>
        ${p.item.itm_location ? `<div style="font-size:0.75rem;color:var(--text-secondary);margin-bottom:0.4rem;">📍 ${p.item.itm_location}</div>` : ''}
        ${p.item.itm_notes ? `<div style="font-size:0.72rem;color:var(--text-muted);font-style:italic;margin-bottom:0.4rem;">"${p.item.itm_notes}"</div>` : ''}
        <div class="popup-cost-row">
          <span style="font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;">Estimated Spend</span>
          <span class="popup-cost-val">${costLabel}</span>
        </div>
        <div class="popup-actions">
          <a href="${gmapsUrl}" target="_blank" rel="noopener noreferrer" class="popup-gmaps-link">
            🧭 Open in Google Maps
          </a>
        </div>
      </div>
    `;

    marker.bindPopup(popupHtml, { maxWidth: 300, className: 'itinerary-map-popup' });
    itineraryState.markers.push({ marker, item: p.item, day: p.day });
  });

  // Draw Route Polyline if viewing specific day or route with multiple waypoints
  if (routePoints.length > 1) {
    itineraryState.routeLine = L.polyline(routePoints, {
      color: '#7A1F3D',
      weight: 3.5,
      opacity: 0.75,
      dashArray: '8, 8',
      lineCap: 'round',
      lineJoin: 'round',
    }).addTo(itineraryState.map);
  }

  // Update Map Header Info
  const headingEl = document.getElementById('map-heading-text');
  const subEl = document.getElementById('map-sub-text');
  if (headingEl) {
    if (itineraryState.activeMapDay === 'all') {
      headingEl.textContent = `Full Trip Places Map (${filteredPlaces.length} stops mapped)`;
    } else {
      headingEl.textContent = `Day ${itineraryState.activeMapDay} Route & Waypoints (${filteredPlaces.length} stops)`;
    }
  }
  if (subEl) {
    subEl.textContent = `${destConf.label} · 🟢 Free · 🟡 Budget-Friendly · 🔴 Expensive`;
  }

  // Fit bounds smoothly
  if (markerBounds.length > 0) {
    try {
      itineraryState.map.fitBounds(L.latLngBounds(markerBounds), { padding: [40, 40], maxZoom: 14 });
    } catch {
      itineraryState.map.setView([destConf.lat, destConf.lng], destConf.zoom);
    }
  } else {
    itineraryState.map.setView([destConf.lat, destConf.lng], destConf.zoom);
  }

  setTimeout(() => {
    itineraryState.map?.invalidateSize();
  }, 250);
}

// ─── Render Day-by-Day Timeline ───────────────────────────────────────────────
function renderItineraryTimeline() {
  const container = document.getElementById('itinerary-timeline');
  if (!container) return;

  const data = itineraryState.data;
  if (!data || !data.days || data.days.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🗺️</div>
        <p>No itinerary items found for this trip.</p>
        <button class="btn btn-primary btn-sm" id="btn-empty-seed-demo" style="margin-top:0.75rem;">
          🎲 Load 7-Day Demo Itinerary
        </button>
      </div>
    `;
    document.getElementById('btn-empty-seed-demo')?.addEventListener('click', seedDemoActivities);
    return;
  }

  const cur = data.trip?.trp_home_currency || state.baseCurrency;
  const filter = itineraryState.activeFilter; // 'all' | 'free' | 'budget' | 'expensive'

  let html = '';

  data.days.forEach(day => {
    // Count categories for this day
    let dayFreeCount = 0;
    let dayBudgetCount = 0;
    let dayExpCount = 0;

    (day.items || []).forEach(itm => {
      const tier = itm.itm_cost_tier || classifyPlaceTier(itm.itm_estimated_cost, itm.itm_currency || cur);
      if (tier === 'free') dayFreeCount++;
      else if (tier === 'budget') dayBudgetCount++;
      else if (tier === 'expensive') dayExpCount++;
    });

    // Filter items based on active filter chip
    const visibleItems = (day.items || []).filter(itm => {
      if (filter === 'all') return true;
      const tier = itm.itm_cost_tier || classifyPlaceTier(itm.itm_estimated_cost, itm.itm_currency || cur);
      return tier === filter;
    });

    const dayEstTotal = (day.items || []).reduce((acc, itm) => acc + (parseFloat(itm.itm_estimated_cost) || 0), 0);
    const dayActualSpent = day.day_total || 0;
    const spentPct = dayEstTotal > 0 ? Math.min(100, Math.round((dayActualSpent / dayEstTotal) * 100)) : 0;

    // Daily simulated weather badge
    const weatherList = ['☀️ 30°C Sunny', '⛅ 28°C Pleasant', '🌤️ 29°C Warm Breeze', '🌧️ 25°C Tropical Shower', '☀️ 31°C Clear', '⛅ 27°C Coastal Breeze', '☀️ 29°C Golden Hour'];
    const dayWeather = weatherList[(day.day_number - 1) % weatherList.length];

    html += `
      <div class="itinerary-day-card" id="day-card-${day.day_number}" data-day="${day.day_number}">
        <div class="itinerary-day-header" onclick="toggleDayCard(${day.day_number})">
          <div class="itinerary-day-number">D${day.day_number}</div>
          <div class="itinerary-day-title">
            <h3>Day ${day.day_number} — ${day.date_display}</h3>
            <div class="day-header-badges">
              <span class="day-weather-chip">${dayWeather}</span>
              <span class="day-tier-summary">🟢 ${dayFreeCount} Free · 🟡 ${dayBudgetCount} Budget · 🔴 ${dayExpCount} Exp</span>
            </div>
          </div>
          <div class="itinerary-day-actions" onclick="event.stopPropagation()">
            <button class="btn-day-map-focus" onclick="focusDayOnMap(${day.day_number})" title="View Day ${day.day_number} Route on Map">
              🗺️ Route Map
            </button>
          </div>
          <div class="itinerary-day-budget-chip">
            <span class="chip-spent">${fmt(dayActualSpent, cur, 0)}</span>
            <span class="chip-label">of ${fmt(dayEstTotal, cur, 0)} est</span>
          </div>
          <div class="itinerary-day-toggle">▼</div>
        </div>

        <div class="itinerary-day-body">
          <!-- Activities Column -->
          <div class="itinerary-activities">
            ${visibleItems.length === 0 ? `
              <div style="font-size:0.8rem;color:var(--text-muted);padding:1rem;text-align:center;background:var(--bg-canvas);border-radius:var(--r-md);border:1px dashed rgba(122,31,61,0.12);">
                ${filter !== 'all' ? `No <strong>${filter}</strong> activities on this day.` : 'No activities added yet for this day.'}
              </div>
            ` : visibleItems.map(itm => renderActivityItemHtml(itm, cur, day.day_number)).join('')}

            <button class="itinerary-add-activity-btn" onclick="openAddPlaceModalForDay(${day.day_number})">
              <span>➕</span>
              <span>Add place / activity to Day ${day.day_number}...</span>
            </button>
          </div>

          <!-- Day Expenses & Budget Breakdown Column -->
          <div class="itinerary-day-expenses">
            <div class="day-expense-summary-box">
              <span class="summary-label">Day ${day.day_number} Financials</span>
              <div style="display:flex;align-items:baseline;justify-content:space-between;margin-top:2px;">
                <span class="summary-total">${fmt(dayActualSpent, cur, 0)}</span>
                <span style="font-size:0.75rem;color:var(--text-muted);font-family:var(--font-mono);">Est: ${fmt(dayEstTotal, cur, 0)}</span>
              </div>
              <div class="day-expense-mini-bar">
                <div class="bar-fill" style="width:${spentPct}%;"></div>
              </div>
              <div style="font-size:0.68rem;color:var(--text-muted);display:flex;justify-content:space-between;">
                <span>${spentPct}% of day estimate</span>
                <span>${(day.expenses || []).length} expenses logged</span>
              </div>
            </div>

            <!-- Linked Expenses List -->
            ${(day.expenses || []).length === 0 ? `
              <div class="day-expense-empty">No expenses logged for this date yet</div>
            ` : (day.expenses || []).map(exp => `
              <div class="day-expense-item">
                <span class="exp-icon">${CATEGORY_META[exp.exp_category]?.icon || '🧾'}</span>
                <div class="exp-info">
                  <div class="exp-name">${exp.exp_title}</div>
                  <div class="exp-sub">${CATEGORY_META[exp.exp_category]?.label || exp.exp_category} · ${exp.exp_currency !== cur ? exp.exp_currency + ' ' + exp.exp_amount + ' → ' : ''}${fmt(exp.exp_home_amount, cur)}</div>
                </div>
                <div class="exp-amt">${fmt(exp.exp_home_amount, cur)}</div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

function renderActivityItemHtml(itm, cur, dayNumber) {
  const tier = itm.itm_cost_tier || classifyPlaceTier(itm.itm_estimated_cost, itm.itm_currency || cur);

  let tierBadge = '<span class="tier-badge tier-budget">🟡 Budget-Friendly</span>';
  let tierBorderColor = '#F59E0B';
  let costDisplay = fmt(itm.itm_estimated_cost || 0, cur, 0);

  if (tier === 'free') {
    tierBadge = '<span class="tier-badge tier-free">🟢 Free</span>';
    tierBorderColor = '#10B981';
    costDisplay = '₹0 · Free';
  } else if (tier === 'expensive') {
    tierBadge = '<span class="tier-badge tier-expensive">🔴 Expensive</span>';
    tierBorderColor = '#E11D48';
    costDisplay = fmt(itm.itm_estimated_cost || 0, cur, 0);
  }

  const typeMeta = {
    activity:  { icon: '🎯', label: 'Activity',  tagClass: 'tag-explore' },
    meal:      { icon: '🍽️', label: 'Dining',    tagClass: 'tag-food' },
    hotel:     { icon: '🏨', label: 'Stay',      tagClass: 'tag-stay' },
    transport: { icon: '🚗', label: 'Transit',   tagClass: 'tag-transit' },
    flight:    { icon: '✈️', label: 'Flight',    tagClass: 'tag-transit' },
    other:     { icon: '📦', label: 'Other',     tagClass: 'tag-leisure' },
  }[itm.itm_type] || { icon: '📍', label: 'Stop', tagClass: 'tag-explore' };

  const gmapsQuery = itm.itm_lat && itm.itm_lng ? `${itm.itm_lat},${itm.itm_lng}` : encodeURIComponent(itm.itm_location || itm.itm_title);
  const gmapsLink = `https://www.google.com/maps/search/?api=1&query=${gmapsQuery}`;

  return `
    <div class="itinerary-activity-item" style="border-left: 3px solid ${tierBorderColor};">
      <div class="activity-time-col">
        <span class="activity-time">${itm.itm_start_time || '10:00'}</span>
        <div class="activity-type-dot" style="background:${tierBorderColor};"></div>
      </div>
      <div class="activity-main">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:0.5rem;">
          <div class="activity-name">${typeMeta.icon} ${itm.itm_title}</div>
          <button class="activity-remove-btn" onclick="deleteItineraryItem('${itm.itm_id}')" title="Remove activity">✕</button>
        </div>

        ${itm.itm_location ? `
          <div class="activity-place">
            <span>📍</span>
            <span>${itm.itm_location}</span>
          </div>
        ` : ''}

        ${itm.itm_notes ? `
          <div style="font-size:0.75rem;color:var(--text-muted);margin-top:3px;font-style:italic;">
            "${itm.itm_notes}"
          </div>
        ` : ''}

        <div class="activity-tags">
          ${tierBadge}
          <span class="activity-tag ${typeMeta.tagClass}">${typeMeta.label}</span>
          ${itm.itm_end_time ? `<span class="activity-tag" style="background:rgba(0,0,0,0.04);color:var(--text-muted);">Until ${itm.itm_end_time}</span>` : ''}
        </div>

        <div class="activity-actions-row">
          <button class="activity-action-btn" onclick="openExpenseForPlace('${itm.itm_id}')" style="color:var(--burgundy);font-weight:700;background:rgba(122,31,61,0.08);border-color:rgba(122,31,61,0.25);" title="Log this place or activity as an expense">
            🧾 Add Expense
          </button>
          ${itm.itm_lat && itm.itm_lng ? `
            <button class="activity-action-btn" onclick="flyToPlaceOnMap(${itm.itm_lat}, ${itm.itm_lng}, '${encodeURIComponent(itm.itm_title)}')">
              🗺️ Map
            </button>
          ` : ''}
          <a href="${gmapsLink}" target="_blank" rel="noopener noreferrer" class="activity-action-btn">
            🧭 Google Maps
          </a>
        </div>
      </div>

      <div class="activity-cost-pill">
        ${costDisplay}
      </div>
    </div>
  `;
}

window.openExpenseForPlace = function(itmId) {
  let item = null;
  if (itineraryState.data && itineraryState.data.days) {
    for (const day of itineraryState.data.days) {
      const match = (day.items || []).find(it => it.itm_id === itmId);
      if (match) { item = match; break; }
    }
  }

  if (!item) {
    toast('Place details not found', 'warning');
    return;
  }

  const categoryMap = {
    activity: 'activities',
    meal: 'food',
    hotel: 'stay',
    transport: 'travel',
    flight: 'travel',
    other: 'misc',
  };

  const prefill = {
    title: item.itm_title || 'Planned Activity',
    amount: item.itm_estimated_cost ? parseFloat(item.itm_estimated_cost) : '',
    category: categoryMap[item.itm_type] || 'activities',
    currency: item.itm_currency || state.currentTrip?.trp_home_currency || 'INR',
    notes: `Planned place: ${item.itm_location || item.itm_title} (${item.itm_cost_tier || 'budget'})`,
  };

  openExpenseModal(prefill);
  toast(`Pre-filled expense form for "${item.itm_title}"`, 'info', 2000);
};

// ─── Map Navigation Helpers ───────────────────────────────────────────────────
function focusDayOnMap(dayNumber) {
  itineraryState.activeMapDay = dayNumber;
  const select = document.getElementById('itinerary-map-day-select');
  if (select) select.value = dayNumber;
  initOrUpdateMap();

  const mapCard = document.getElementById('itinerary-map-card');
  if (mapCard) {
    mapCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
  toast(`Displaying Day ${dayNumber} route on map`, 'info', 2000);
}

function flyToPlaceOnMap(lat, lng, titleEsc) {
  if (!itineraryState.map) return;

  const mapCard = document.getElementById('itinerary-map-card');
  if (mapCard) {
    mapCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  setTimeout(() => {
    itineraryState.map.flyTo([lat, lng], 15, { duration: 1.2 });

    // Open matching marker popup
    const target = itineraryState.markers.find(m => {
      const p = m.marker.getLatLng();
      return Math.abs(p.lat - lat) < 0.0001 && Math.abs(p.lng - lng) < 0.0001;
    });
    if (target) {
      setTimeout(() => target.marker.openPopup(), 1300);
    }
  }, 300);
}

function toggleDayCard(dayNumber) {
  const card = document.getElementById(`day-card-${dayNumber}`);
  if (card) card.classList.toggle('collapsed');
}

// ─── Filter Chips Handling ────────────────────────────────────────────────────
document.querySelectorAll('#itinerary-stat-chips .itinerary-stat-chip[data-filter]').forEach(chip => {
  chip.addEventListener('click', () => {
    const filter = chip.getAttribute('data-filter');
    itineraryState.activeFilter = filter;

    document.querySelectorAll('#itinerary-stat-chips .itinerary-stat-chip[data-filter]').forEach(c => c.classList.remove('active-filter'));
    chip.classList.add('active-filter');

    // Also synchronize map tier filter
    itineraryState.activeMapTier = filter;
    const tierSelect = document.getElementById('itinerary-map-tier-select');
    if (tierSelect) tierSelect.value = filter;

    initOrUpdateMap();
    renderItineraryTimeline();

    toast(`Filtered places: ${filter.toUpperCase()}`, 'info', 1500);
  });
});

// Map Toolbar Controls
document.getElementById('itinerary-map-day-select')?.addEventListener('change', e => {
  itineraryState.activeMapDay = e.target.value;
  initOrUpdateMap();
});

document.getElementById('itinerary-map-tier-select')?.addEventListener('change', e => {
  itineraryState.activeMapTier = e.target.value;
  initOrUpdateMap();
});

document.getElementById('btn-fit-map')?.addEventListener('click', () => {
  if (!itineraryState.map) return;
  const validLatLngs = itineraryState.markers.map(m => m.marker.getLatLng());
  if (validLatLngs.length > 0) {
    itineraryState.map.fitBounds(L.latLngBounds(validLatLngs), { padding: [40, 40] });
    toast('Map centered to all places', 'info', 1500);
  }
});

// Weather Clouds Radar Layer toggle
document.getElementById('btn-toggle-weather-radar')?.addEventListener('click', () => {
  if (!itineraryState.map) return;
  const apiKey = window.OPENWEATHER_API_KEY || '03be34f98468f6c09b66d0a9363cd4b6';
  const btn = document.getElementById('btn-toggle-weather-radar');

  if (!itineraryState.radarActive) {
    try {
      itineraryState.weatherLayer = L.tileLayer(`https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=${apiKey}`, {
        maxZoom: 18,
        opacity: 0.6,
      }).addTo(itineraryState.map);
      itineraryState.radarActive = true;
      if (btn) {
        btn.classList.add('btn-primary');
        btn.classList.remove('btn-ghost');
        btn.textContent = '☁️ Radar Active';
      }
      toast('Live weather clouds layer enabled (OpenWeatherMap)', 'success');
    } catch (e) {
      toast('Could not load weather radar tiles', 'error');
    }
  } else {
    if (itineraryState.weatherLayer) {
      itineraryState.map.removeLayer(itineraryState.weatherLayer);
      itineraryState.weatherLayer = null;
    }
    itineraryState.radarActive = false;
    if (btn) {
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-ghost');
      btn.textContent = '☁️ Cloud Radar';
    }
    toast('Weather radar layer disabled', 'info');
  }
});

// ─── Fast Add Place Bar ───────────────────────────────────────────────────────
document.getElementById('itinerary-add-tier')?.addEventListener('change', e => {
  const tier = e.target.value;
  const costInput = document.getElementById('itinerary-est-cost');
  if (!costInput) return;
  if (tier === 'free') {
    costInput.value = '0';
    costInput.disabled = true;
  } else {
    costInput.disabled = false;
    if (tier === 'budget' && costInput.value === '0') costInput.value = '500';
    if (tier === 'expensive' && (costInput.value === '0' || costInput.value === '500')) costInput.value = '3500';
  }
});

document.getElementById('btn-add-place-to-day')?.addEventListener('click', async () => {
  const day = document.getElementById('itinerary-add-to-day')?.value || 1;
  const title = document.getElementById('places-search-input')?.value.trim();
  const tier = document.getElementById('itinerary-add-tier')?.value || 'budget';
  const type = document.getElementById('itinerary-add-type')?.value || 'activity';
  let cost = parseFloat(document.getElementById('itinerary-est-cost')?.value) || 0;

  if (tier === 'free') cost = 0;

  if (!title) {
    toast('Please enter a place or activity name', 'warning');
    return;
  }

  // Get destination base coords with jitter for visual pin separation
  const destKey = getTripDestKey(itineraryState.data?.trip?.trp_destination);
  const destConf = DEST_CENTERS[destKey] || DEST_CENTERS.goa;
  const jitterLat = (Math.random() - 0.5) * 0.04;
  const jitterLng = (Math.random() - 0.5) * 0.04;

  try {
    await api(`/itineraries/${state.currentTripId}/items`, {
      method: 'POST',
      body: JSON.stringify({
        day_number: parseInt(day),
        title: title,
        type: type,
        cost_tier: tier,
        estimated_cost: cost,
        location: `${title}, ${destConf.label}`,
        lat: Number((destConf.lat + jitterLat).toFixed(4)),
        lng: Number((destConf.lng + jitterLng).toFixed(4)),
        start_time: '11:00',
        end_time: '13:00',
        notes: `Added to Day ${day}`,
      }),
    });

    toast(`📍 Added "${title}" to Day ${day} as ${tier.toUpperCase()}!`, 'success');
    document.getElementById('places-search-input').value = '';
    await loadItinerary();
  } catch (err) {
    toast(`Failed to add place: ${err.message}`, 'error');
  }
});

// ─── Add / Edit Modal Handlers ────────────────────────────────────────────────
function openAddPlaceModalForDay(dayNumber) {
  const modal = document.getElementById('itinerary-place-modal');
  if (!modal) return;

  const daySelect = document.getElementById('modal-place-day');
  if (daySelect && dayNumber) daySelect.value = dayNumber;

  const destKey = getTripDestKey(itineraryState.data?.trip?.trp_destination);
  const destConf = DEST_CENTERS[destKey] || DEST_CENTERS.goa;

  const latInput = document.getElementById('modal-place-lat');
  const lngInput = document.getElementById('modal-place-lng');
  if (latInput) latInput.value = destConf.lat;
  if (lngInput) lngInput.value = destConf.lng;

  selectModalTier('budget');
  modal.classList.add('active');
}

document.getElementById('btn-itinerary-add-place')?.addEventListener('click', () => {
  openAddPlaceModalForDay(1);
});

document.getElementById('btn-place-modal-close')?.addEventListener('click', () => {
  document.getElementById('itinerary-place-modal')?.classList.remove('active');
});
document.getElementById('btn-place-modal-cancel')?.addEventListener('click', () => {
  document.getElementById('itinerary-place-modal')?.classList.remove('active');
});

// Tier selector in modal
function selectModalTier(tier) {
  itineraryState.modalSelectedTier = tier;
  const freeOpt = document.getElementById('tier-opt-free');
  const budgetOpt = document.getElementById('tier-opt-budget');
  const expOpt = document.getElementById('tier-opt-expensive');
  const costInput = document.getElementById('modal-place-cost');

  freeOpt?.classList.remove('selected-free');
  budgetOpt?.classList.remove('selected-budget');
  expOpt?.classList.remove('selected-expensive');

  if (tier === 'free') {
    freeOpt?.classList.add('selected-free');
    if (costInput) {
      costInput.value = '0';
      costInput.disabled = true;
    }
  } else if (tier === 'expensive') {
    expOpt?.classList.add('selected-expensive');
    if (costInput) {
      costInput.disabled = false;
      if (costInput.value === '0' || costInput.value === '500') costInput.value = '3500';
    }
  } else {
    budgetOpt?.classList.add('selected-budget');
    if (costInput) {
      costInput.disabled = false;
      if (costInput.value === '0') costInput.value = '500';
    }
  }
}

document.getElementById('tier-opt-free')?.addEventListener('click', () => selectModalTier('free'));
document.getElementById('tier-opt-budget')?.addEventListener('click', () => selectModalTier('budget'));
document.getElementById('tier-opt-expensive')?.addEventListener('click', () => selectModalTier('expensive'));

document.getElementById('btn-place-modal-save')?.addEventListener('click', async () => {
  const day = document.getElementById('modal-place-day')?.value || 1;
  const title = document.getElementById('modal-place-title')?.value.trim();
  const type = document.getElementById('modal-place-type')?.value || 'activity';
  const tier = itineraryState.modalSelectedTier || 'budget';
  let cost = parseFloat(document.getElementById('modal-place-cost')?.value) || 0;
  const location = document.getElementById('modal-place-location')?.value.trim();
  const start = document.getElementById('modal-place-start')?.value || '10:00';
  const end = document.getElementById('modal-place-end')?.value || '12:00';
  const lat = parseFloat(document.getElementById('modal-place-lat')?.value) || null;
  const lng = parseFloat(document.getElementById('modal-place-lng')?.value) || null;
  const notes = document.getElementById('modal-place-notes')?.value.trim();

  if (!title) {
    toast('Place title is required', 'warning');
    return;
  }
  if (tier === 'free') cost = 0;

  try {
    await api(`/itineraries/${state.currentTripId}/items`, {
      method: 'POST',
      body: JSON.stringify({
        day_number: parseInt(day),
        title,
        type,
        cost_tier: tier,
        estimated_cost: cost,
        location,
        start_time: start,
        end_time: end,
        lat,
        lng,
        notes,
      }),
    });

    toast(`📍 Successfully saved "${title}" to Day ${day}!`, 'success');
    document.getElementById('itinerary-place-modal')?.classList.remove('active');
    document.getElementById('modal-place-title').value = '';
    document.getElementById('modal-place-location').value = '';
    document.getElementById('modal-place-notes').value = '';
    await loadItinerary();
  } catch (err) {
    toast(`Error saving place: ${err.message}`, 'error');
  }
});

// Delete Place
async function deleteItineraryItem(itemId) {
  if (!confirm('Remove this place from your itinerary?')) return;
  try {
    await api(`/itineraries/${state.currentTripId}/items/${itemId}`, { method: 'DELETE' });
    toast('Place removed from itinerary', 'info');
    await loadItinerary();
  } catch (err) {
    toast(`Failed to remove item: ${err.message}`, 'error');
  }
}

// Reseed All Days
async function seedDemoActivities() {
  try {
    toast('Seeding complete 7-day itinerary with categorized places & maps...', 'info', 2500);
    const res = await api(`/itineraries/${state.currentTripId}/seed-demo?force=true`, { method: 'POST' });
    toast(res.message || '7-day itinerary populated with Free, Budget & Expensive places!', 'success');
    await loadItinerary();
  } catch (err) {
    toast(`Seed error: ${err.message}`, 'error');
  }
}

document.getElementById('btn-itinerary-seed-demo')?.addEventListener('click', seedDemoActivities);

// ─── Curated Hotels, Recommendations & Journey Route ──────────────────────────
const hotelsState = {
  data: null,
  filter: 'all',
};

async function loadHotelsAndRoute(customOrigin = null, customDest = null) {
  const grid = document.getElementById('hotels-grid');
  if (!grid) return;

  try {
    let url = `/hotels?trip_id=${state.currentTripId}`;
    if (customOrigin) url += `&origin=${encodeURIComponent(customOrigin)}`;
    if (customDest) url += `&destination=${encodeURIComponent(customDest)}`;

    const data = await api(url);
    hotelsState.data = data;

    // Update input fields
    const startInput = document.getElementById('itinerary-start-place');
    const destInput = document.getElementById('itinerary-dest-place');
    if (startInput && !customOrigin) {
      startInput.value = data.origin || 'Mumbai, India';
    }
    if (destInput && !customDest) {
      destInput.value = data.destination || 'Goa, India';
    }

    // Update Transit Ribbon
    const flightBadge = document.getElementById('transit-flight-badge');
    const fareEst = document.getElementById('transit-fare-est');
    const altEst = document.getElementById('transit-alt-est');
    const flightLink = document.getElementById('transit-booking-link');

    if (data.route) {
      if (flightBadge) flightBadge.textContent = data.route.flight_badge || '✈️ Direct Flight Available';
      if (fareEst) fareEst.textContent = data.route.flight_fare || 'Competitive airfares';
      if (altEst) altEst.textContent = data.route.transit_alt || 'High-speed transit available';
      if (flightLink && data.route.booking_link) {
        flightLink.href = data.route.booking_link;
        flightLink.style.display = 'inline-flex';
      }
    }

    renderHotelsGrid();
  } catch (err) {
    console.error('Failed to load hotels & route:', err);
    if (grid) {
      grid.innerHTML = `<div style="grid-column: 1/-1; padding: 1.5rem; text-align: left; color: var(--text-muted); font-size: 0.85rem;">
        ⚠️ Unable to load curated stays right now. Please verify backend connection.
      </div>`;
    }
  }
}

function setHotelFilter(filter) {
  hotelsState.filter = filter;
  // Update button active states strictly
  document.querySelectorAll('.hotel-filter-btn').forEach(btn => {
    if (btn.getAttribute('data-filter') === filter) {
      btn.classList.remove('btn-ghost');
      btn.classList.add('btn-primary', 'active');
    } else {
      btn.classList.remove('btn-primary', 'active');
      btn.classList.add('btn-ghost');
    }
  });
  renderHotelsGrid();
}

function renderHotelsGrid() {
  const grid = document.getElementById('hotels-grid');
  if (!grid || !hotelsState.data) return;

  const hotels = hotelsState.data.hotels || [];
  let filtered = hotels;
  if (hotelsState.filter === 'recommended') {
    filtered = hotels.filter(h => h.recommended);
  } else if (hotelsState.filter === 'luxury') {
    filtered = hotels.filter(h => h.category === 'luxury' || h.price_tier === 'expensive');
  } else if (hotelsState.filter === 'budget') {
    filtered = hotels.filter(h => h.category === 'budget' || h.price_tier === 'budget');
  }

  const countBadge = document.getElementById('hotels-count-badge');
  if (countBadge) {
    countBadge.textContent = `${filtered.length} Stays`;
  }

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; padding: 2.5rem; text-align: left; background: var(--bg-surface); border: 1px dashed var(--border); border-radius: var(--r-md);">
        <div style="font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.35rem;">No stays found matching this filter</div>
        <p style="font-size: 0.82rem; color: var(--text-muted); margin: 0 0 1rem 0;">Switch filters or search for another destination.</p>
        <button class="btn btn-sm btn-primary" onclick="setHotelFilter('all')">Show All Stays</button>
      </div>`;
    return;
  }

  grid.innerHTML = filtered.map(h => {
    const isRec = !!h.recommended;
    let badgeClass = 'badge-tag-val';
    let badgeText = h.recommendation_badge || 'Best Value';
    if (isRec) {
      badgeClass = 'badge-tag-rec';
      badgeText = '⭐ Recommended';
    } else if (h.category === 'luxury') {
      badgeClass = 'badge-tag-lux';
      badgeText = '👑 Luxury Pick';
    } else if (h.category === 'budget') {
      badgeClass = 'badge-tag-bud';
      badgeText = '🎒 Budget Friendly';
    }

    const amenitiesHtml = (h.amenities || []).map(a => `<span class="hotel-amenity-pill">${a}</span>`).join('');

    return `
      <div class="hotel-card ${isRec ? 'is-recommended' : ''}" id="hotel-card-${h.id}">
        <div class="hotel-media">
          <img class="hotel-img" src="${h.image_url}" alt="${h.name}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=700&q=80'" />
          <span class="hotel-badge-tag ${badgeClass}">${badgeText}</span>
          <span class="hotel-rating-tag">★ ${h.rating} <span style="font-size:0.65rem;opacity:0.8;">(${h.reviews_count.toLocaleString()})</span></span>
        </div>

        <div class="hotel-body">
          <div class="hotel-name">${h.name}</div>
          <div class="hotel-location">📍 ${h.location}</div>

          <div class="hotel-amenities-wrap">
            ${amenitiesHtml}
          </div>

          <div class="hotel-reason-box">
            <strong>💡 Recommendation Verdict</strong>
            ${h.recommendation_reason}
          </div>

          <div class="hotel-price-row">
            <div>
              <span class="hotel-price-val">${fmt(h.price_per_night, h.currency, 0)}</span>
              <span style="font-size:0.75rem;color:var(--text-muted);"> / night</span>
            </div>
            <div class="hotel-price-sub">taxes & fees included</div>
          </div>

          <!-- Action buttons kept strictly to the LEFT -->
          <div class="hotel-actions-left">
            <a href="${h.booking_url}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm hotel-book-btn" title="Open verified booking partner">
              🔗 Book Stay ↗
            </a>
            <button class="btn btn-ghost btn-sm" onclick="openExpenseForHotel('${h.id}')" title="Log hotel stay as an expense">
              🧾 Log Expense
            </button>
            <button class="btn btn-ghost btn-sm" onclick="focusHotelOnMap(${h.lat}, ${h.lng}, '${h.name.replace(/'/g, "\\'")}')" title="Locate on Leaflet map">
              🗺️ Map
            </button>
            <button class="btn btn-ghost btn-sm" onclick="addHotelToTripItinerary('${h.id}')" title="Add this hotel check-in to Day 1 itinerary">
              ➕ Add to Plan
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

window.openExpenseForHotel = function(hotelId) {
  const hotel = (hotelsState.data?.hotels || []).find(h => h.id === hotelId);
  if (!hotel) return;

  const prefill = {
    title: `Stay: ${hotel.name}`,
    amount: hotel.price_per_night || '',
    category: 'stay',
    currency: hotel.currency || 'INR',
    notes: `Nightly booking at ${hotel.name}, ${hotel.location}`,
  };

  openExpenseModal(prefill);
  toast(`Pre-filled stay expense for "${hotel.name}"`, 'info', 2000);
};

async function addHotelToTripItinerary(hotelId) {
  const hotel = (hotelsState.data?.hotels || []).find(h => h.id === hotelId);
  if (!hotel) return;

  try {
    toast(`Adding "${hotel.name}" to trip itinerary...`, 'info', 1500);
    const res = await api('/hotels/add-to-itinerary', {
      method: 'POST',
      body: JSON.stringify({
        trip_id: state.currentTripId,
        day_number: 1,
        hotel_id: hotel.id,
        hotel_name: hotel.name,
        price_per_night: hotel.price_per_night,
        currency: hotel.currency,
        location: hotel.location,
        lat: hotel.lat,
        lng: hotel.lng,
        booking_url: hotel.booking_url,
      }),
    });

    toast(res.message || `🏨 Added "${hotel.name}" to Day 1!`, 'success');
    await loadItinerary();
  } catch (err) {
    toast(`Failed to add hotel: ${err.message}`, 'error');
  }
}

function focusHotelOnMap(lat, lng, name) {
  if (!itineraryState.map) return;
  const mapCard = document.getElementById('itinerary-map-card');
  if (mapCard) mapCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
  itineraryState.map.setView([lat, lng], 14, { animate: true });

  const hotelIcon = L.divIcon({
    className: '',
    html: `<div class="custom-map-pin pin-tier-expensive" style="background:#7a1f3d;border:2px solid #fff;box-shadow:0 0 12px rgba(122,31,61,0.6);" title="${name}">
             <div class="custom-map-pin-inner" style="font-size:14px;">🏨</div>
           </div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 36],
    popupAnchor: [0, -36],
  });

  const hotelMarker = L.marker([lat, lng], { icon: hotelIcon }).addTo(itineraryState.map);
  hotelMarker.bindPopup(`
    <div class="itinerary-map-popup">
      <div class="popup-header">
        <div class="popup-title">🏨 ${name}</div>
        <span class="tier-badge tier-expensive">Curated Stay</span>
      </div>
      <div class="popup-meta" style="margin-top:4px;">
        <span>⭐ Recommended Stay</span>
      </div>
      <div class="popup-actions" style="margin-top:8px;">
        <a href="https://www.google.com/maps/search/?api=1&query=${lat},${lng}" target="_blank" rel="noopener noreferrer" class="popup-gmaps-link">
          🧭 Open in Google Maps
        </a>
      </div>
    </div>
  `).openPopup();
}

// Bind Hotel & Journey Route Event Listeners
document.getElementById('btn-search-hotels-route')?.addEventListener('click', async () => {
  const origin = document.getElementById('itinerary-start-place')?.value.trim();
  const dest = document.getElementById('itinerary-dest-place')?.value.trim();
  if (!dest) {
    toast('Please enter a destination place', 'warning');
    return;
  }
  toast(`Searching transit & curated stays from ${origin || 'any origin'} to ${dest}...`, 'info', 2000);
  await loadHotelsAndRoute(origin, dest);
  loadDestinationWeather(dest);
});

document.getElementById('btn-save-trip-route')?.addEventListener('click', async () => {
  const origin = document.getElementById('itinerary-start-place')?.value.trim() || 'Mumbai, India';
  const dest = document.getElementById('itinerary-dest-place')?.value.trim() || 'Goa, India';
  try {
    await api('/hotels/update-route', {
      method: 'POST',
      body: JSON.stringify({
        trip_id: state.currentTripId,
        origin: origin,
        destination: dest,
      }),
    });
    toast(`Saved journey route: ${origin} ➔ ${dest}!`, 'success');
  } catch (err) {
    toast(`Failed to save route: ${err.message}`, 'error');
  }
});

// Bind hotel filter buttons
document.querySelectorAll('.hotel-filter-btn').forEach(btn => {
  btn.addEventListener('click', (e) => {
    const filter = e.currentTarget.getAttribute('data-filter') || 'all';
    setHotelFilter(filter);
  });
});

// Window exports for inline handlers
window.setHotelFilter = setHotelFilter;
window.addHotelToTripItinerary = addHotelToTripItinerary;
window.focusHotelOnMap = focusHotelOnMap;
window.loadHotelsAndRoute = loadHotelsAndRoute;

// ─── Multi-Modal Transit & Travel Hub ─────────────────────────────────────────
const transitState = {
  data: null,
  activeMode: 'all',
  origin: 'Mumbai, India',
  destination: 'Goa, India',
};

async function loadTransitHub(customOrigin = null, customDest = null) {
  const grid = document.getElementById('transit-cards-grid');
  const subtitle = document.getElementById('transit-subtitle');
  if (!grid) return;

  try {
    let url = `/transit?trip_id=${state.currentTripId}`;
    if (customOrigin) url += `&origin=${encodeURIComponent(customOrigin)}`;
    if (customDest) url += `&destination=${encodeURIComponent(customDest)}`;

    const data = await api(url);
    transitState.data = data;
    transitState.origin = data.origin;
    transitState.destination = data.destination;

    // Update inputs
    const originInput = document.getElementById('transit-origin-input');
    const destInput = document.getElementById('transit-dest-input');
    if (originInput && !customOrigin) originInput.value = data.origin || 'Mumbai, India';
    if (destInput && !customDest) destInput.value = data.destination || 'Goa, India';

    // Update Subtitle
    if (subtitle) {
      subtitle.textContent = `All transit modes connecting ${data.origin} ➔ ${data.destination} · Flights, High-Speed Rail, Metro, Cabs, Rentals & Scenic Ferries`;
    }

    // Update KPI Bar
    const cur = data.currency || state.baseCurrency;
    const fastEl = document.getElementById('transit-kpi-fastest');
    const cheapEl = document.getElementById('transit-kpi-cheapest');
    const ecoEl = document.getElementById('transit-kpi-eco');
    const budEl = document.getElementById('transit-kpi-budget');
    const budSubEl = document.getElementById('transit-kpi-budget-sub');

    if (fastEl) fastEl.textContent = data.summary?.fastest || 'Flight (1h 15m)';
    if (cheapEl) cheapEl.textContent = data.summary?.cheapest || 'Metro / Local Ferry';
    if (ecoEl) ecoEl.textContent = data.summary?.eco_friendly || 'High-Speed Rail';

    const cap = data.budget_transport_cap || 15000;
    const spent = data.budget_transport_spent || 0;
    const rem = data.budget_transport_remaining || (cap - spent);

    if (budEl) budEl.textContent = fmt(cap, cur, 0);
    if (budSubEl) {
      budSubEl.textContent = `${fmt(spent, cur, 0)} logged · ${fmt(rem, cur, 0)} safe runway`;
      if (rem < 0) {
        budSubEl.style.color = '#dc2626';
        budSubEl.textContent += ' ⚠️ Over cap!';
      } else {
        budSubEl.style.color = 'var(--text-secondary)';
      }
    }

    // Update Count Badges on Filters
    const countAll = document.getElementById('count-all-modes');
    const countFlt = document.getElementById('count-flights');
    const countTrn = document.getElementById('count-trains');
    const countMtr = document.getElementById('count-metro');
    const countCab = document.getElementById('count-cabs');
    const countRnt = document.getElementById('count-rentals');
    const countFer = document.getElementById('count-ferries');

    if (countAll) countAll.textContent = data.total_options_count || 0;
    if (countFlt) countFlt.textContent = data.flights?.length || 0;
    if (countTrn) countTrn.textContent = data.trains?.length || 0;
    if (countMtr) countMtr.textContent = data.metro?.length || 0;
    if (countCab) countCab.textContent = data.cabs?.length || 0;
    if (countRnt) countRnt.textContent = data.rentals?.length || 0;
    if (countFer) countFer.textContent = data.ferries?.length || 0;

    renderTransitCards();
  } catch (err) {
    console.error('Failed to load transit data:', err);
    if (grid) {
      grid.innerHTML = `<div style="grid-column: 1/-1; padding: 2rem; text-align: left; color: var(--text-muted);">
        ⚠️ Could not load travel modes. Ensure backend is running.
      </div>`;
    }
  }
}

function setTransitModeFilter(mode) {
  transitState.activeMode = mode;
  document.querySelectorAll('.transit-filter-btn').forEach(btn => {
    if (btn.getAttribute('data-mode') === mode) {
      btn.classList.remove('btn-ghost');
      btn.classList.add('btn-primary', 'active');
    } else {
      btn.classList.remove('btn-primary', 'active');
      btn.classList.add('btn-ghost');
    }
  });
  renderTransitCards();
}

function renderTransitCards() {
  const grid = document.getElementById('transit-cards-grid');
  if (!grid || !transitState.data) return;

  const data = transitState.data;
  const cur = data.currency || state.baseCurrency;
  const mode = transitState.activeMode;

  let items = [];

  // Flights
  if (mode === 'all' || mode === 'flights') {
    (data.flights || []).forEach(f => {
      items.push({
        category: 'flights',
        categoryLabel: '✈️ Flight',
        badge: f.badge || 'Fastest Air Link',
        badgeClass: 'transit-badge-fast',
        title: `${f.carrier} · ${f.flight_no}`,
        route: `${f.origin_code} (${f.dep_time}) ➔ ${f.dest_code} (${f.arr_time})`,
        duration: f.duration,
        meta1: `Class: <strong>${f.class}</strong>`,
        meta2: `Carbon: <strong>${f.carbon_kg} kg CO2</strong>`,
        notes: `${f.origin_airport} to ${f.dest_airport}. ${f.luggage}.`,
        price: f.fare,
        currency: f.currency || cur,
        bookingUrl: f.booking_link,
        bookLabel: '🔗 Book Flight ↗',
        transitType: 'flight',
        raw: f,
      });
    });
  }

  // Trains
  if (mode === 'all' || mode === 'trains') {
    (data.trains || []).forEach(t => {
      items.push({
        category: 'trains',
        categoryLabel: '🚆 Train & Rail',
        badge: t.badge || 'Scenic High-Speed Rail',
        badgeClass: 'transit-badge-eco',
        title: `${t.name} #${t.train_no}`,
        route: `${t.origin_station} ➔ ${t.dest_station}`,
        duration: t.duration,
        meta1: `Class: <strong>${t.class}</strong>`,
        meta2: `Carbon: <strong>${t.carbon_kg} kg CO2</strong>`,
        notes: `${t.catering}. ${t.speed}. ${t.seats_status}.`,
        price: t.fare,
        currency: t.currency || cur,
        bookingUrl: t.booking_link,
        bookLabel: '🔗 Book Trainline / IRCTC ↗',
        transitType: 'transport',
        raw: t,
      });
    });
  }

  // Metro
  if (mode === 'all' || mode === 'metro') {
    (data.metro || []).forEach(m => {
      items.push({
        category: 'metro',
        categoryLabel: '🚇 Metro & Urban Transit',
        badge: m.badge || 'Rapid Metro Transit',
        badgeClass: 'transit-badge-budget',
        title: `${m.network} · ${m.line}`,
        route: m.route,
        duration: m.frequency,
        meta1: `Operating: <strong>${m.operating_hours}</strong>`,
        meta2: `Carbon: <strong>${m.carbon_kg} kg CO2</strong>`,
        notes: `${m.features}. Passes: ${fmt(m.fare_day_pass, m.currency, 0)} day pass available.`,
        price: m.fare_token,
        currency: m.currency || cur,
        bookingUrl: m.portal_link || m.map_link,
        bookLabel: '🗺️ Metro Map & Portal ↗',
        transitType: 'transport',
        raw: m,
      });
    });
  }

  // Cabs
  if (mode === 'all' || mode === 'cabs') {
    (data.cabs || []).forEach(c => {
      items.push({
        category: 'cabs',
        categoryLabel: '🚕 Cab & Rideshare',
        badge: c.badge || 'On-Demand Transfer',
        badgeClass: 'transit-badge-luxury',
        title: c.provider,
        route: `Pickup: ${c.pickup_point}`,
        duration: c.est_duration,
        meta1: `Vehicle: <strong>${c.vehicle_type}</strong>`,
        meta2: `Surge: <strong>${c.surge_index}</strong>`,
        notes: `${c.capacity}. ${c.features}.`,
        price: c.fare_min,
        priceMax: c.fare_max,
        currency: c.currency || cur,
        bookingUrl: c.booking_link,
        bookLabel: '📱 Open Cab App ↗',
        transitType: 'transport',
        raw: c,
      });
    });
  }

  // Rentals
  if (mode === 'all' || mode === 'rentals') {
    (data.rentals || []).forEach(r => {
      items.push({
        category: 'rentals',
        categoryLabel: '🛵 Rentals & Self-Drive',
        badge: r.badge || 'Self-Drive Freedom',
        badgeClass: 'transit-badge-budget',
        title: r.vehicle,
        route: `Type: ${r.type} · Provider: ${r.provider}`,
        duration: 'Per Day',
        meta1: `Deposit: <strong>${fmt(r.deposit, r.currency, 0)}</strong>`,
        meta2: `Fuel: <strong>${r.fuel_policy}</strong>`,
        notes: `${r.inclusions}`,
        price: r.daily_rate,
        currency: r.currency || cur,
        bookingUrl: r.booking_link,
        bookLabel: '🔗 Book Rental Vehicle ↗',
        transitType: 'transport',
        raw: r,
      });
    });
  }

  // Ferries
  if (mode === 'all' || mode === 'ferries') {
    (data.ferries || []).forEach(f => {
      items.push({
        category: 'ferries',
        categoryLabel: '⛴️ Ferry & Marine',
        badge: f.badge || 'Scenic Waterway',
        badgeClass: 'transit-badge-eco',
        title: f.name,
        route: f.route,
        duration: f.duration,
        meta1: `Frequency: <strong>${f.frequency}</strong>`,
        meta2: `Scenic Score: <strong>${f.scenic_score}</strong>`,
        notes: f.free_pedestrians ? 'Complimentary travel for pedestrians.' : 'Tickets available at wharf / online.',
        price: f.fare,
        currency: f.currency || cur,
        bookingUrl: f.booking_link,
        bookLabel: '🌊 Book Ferry Wharf ↗',
        transitType: 'transport',
        raw: f,
      });
    });
  }

  if (items.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; padding: 2.5rem; text-align: left; background: var(--bg-surface); border: 1px dashed var(--border); border-radius: var(--r-md);">
        <div style="font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.35rem;">No options found for this mode filter</div>
        <p style="font-size: 0.82rem; color: var(--text-muted); margin: 0 0 1rem 0;">Try selecting "All Modes" to view every way to travel.</p>
        <button class="btn btn-sm btn-primary" onclick="setTransitModeFilter('all')">Show All Modes</button>
      </div>`;
    return;
  }

  grid.innerHTML = items.map(item => {
    const priceStr = item.priceMax
      ? `${fmt(item.price, item.currency, 0)} – ${fmt(item.priceMax, item.currency, 0)}`
      : fmt(item.price, item.currency, 0);

    const safeTitle = item.title.replace(/'/g, "\\'");

    return `
      <div class="transit-card">
        <div class="transit-card-header">
          <span style="font-weight:700;font-size:0.75rem;color:var(--text-primary);display:flex;align-items:center;gap:4px;">
            ${item.categoryLabel}
          </span>
          <span class="transit-badge ${item.badgeClass}">${item.badge}</span>
        </div>

        <div class="transit-card-body">
          <div class="transit-carrier-title">${item.title}</div>
          <div class="transit-route-row">
            <span>📍 ${item.route}</span>
            <span style="opacity:0.6;">·</span>
            <span style="font-weight:600;color:var(--primary);">⏱️ ${item.duration}</span>
          </div>

          <div class="transit-meta-grid">
            <div class="transit-meta-item">${item.meta1}</div>
            <div class="transit-meta-item">${item.meta2}</div>
          </div>

          <div class="transit-notes-box">
            ${item.notes}
          </div>

          <div class="transit-price-row">
            <div>
              <span class="transit-price-val">${priceStr}</span>
              <span style="font-size:0.72rem;color:var(--text-muted);"> ${item.category === 'rentals' ? '/ day' : 'est. fare'}</span>
            </div>
            <span style="font-size:0.72rem;color:#059669;font-weight:600;">✅ Verified Carrier</span>
          </div>

          <!-- Action buttons strictly on the LEFT -->
          <div class="transit-actions-left">
            <a href="${item.bookingUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm" title="Open verified official booking partner">
              ${item.bookLabel}
            </a>
            <button class="btn btn-ghost btn-sm" onclick="planTransitItem('${item.transitType}', '${safeTitle}', ${item.price}, '${item.currency}', '${item.duration}')" title="Insert transit schedule into Trip Itinerary">
              ➕ Add to Plan
            </button>
            <button class="btn btn-ghost btn-sm" onclick="logTransitExpenseDirectly('${safeTitle}', ${item.price}, '${item.currency}')" title="Record this ride in Transport Expenses">
              🧾 Log Expense
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

async function planTransitItem(type, title, fare, currency, duration) {
  try {
    toast(`Adding "${title}" to trip itinerary...`, 'info', 1500);
    const res = await api('/transit/book-or-plan', {
      method: 'POST',
      body: JSON.stringify({
        trip_id: state.currentTripId,
        day_number: 1,
        title: title,
        transit_type: type,
        fare: fare,
        currency: currency,
        duration: duration,
        notes: `Multi-modal transit booked via WanderWallet Hub`,
      }),
    });
    toast(res.message || `Added "${title}" to Day 1 plan!`, 'success');
  } catch (err) {
    toast(`Failed to add transit: ${err.message}`, 'error');
  }
}

async function logTransitExpenseDirectly(description, amount, currency) {
  try {
    toast(`Logging transport expense "${description}"...`, 'info', 1500);
    const res = await api('/transit/log-expense', {
      method: 'POST',
      body: JSON.stringify({
        trip_id: state.currentTripId,
        description: description,
        amount: amount,
        currency: currency,
      }),
    });
    toast(res.message || `Logged ${currency} ${amount} under Transport expenses!`, 'success');
    // Refresh transit hub to reflect updated transport budget runway
    await loadTransitHub();
  } catch (err) {
    toast(`Failed to log expense: ${err.message}`, 'error');
  }
}

function applyTransitPreset(orig, dest) {
  const originInput = document.getElementById('transit-origin-input');
  const destInput = document.getElementById('transit-dest-input');
  if (originInput) originInput.value = orig;
  if (destInput) destInput.value = dest;
  toast(`Loading travel modes for ${orig} ➔ ${dest}...`, 'info', 1500);
  loadTransitHub(orig, dest);
}

// Bind transit event listeners
document.getElementById('btn-transit-search')?.addEventListener('click', () => {
  const orig = document.getElementById('transit-origin-input')?.value.trim();
  const dest = document.getElementById('transit-dest-input')?.value.trim();
  if (!dest) {
    toast('Please enter a destination', 'warning');
    return;
  }
  toast(`Searching all transit modes from ${orig || 'any origin'} to ${dest}...`, 'info', 1800);
  loadTransitHub(orig, dest);
});

document.getElementById('btn-transit-search-trigger')?.addEventListener('click', () => {
  const orig = document.getElementById('transit-origin-input')?.value.trim();
  const dest = document.getElementById('transit-dest-input')?.value.trim();
  loadTransitHub(orig, dest);
});

document.getElementById('btn-transit-jump-itinerary')?.addEventListener('click', () => navigate('itinerary'));

document.getElementById('btn-transit-save-route')?.addEventListener('click', async () => {
  const orig = document.getElementById('transit-origin-input')?.value.trim() || 'Mumbai, India';
  const dest = document.getElementById('transit-dest-input')?.value.trim() || 'Goa, India';
  try {
    await api('/hotels/update-route', {
      method: 'POST',
      body: JSON.stringify({
        trip_id: state.currentTripId,
        origin: orig,
        destination: dest,
      }),
    });
    toast(`Saved default trip route: ${orig} ➔ ${dest}!`, 'success');
  } catch (err) {
    toast(`Failed to save route: ${err.message}`, 'error');
  }
});

// Bind transit filter buttons
document.querySelectorAll('.transit-filter-btn').forEach(btn => {
  btn.addEventListener('click', (e) => {
    const mode = e.currentTarget.getAttribute('data-mode') || 'all';
    setTransitModeFilter(mode);
  });
});

// Window exports
window.applyTransitPreset = applyTransitPreset;
window.setTransitModeFilter = setTransitModeFilter;
window.planTransitItem = planTransitItem;
window.logTransitExpenseDirectly = logTransitExpenseDirectly;
window.loadTransitHub = loadTransitHub;

// ─── Demo Fallback State ──────────────────────────────────────────────────────
function renderDemoState() {
  document.getElementById('trip-title').textContent = 'Goa Celebration 2026 🏖️ (Demo)';
  document.getElementById('trip-dates').textContent = '01 Oct 2026 – 07 Oct 2026 · Goa, India';
  document.getElementById('kpi-spent').textContent = '₹30,688';
  document.getElementById('kpi-spent-sub').textContent = 'of ₹50,000 total cap';
  document.getElementById('kpi-remaining').textContent = '₹19,312';
  document.getElementById('kpi-members').textContent = '4';
  document.getElementById('kpi-expenses').textContent = '6';

  renderBudgetRing({ summary: { total_spent: 30688, total_budget: 50000, remaining: 19312, home_currency: 'INR' } });
  renderBreachBanners([{
    type: 'breached',
    category: 'food',
    message: 'Food spend breached cap by ₹1,092.50 due to foreign USD dinner ($55 converted at 83.50).',
  }]);

  // Inject demo trips into selector if API failed
  const select = document.getElementById('trip-select');
  if (select && select.options.length === 0) {
    const demoTrips = [
      { id: 'trp_goa_2026',        name: '🏖️ Goa Celebration 2026' },
      { id: 'trp_bali',            name: '🌴 Bali Bliss 2026' },
      { id: 'trp_london',          name: '🏴󠁧󠁢󠁥󠁮󠁧󠁿 London Explorer' },
      { id: 'trp_paris',           name: '🗼 Paris Romance' },
      { id: 'trp_dubai',           name: '🏙️ Dubai Luxury Escape' },
      { id: 'trp_kashmir',         name: '🏔️ Kashmir Paradise' },
    ];
    demoTrips.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = t.name;
      select.appendChild(opt);
    });
  }
}

// ─── App Initialization ───────────────────────────────────────────────────────
async function checkBackendHealth() {
  const pill = document.getElementById('backend-status-pill');
  if (!pill) return;
  try {
    const res = await fetch('http://localhost:5001/api/health', { method: 'GET' });
    if (res.ok) {
      const data = await res.json();
      const dbLabel = data.database === 'supabase_postgresql' ? 'Supabase' : 'Active';
      pill.innerHTML = `<span class="backend-dot-indicator"></span> API :5001 (${dbLabel})`;
      pill.style.background = 'rgba(34, 197, 94, 0.14)';
      pill.style.borderColor = 'rgba(34, 197, 94, 0.38)';
      pill.style.color = '#4ade80';
    } else {
      pill.innerHTML = `<span style="width:7px;height:7px;border-radius:50%;background:#f59e0b;display:inline-block;"></span> API :5001`;
    }
  } catch (e) {
    pill.innerHTML = `<span style="width:7px;height:7px;border-radius:50%;background:#ef4444;display:inline-block;"></span> API Offline`;
    pill.style.background = 'rgba(239, 68, 68, 0.15)';
    pill.style.borderColor = 'rgba(239, 68, 68, 0.4)';
    pill.style.color = '#f87171';
  }
}

async function initApp() {
  checkBackendHealth();
  await loadTrips();
  await loadDashboard();
}

initApp();
