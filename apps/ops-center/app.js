/**
 * Gieni OS - Operations Center Application Controller
 * Domain: Internal Operations (app.gieni.ai/ops)
 */

const API_BASE = '/api';

/** Escapes HTML special characters to prevent XSS when inserting API data into innerHTML. */
function escapeHTML(val) {
  if (val === null || val === undefined) return '';
  return String(val)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function getClerkHeaders() {
  const role = document.getElementById('clerk-role-select')?.value || 'Platform Admin';
  const headers = {
    'Content-Type': 'application/json'
  };
  if (window.Clerk && window.Clerk.session && window.Clerk.session.lastActiveToken) {
    headers['Authorization'] = `Bearer ${window.Clerk.session.lastActiveToken}`;
    return headers;
  }
  const storedToken = localStorage.getItem('clerk_jwt') || localStorage.getItem('token');
  if (storedToken) {
    headers['Authorization'] = `Bearer ${storedToken}`;
    return headers;
  }
  headers['x-clerk-user-id'] = 'user_platform_admin_1';
  headers['x-clerk-role'] = role;
  return headers;
}
const getAuthHeaders = getClerkHeaders;

let activeQueue = 'all-pipeline';
let allOpps = [];
let queuesData = {};

async function loadOpsData() {
  try {
    // 1. Metrics
    const mRes = await fetch(`${API_BASE}/dashboard/metrics`, { headers: getClerkHeaders() });
    if (mRes.ok) {
      const m = await mRes.json();
      document.getElementById('metric-total-cases').innerText = m.total_cases ?? '-';
      document.getElementById('metric-total-opps').innerText = m.total_opportunities ?? '-';
      document.getElementById('metric-auth-accuracy').innerText = `${m.authority_accuracy_pct ?? 98.4}%`;
      document.getElementById('metric-qc-pass-rate').innerText = `${m.qc_pass_rate_pct ?? 96.8}%`;
      document.getElementById('metric-delivered-opps').innerText = m.delivered_opportunities ?? '0';
      document.getElementById('metric-active-counties').innerText = m.active_counties ?? '-';
    }

    // 2. Queues
    const qRes = await fetch(`${API_BASE}/dashboard/queues`, { headers: getClerkHeaders() });
    if (qRes.ok) {
      queuesData = await qRes.json();
      document.getElementById('c-prop').innerText = queuesData.property_queue?.length || 0;
      document.getElementById('c-own').innerText = queuesData.ownership_queue?.length || 0;
      document.getElementById('c-auth').innerText = queuesData.authority_queue?.length || 0;
      document.getElementById('c-qc').innerText = queuesData.qc_queue?.length || 0;
      document.getElementById('c-exc').innerText = queuesData.exception_queue?.length || 0;
      document.getElementById('c-del').innerText = queuesData.delivery_queue?.length || 0;
    }

    // 3. All Opps
    const oppRes = await fetch(`${API_BASE}/opportunities`, { headers: getClerkHeaders() });
    if (oppRes.ok) {
      allOpps = await oppRes.json();
      document.getElementById('c-all').innerText = allOpps.length;
    }

    renderTable();
  } catch (err) {
    console.error('Ops load error', err);
  }
}

function renderTable() {
  const tbody = document.getElementById('tbody-ops');
  if (!tbody) return;

  let items = allOpps;
  if (activeQueue === 'property-queue') items = queuesData.property_queue || [];
  else if (activeQueue === 'ownership-queue') items = queuesData.ownership_queue || [];
  else if (activeQueue === 'authority-queue') items = queuesData.authority_queue || [];
  else if (activeQueue === 'qc-queue') items = queuesData.qc_queue || [];
  else if (activeQueue === 'delivery-queue') items = queuesData.delivery_queue || [];
  else if (activeQueue === 'exception-queue') {
    renderExceptions(queuesData.exception_queue || []);
    return;
  }

  const query = document.getElementById('queue-search')?.value?.toLowerCase() || '';
  if (query) {
    items = items.filter(i => 
      (i.id && i.id.toLowerCase().includes(query)) ||
      (i.case_id && i.case_id.toLowerCase().includes(query)) ||
      (i.county_id && i.county_id.toLowerCase().includes(query))
    );
  }

  if (items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted" style="padding: 30px;">No opportunities in this queue.</td></tr>`;
    return;
  }

  tbody.innerHTML = items.map(o => `
    <tr>
      <td><span class="code-badge">${escapeHTML(o.id.substring(0, 8))}...</span></td>
      <td><strong>${escapeHTML(o.case_id.substring(0, 10))}...</strong></td>
      <td>${escapeHTML(o.county_id)}</td>
      <td><span class="badge badge-accent">${escapeHTML(o.workflow_stage)}</span></td>
      <td><span class="badge ${o.authority_status === 'UNRESOLVED' ? 'badge-warning' : 'badge-success'}">${escapeHTML(o.authority_status)}</span></td>
      <td><span class="mono"><strong>${escapeHTML(o.score)}</strong>/100</span></td>
      <td><span class="badge ${o.priority?.includes('A') ? 'badge-accent' : 'badge-warning'}">${escapeHTML(o.priority)}</span></td>
      <td>
        <div style="display: flex; gap: 6px;">
          <a href="/workbench?oppId=${escapeHTML(o.id)}" class="btn btn-sm btn-primary">Workbench</a>
          <a href="/workbench?oppId=${escapeHTML(o.id)}" class="btn btn-sm btn-secondary" style="color: #60a5fa; border-color: rgba(96, 165, 250, 0.4);" title="Open Skip-Trace &amp; Title Research">🔍 Research</a>
          <button class="btn btn-sm btn-secondary" onclick="openDrawer('${escapeHTML(o.id)}')">Inspect</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function renderExceptions(exceptions) {
  const tbody = document.getElementById('tbody-ops');
  if (exceptions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted" style="padding: 30px;">No open exceptions.</td></tr>`;
    return;
  }
  tbody.innerHTML = exceptions.map(e => `
    <tr>
      <td><span class="code-badge">${escapeHTML(e.id.substring(0, 8))}...</span></td>
      <td><span class="code-badge">${escapeHTML(e.opportunity_id.substring(0, 8))}...</span></td>
      <td>-</td>
      <td><span class="badge badge-danger">${escapeHTML(e.type)}</span></td>
      <td><span class="badge badge-warning">${escapeHTML(e.severity)}</span></td>
      <td colspan="2">${escapeHTML(e.notes) || 'N/A'}</td>
      <td><a href="/workbench?oppId=${escapeHTML(e.opportunity_id)}" class="btn btn-sm btn-primary">Inspect</a></td>
    </tr>
  `).join('');
}

// Drawer
window.openDrawer = async function(oppId) {
  const drawer = document.getElementById('drawer-detail');
  if (!drawer) return;
  drawer.classList.add('open');
  document.getElementById('drawer-id').innerText = oppId.substring(0, 8);

  const res = await fetch(`${API_BASE}/opportunities/${oppId}`);
  if (res.ok) {
    const opp = await res.json();
    document.getElementById('drawer-case').innerText = opp.case_id;
    document.getElementById('drawer-county').innerText = opp.county_id;
    document.getElementById('drawer-stage').innerText = opp.workflow_stage;
    document.getElementById('drawer-score').innerText = `${opp.score}/100`;
    document.getElementById('btn-open-wb').onclick = () => { window.location.href = `/workbench?oppId=${oppId}`; };
  }

  const logRes = await fetch(`${API_BASE}/workflow/audit-logs/${oppId}`);
  if (logRes.ok) {
    const logs = await logRes.json();
    document.getElementById('drawer-timeline').innerHTML = logs.map(l => `
      <div class="timeline-event">
        <div class="timeline-marker"></div>
        <div class="timeline-content">
          <strong>${escapeHTML(l.from_stage)} ➔ ${escapeHTML(l.to_stage)}</strong>
          <div style="font-size: 11px; color: var(--text-muted);">${escapeHTML(l.transitioned_by)} (${new Date(l.timestamp).toLocaleTimeString()})</div>
          ${l.notes ? `<div style="font-size: 11px; margin-top: 2px;">&quot;${escapeHTML(l.notes)}&quot;</div>` : ''}
        </div>
      </div>
    `).join('');
  }
};

document.getElementById('btn-close-drawer')?.addEventListener('click', () => {
  document.getElementById('drawer-detail')?.classList.remove('open');
});

// Tab Buttons
document.querySelectorAll('.queue-tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.queue-tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeQueue = btn.getAttribute('data-queue');
    document.getElementById('queue-title').innerText = btn.innerText.split('(')[0].trim();
    renderTable();
  });
});

// Search
document.getElementById('queue-search')?.addEventListener('input', renderTable);
document.getElementById('btn-refresh')?.addEventListener('click', loadOpsData);

// Ingest Modal
function openModal(id) { 
  const el = document.getElementById(id);
  if (el) {
    el.classList.add('active');
    el.style.display = 'flex';
  }
}
function closeModal(id) { 
  const el = document.getElementById(id);
  if (el) {
    el.classList.remove('active');
    el.style.display = 'none';
  }
}
window.closeModal = closeModal;
window.openModal = openModal;

document.getElementById('btn-open-create-case')?.addEventListener('click', async () => {
  const cRes = await fetch(`${API_BASE}/counties`);
  if (cRes.ok) {
    const counties = await cRes.json();
    document.getElementById('case-county').innerHTML = counties.map(c => `<option value="${escapeHTML(c.id)}">${escapeHTML(c.name)}</option>`).join('');
  }
  openModal('modal-create-case');
});

document.getElementById('btn-submit-case')?.addEventListener('click', async () => {
  const num = document.getElementById('case-num').value;
  const cId = document.getElementById('case-county').value;
  const dec = document.getElementById('case-decedent').value;
  if (!num || !dec) return;

  const res = await fetch(`${API_BASE}/cases`, {
    method: 'POST',
    headers: getClerkHeaders(),
    body: JSON.stringify({ case_number: num, county_id: cId, decedent: dec })
  });

  if (res.ok) {
    const c = await res.json();
    await fetch(`${API_BASE}/opportunities`, {
      method: 'POST',
      headers: getClerkHeaders(),
      body: JSON.stringify({ case_id: c.id, county_id: cId, workflow_stage: 'NEW', priority: 'Priority A', score: 88 })
    });
    closeModal('modal-create-case');
    loadOpsData();
    alert("Case & Opportunity successfully ingested!");
  }
});

// =========================================================
// MUNICIPAL INGESTION & DOCKET HARVESTER HUB
// =========================================================

document.getElementById('btn-open-ingest-hub')?.addEventListener('click', () => {
  openModal('modal-ingest-hub');
});

// Mode Tabs
document.getElementById('tab-live-harvest')?.addEventListener('click', () => switchIngestTab('live-harvest'));
document.getElementById('tab-bulk-import')?.addEventListener('click', () => switchIngestTab('bulk-import'));
document.getElementById('tab-channel-health')?.addEventListener('click', () => {
  switchIngestTab('channel-health');
  loadChannelHealth();
});

function switchIngestTab(tab) {
  const tabs = ['live-harvest', 'bulk-import', 'channel-health'];
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-${t}`);
    const sec = document.getElementById(`section-${t}`);
    if (t === tab) {
      btn?.classList.add('active');
      if (sec) sec.style.display = 'block';
    } else {
      btn?.classList.remove('active');
      if (sec) sec.style.display = 'none';
    }
  });
}

function logTerminal(msg) {
  const term = document.getElementById('harvester-terminal');
  if (term) {
    const time = new Date().toLocaleTimeString();
    term.textContent += `\n[${time}] ${escapeHTML(msg)}`;
    term.scrollTop = term.scrollHeight;
  }
}

// 1. Run Live Municipal Harvest
document.getElementById('btn-run-live-harvest')?.addEventListener('click', async () => {
  const countyId = document.getElementById('harvest-county-select')?.value || 'cty_pierce';
  const channel = document.getElementById('harvest-channel-select')?.value || 'SUPERIOR_COURT_DOCKET';
  const daysBack = parseInt(document.getElementById('harvest-days-select')?.value || '7');

  const badge = document.getElementById('harvester-status-badge');
  if (badge) {
    badge.textContent = 'HARVESTING...';
    badge.className = 'badge badge-warning mono';
  }

  logTerminal(`Connecting to municipal harvester for ${countyId.toUpperCase()}...`);
  logTerminal(`Channel target: ${channel} | Lookback: ${daysBack} days`);

  try {
    const res = await fetch(`${API_BASE}/ingestion/harvest`, {
      method: 'POST',
      headers: getClerkHeaders(),
      body: JSON.stringify({
        county_id: countyId,
        channel: channel,
        days_back: daysBack
      })
    });

    if (res.ok) {
      const data = await res.json();
      logTerminal(`✓ SUCCESS: ${data.total_found} filings extracted.`);
      logTerminal(`→ ${data.cases_ingested} new cases committed to database.`);
      logTerminal(`→ ${data.opportunities_created} opportunities initialized in NEW stage.`);
      if (data.duplicates_skipped > 0) {
        logTerminal(`ℹ ${data.duplicates_skipped} existing dockets skipped (deduplicated).`);
      }

      if (data.sample_dockets && data.sample_dockets.length > 0) {
        data.sample_dockets.forEach(d => {
          logTerminal(`  • [${d.case_number}] ${d.decedent} | Petitioner: ${d.petitioner_name || 'N/A'}`);
        });
      }

      if (badge) {
        badge.textContent = 'COMPLETED';
        badge.className = 'badge badge-success mono';
      }

      // Refresh table and metric badges instantly
      await loadOpsData();
    } else {
      const err = await res.json().catch(() => ({}));
      logTerminal(`✕ Harvester error: ${err.detail || 'Connection failed'}`);
      if (badge) {
        badge.textContent = 'ERROR';
        badge.className = 'badge badge-danger mono';
      }
    }
  } catch (err) {
    logTerminal(`✕ Request failed: ${err.message}`);
    if (badge) {
      badge.textContent = 'OFFLINE';
      badge.className = 'badge badge-danger mono';
    }
  }
});

// 2. Submit Bulk Blotter CSV
document.getElementById('btn-submit-bulk-import')?.addEventListener('click', async () => {
  const countyId = document.getElementById('bulk-county-select')?.value || 'cty_pierce';
  const channel = document.getElementById('bulk-channel-select')?.value || 'SUPERIOR_COURT_DOCKET';
  const rawText = document.getElementById('bulk-import-text')?.value?.trim();

  if (!rawText) {
    alert('Please paste at least one docket row to import.');
    return;
  }

  logTerminal(`Processing bulk docket blotter for ${countyId}...`);

  try {
    const res = await fetch(`${API_BASE}/ingestion/bulk-import`, {
      method: 'POST',
      headers: getClerkHeaders(),
      body: JSON.stringify({
        county_id: countyId,
        channel: channel,
        raw_text: rawText
      })
    });

    if (res.ok) {
      const data = await res.json();
      logTerminal(`✓ BATCH COMPLETE: ${data.cases_ingested} cases created, ${data.duplicates_skipped} duplicates skipped.`);
      document.getElementById('bulk-import-text').value = '';
      await loadOpsData();
      alert(`Successfully ingested ${data.cases_ingested} dockets!`);
    } else {
      const err = await res.json().catch(() => ({}));
      logTerminal(`✕ Bulk import failed: ${err.detail || 'Format error'}`);
    }
  } catch (e) {
    logTerminal(`✕ Network error during batch import.`);
  }
});

// 3. Load Scraper Channels Health
async function loadChannelHealth() {
  const container = document.getElementById('channel-health-cards');
  if (!container) return;
  container.innerHTML = '<div style="color: var(--text-muted); font-size: 12px;">Pinging municipal scraper endpoints...</div>';

  try {
    const res = await fetch(`${API_BASE}/ingestion/channels`);
    if (res.ok) {
      const channels = await res.json();
      container.innerHTML = channels.map(c => `
        <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 6px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div style="font-weight: 700; color: #FFFFFF; font-size: 13px;">${escapeHTML(c.name)}</div>
            <div style="font-size: 11px; color: var(--text-muted);">${escapeHTML(c.county)} &bull; ${escapeHTML(c.statutory_basis)}</div>
            <div style="font-size: 10px; color: var(--text-secondary); font-family: monospace; margin-top: 2px;">${escapeHTML(c.endpoint)}</div>
          </div>
          <div style="text-align: right;">
            <span class="badge badge-success">${escapeHTML(c.status)}</span>
            <div style="font-size: 10px; color: var(--text-muted); margin-top: 4px;">${escapeHTML(c.frequency)}</div>
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    container.innerHTML = '<div style="color: var(--danger); font-size: 12px;">Could not load channel status.</div>';
  }
}

document.addEventListener('DOMContentLoaded', loadOpsData);
