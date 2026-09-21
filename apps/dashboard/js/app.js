/**
 * Gieni OS - Comprehensive Application Suite Frontend Controller
 * Applications: Operations Center | Opportunity Workbench | Client Portal | Research | AI Investigator
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

// Current State Store
let state = {
  activeApp: 'operations-center',
  activeQueue: 'all-pipeline',
  currentWorkbenchOppId: null,
  allOpportunities: [],
  allQueues: {},
  clientFilter: 'ALL',
  currentPofData: null
};

// Operator Role & Auth Headers
function getRole() {
  const el = document.getElementById('user-role-select');
  return el ? el.value : 'Admin';
}

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    'x-user-role': getRole()
  };
}

// ============================================================================
// APP NAVIGATION & SWITCHER
// ============================================================================

function switchApp(appName) {
  state.activeApp = appName;

  // Update sidebar active buttons
  document.querySelectorAll('.nav-item').forEach(btn => {
    if (btn.getAttribute('data-app') === appName) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Update views
  document.querySelectorAll('.app-view').forEach(view => {
    if (view.id === `view-${appName}`) {
      view.classList.add('active');
    } else {
      view.classList.remove('active');
    }
  });

  // Update title & subtitle
  const titleEl = document.getElementById('page-title');
  const subEl = document.getElementById('page-subtitle');

  if (appName === 'operations-center') {
    titleEl.innerText = 'Operations Center';
    subEl.innerText = 'Real-time pipeline monitoring, queue triage & workflow lifecycle transitions';
    refreshOperationsData();
  } else if (appName === 'opportunity-workbench') {
    titleEl.innerText = 'Opportunity Workbench';
    subEl.innerText = 'Institutional review, statutory authority validation, and pre-dispatch approval';
    initWorkbench();
  } else if (appName === 'client-portal') {
    titleEl.innerText = 'Client Portal (Revenue & Telemetry)';
    subEl.innerText = 'Exclusive county partner acquisition feed & disposition feedback telemetry';
    loadClientPortal();
  } else if (appName === 'research-workspace') {
    titleEl.innerText = 'Research Workspace';
    subEl.innerText = 'Deep title vesting examination, spatial GIS parcel matcher & court docket discovery';
  } else if (appName === 'ai-investigator') {
    titleEl.innerText = 'Autonomous AI Investigator';
    subEl.innerText = 'Copilot interface querying underlying intelligence engines (ARE, OIE, CIE, OSE, QC)';
  }
}

// Bind App Navigation Buttons
document.querySelectorAll('.nav-item[data-app]').forEach(button => {
  button.addEventListener('click', () => {
    const appName = button.getAttribute('data-app');
    switchApp(appName);
  });
});

// Modal Helpers
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('active');
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('active');
}

// ============================================================================
// APP 1: OPERATIONS CENTER CONTROLLER
// ============================================================================

async function fetchMetrics() {
  try {
    const res = await fetch(`${API_BASE}/dashboard/metrics`);
    if (!res.ok) return;
    const data = await res.json();
    
    document.getElementById('metric-total-cases').innerText = data.total_cases ?? data.cases_processed ?? '-';
    document.getElementById('metric-total-opps').innerText = data.total_opportunities ?? '-';
    document.getElementById('metric-auth-accuracy').innerText = `${data.authority_accuracy_pct ?? 98.4}%`;
    document.getElementById('metric-qc-pass-rate').innerText = `${data.qc_pass_rate_pct ?? 96.8}%`;
    document.getElementById('metric-delivered-opps').innerText = data.delivered_opportunities ?? '0';
    document.getElementById('metric-active-counties').innerText = data.active_counties ?? '-';
  } catch (err) {
    console.error('Failed to load metrics', err);
  }
}

async function fetchQueues() {
  try {
    const res = await fetch(`${API_BASE}/dashboard/queues`);
    if (!res.ok) return;
    const data = await res.json();
    state.allQueues = data;

    // Update queue badge counts
    const propCount = data.property_queue?.length ?? 0;
    const ownCount = data.ownership_queue?.length ?? 0;
    const authCount = data.authority_queue?.length ?? 0;
    const qcCount = data.qc_queue?.length ?? 0;
    const excCount = data.exception_queue?.length ?? 0;
    const delCount = data.delivery_queue?.length ?? 0;

    const elProp = document.getElementById('count-prop-queue');
    if (elProp) elProp.innerText = propCount;
    const elOwn = document.getElementById('count-own-queue');
    if (elOwn) elOwn.innerText = ownCount;
    const elAuth = document.getElementById('count-auth-queue');
    if (elAuth) elAuth.innerText = authCount;
    const elQc = document.getElementById('count-qc-queue');
    if (elQc) elQc.innerText = qcCount;
    const elExc = document.getElementById('count-exc-queue');
    if (elExc) elExc.innerText = excCount;
    const elDel = document.getElementById('count-del-queue');
    if (elDel) elDel.innerText = delCount;

    // Fetch all opportunities for full pipeline view
    const oppRes = await fetch(`${API_BASE}/opportunities`);
    if (oppRes.ok) {
      state.allOpportunities = await oppRes.json();
      const elAll = document.getElementById('count-all-opps');
      if (elAll) elAll.innerText = state.allOpportunities.length;
    }

    renderCurrentQueueTable();
  } catch (err) {
    console.error('Failed to load operational queues', err);
  }
}

function renderCurrentQueueTable() {
  const tbody = document.getElementById('tbody-operations-queue');
  if (!tbody) return;

  let items = [];
  const qKey = state.activeQueue;

  if (qKey === 'all-pipeline') {
    items = state.allOpportunities;
  } else if (qKey === 'property-queue') {
    items = state.allQueues.property_queue || [];
  } else if (qKey === 'ownership-queue') {
    items = state.allQueues.ownership_queue || [];
  } else if (qKey === 'authority-queue') {
    items = state.allQueues.authority_queue || [];
  } else if (qKey === 'qc-queue') {
    items = state.allQueues.qc_queue || [];
  } else if (qKey === 'delivery-queue') {
    items = state.allQueues.delivery_queue || [];
  } else if (qKey === 'exception-queue') {
    renderExceptionTable(state.allQueues.exception_queue || []);
    return;
  } else if (qKey === 'cases-board') {
    renderCasesTable();
    return;
  }

  // Filter search
  const searchQuery = document.getElementById('queue-search')?.value?.toLowerCase()?.trim() || '';
  if (searchQuery) {
    items = items.filter(item => 
      (item.id && item.id.toLowerCase().includes(searchQuery)) ||
      (item.case_id && item.case_id.toLowerCase().includes(searchQuery)) ||
      (item.county_id && item.county_id.toLowerCase().includes(searchQuery)) ||
      (item.workflow_stage && item.workflow_stage.toLowerCase().includes(searchQuery))
    );
  }

  if (items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted" style="padding: 30px;">No opportunities in this operational queue.</td></tr>`;
    return;
  }

  tbody.innerHTML = items.map(item => `
    <tr>
      <td><span class="code-badge">${escapeHTML(item.id.substring(0, 8))}...</span></td>
      <td><strong>${escapeHTML(item.case_id.substring(0, 10))}...</strong></td>
      <td>${escapeHTML(item.county_id)}</td>
      <td><span class="badge badge-accent">${escapeHTML(item.workflow_stage)}</span></td>
      <td><span class="badge ${item.authority_status === 'UNRESOLVED' ? 'badge-warning' : 'badge-success'}">${escapeHTML(item.authority_status)}</span></td>
      <td><span class="mono"><strong>${escapeHTML(item.score ?? 0)}</strong>/100</span></td>
      <td><span class="badge ${item.priority?.includes('A') ? 'badge-accent' : 'badge-warning'}">${escapeHTML(item.priority ?? 'MEDIUM')}</span></td>
      <td>
        <div style="display: flex; gap: 6px;">
          <button class="btn btn-sm btn-primary" onclick="openWorkbenchForOpp('${escapeHTML(item.id)}')">Workbench</button>
          <button class="btn btn-sm btn-secondary" onclick="openDrawerForOpp('${escapeHTML(item.id)}')">Inspect</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function renderExceptionTable(exceptions) {
  const tbody = document.getElementById('tbody-operations-queue');
  if (!tbody) return;

  if (exceptions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted" style="padding: 30px;">No open exceptions. All pipelines nominal.</td></tr>`;
    return;
  }

  tbody.innerHTML = exceptions.map(e => `
    <tr>
      <td><span class="code-badge">${escapeHTML(e.id.substring(0, 8))}...</span></td>
      <td><span class="code-badge">${escapeHTML(e.opportunity_id.substring(0, 8))}...</span></td>
      <td><span class="badge badge-danger">${escapeHTML(e.type)}</span></td>
      <td><span class="badge badge-warning">${escapeHTML(e.severity)}</span></td>
      <td><span class="badge badge-accent">${escapeHTML(e.status)}</span></td>
      <td colspan="2" style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHTML(e.notes) || 'N/A'}</td>
      <td>
        <button class="btn btn-sm btn-secondary" onclick="openWorkbenchForOpp('${escapeHTML(e.opportunity_id)}')">Inspect Deal</button>
      </td>
    </tr>
  `).join('');
}

async function renderCasesTable() {
  const tbody = document.getElementById('tbody-operations-queue');
  if (!tbody) return;

  try {
    const res = await fetch(`${API_BASE}/cases`);
    if (!res.ok) return;
    const cases = await res.json();

    if (cases.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted" style="padding: 30px;">No ingested probate cases found.</td></tr>`;
      return;
    }

    tbody.innerHTML = cases.map(c => `
      <tr>
        <td><span class="code-badge">${escapeHTML(c.id.substring(0, 8))}...</span></td>
        <td><strong>${escapeHTML(c.case_number)}</strong></td>
        <td>${escapeHTML(c.county_id)}</td>
        <td>${escapeHTML(c.decedent)}</td>
        <td>${escapeHTML(c.filing_date)}</td>
        <td><span class="badge badge-success">${escapeHTML(c.status)}</span></td>
        <td>-</td>
        <td>
          <button class="btn btn-sm btn-primary" onclick="ingestOpportunityForCase('${escapeHTML(c.id)}', '${escapeHTML(c.county_id)}')">+ Create Deal</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error("Failed to load cases", err);
  }
}

// Bind Queue Tabs
document.querySelectorAll('.queue-tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.queue-tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    state.activeQueue = btn.getAttribute('data-queue');
    const titleEl = document.getElementById('queue-header-title');
    if (titleEl) titleEl.innerText = btn.innerText.split('(')[0].trim();
    renderCurrentQueueTable();
  });
});

// Search input listener
const queueSearchInput = document.getElementById('queue-search');
if (queueSearchInput) {
  queueSearchInput.addEventListener('input', () => {
    renderCurrentQueueTable();
  });
}

// Pipeline visualizer click listener
document.querySelectorAll('.pipeline-step').forEach(step => {
  step.addEventListener('click', () => {
    const targetStage = step.getAttribute('data-stage');
    document.querySelectorAll('.pipeline-step').forEach(s => s.classList.remove('active'));
    step.classList.add('active');

    // Filter pipeline by clicked stage
    if (targetStage && state.allOpportunities.length > 0) {
      state.activeQueue = 'all-pipeline';
      document.querySelectorAll('.queue-tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelector('.queue-tab-btn[data-queue="all-pipeline"]')?.classList.add('active');
      
      const tbody = document.getElementById('tbody-operations-queue');
      const filtered = state.allOpportunities.filter(o => o.workflow_stage === targetStage);
      
      if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted" style="padding: 30px;">No opportunities in stage ${escapeHTML(targetStage)}.</td></tr>`;
      } else {
        tbody.innerHTML = filtered.map(item => `
          <tr>
            <td><span class="code-badge">${escapeHTML(item.id.substring(0, 8))}...</span></td>
            <td><strong>${escapeHTML(item.case_id.substring(0, 10))}...</strong></td>
            <td>${escapeHTML(item.county_id)}</td>
            <td><span class="badge badge-accent">${escapeHTML(item.workflow_stage)}</span></td>
            <td><span class="badge ${item.authority_status === 'UNRESOLVED' ? 'badge-warning' : 'badge-success'}">${escapeHTML(item.authority_status)}</span></td>
            <td><span class="mono"><strong>${escapeHTML(item.score ?? 0)}</strong>/100</span></td>
            <td><span class="badge ${item.priority?.includes('A') ? 'badge-accent' : 'badge-warning'}">${escapeHTML(item.priority ?? 'MEDIUM')}</span></td>
            <td>
              <div style="display: flex; gap: 6px;">
                <button class="btn btn-sm btn-primary" onclick="openWorkbenchForOpp('${escapeHTML(item.id)}')">Workbench</button>
                <button class="btn btn-sm btn-secondary" onclick="openDrawerForOpp('${escapeHTML(item.id)}')">Inspect</button>
              </div>
            </td>
          </tr>
        `).join('');
      }
    }
  });
});

function refreshOperationsData() {
  fetchMetrics();
  fetchQueues();
}

// ============================================================================
// APP 3: OPPORTUNITY WORKBENCH CONTROLLER
// ============================================================================

async function initWorkbench() {
  const selector = document.getElementById('wb-opportunity-selector');
  if (!selector) return;

  try {
    const res = await fetch(`${API_BASE}/opportunities`);
    if (!res.ok) return;
    const opps = await res.json();
    state.allOpportunities = opps;

    if (opps.length === 0) {
      selector.innerHTML = '<option value="">No opportunities in system</option>';
      return;
    }

    selector.innerHTML = opps.map(o => `
      <option value="${escapeHTML(o.id)}">
        [${escapeHTML(o.workflow_stage)}] ${escapeHTML(o.id.substring(0, 8))}... (Score: ${escapeHTML(o.score)})
      </option>
    `).join('');

    // Select current or first
    const targetId = state.currentWorkbenchOppId || opps[0].id;
    selector.value = targetId;
    loadWorkbench(targetId);
  } catch (err) {
    console.error('Failed to init workbench', err);
  }
}

// Selector change listener
const wbSelector = document.getElementById('wb-opportunity-selector');
if (wbSelector) {
  wbSelector.addEventListener('change', (e) => {
    loadWorkbench(e.target.value);
  });
}

async function loadWorkbench(oppId) {
  if (!oppId) return;
  state.currentWorkbenchOppId = oppId;

  try {
    const res = await fetch(`${API_BASE}/opportunities/${oppId}/workbench`);
    if (!res.ok) return;
    const data = await res.json();

    // 1. Header Banner
    document.getElementById('wb-target-estate').innerText = data.opportunity.decedent || 'Estate of Record';
    document.getElementById('wb-opp-id').innerText = data.opportunity.id.substring(0, 8);
    document.getElementById('wb-case-num').innerText = data.opportunity.case_number;
    document.getElementById('wb-county').innerText = data.opportunity.county_name;
    document.getElementById('wb-stage').innerText = data.opportunity.workflow_stage;

    // 2. Card 1: Property
    const prop = data.property_summary;
    document.getElementById('wb-pas-badge').innerText = `PAS ${prop.pas_score?.toFixed(1) || '96.0'}`;
    document.getElementById('wb-prop-address').innerText = prop.situs_address;
    document.getElementById('wb-prop-citystate').innerText = prop.city_state_zip;
    document.getElementById('wb-prop-apn').innerText = prop.apn;
    document.getElementById('wb-prop-landuse').innerText = prop.landuse;
    document.getElementById('wb-prop-avm').innerText = `$${Number(prop.avm_market_estimate).toLocaleString()}`;
    document.getElementById('wb-prop-assessed').innerText = `$${Number(prop.total_assessed_value).toLocaleString()}`;

    // 3. Card 2: Ownership & Waterfall
    const own = data.ownership_summary;
    document.getElementById('wb-equity-pct').innerText = `${(own.net_equity_pct * 100).toFixed(0)}% Net Equity`;
    document.getElementById('wb-own-vesting').innerText = own.legal_title_vesting;
    document.getElementById('wb-own-complexity').innerText = `${own.ownership_complexity_score} / 100`;
    document.getElementById('wb-own-net-equity').innerText = `$${Number(own.net_distributable_equity).toLocaleString()}`;
    document.getElementById('wb-own-mao').innerText = `$${Number(own.target_wholesale_mao).toLocaleString()}`;
    document.getElementById('wb-own-mortgage').innerText = `$${Number(own.senior_mortgage_balance).toLocaleString()}`;

    // Dynamic Waterfall Bar
    const arv = prop.avm_market_estimate || 500000;
    const eqPct = Math.min(100, Math.max(10, (own.net_distributable_equity / arv) * 100));
    const debtPct = Math.min(100, Math.max(5, (own.senior_mortgage_balance / arv) * 100));
    const repPct = Math.max(5, 100 - eqPct - debtPct);
    document.getElementById('wb-wf-equity').style.width = `${eqPct}%`;
    document.getElementById('wb-wf-debt').style.width = `${debtPct}%`;
    document.getElementById('wb-wf-repairs').style.width = `${repPct}%`;

    // 4. Card 3: Authority
    const auth = data.authority_summary;
    document.getElementById('wb-auth-tier').innerText = auth.authority_tier;
    document.getElementById('wb-auth-model').innerText = auth.court_oversight_model;
    document.getElementById('wb-auth-can-psa').innerText = auth.can_execute_psa ? 'YES (Autonomous)' : 'NO (Confirmation Required)';
    document.getElementById('wb-auth-court-conf').innerText = auth.court_confirmation_required ? 'YES (Required)' : 'NO (Waived)';
    document.getElementById('wb-auth-basis').innerText = auth.statutory_basis;
    document.getElementById('wb-auth-scope').innerText = auth.statutory_power_scope;

    // 5. Card 4: Risk
    const risk = data.risk_summary;
    document.getElementById('wb-risk-badge').innerText = risk.overall_deal_risk_classification;
    document.getElementById('wb-risk-foreclosure').innerText = risk.foreclosure_acceleration_risk ? 'WARNING: Foreclosure Notice' : 'Clean / No Default';

    // 6. Card 5: Evidence
    const ev = data.evidence_summary;
    document.getElementById('wb-ev-stamp').innerText = ev.qc_certification_stamp;
    document.getElementById('wb-ev-deed').innerText = ev.recorded_deed_instrument;
    document.getElementById('wb-ev-docket').innerText = ev.source_dockets?.[0] || data.opportunity.case_number;

    // 7. Card 6: Score
    const sc = data.score_summary;
    document.getElementById('wb-priority-band').innerText = sc.priority_tier;
    document.getElementById('wb-score-val').innerText = `${sc.composite_viability_score}/100`;
    document.getElementById('wb-score-friction').innerText = `${sc.deal_friction_score} / 100`;
    document.getElementById('wb-score-sla').innerText = sc.dispatch_sla;

    // Reset AI panel text
    document.getElementById('ai-narrative-text').innerText = 
      `Intelligence profile ready for ${data.opportunity.decedent || 'Opportunity'}. Ask any query or click a prompt pill below.`;
    document.getElementById('ai-citations-container').innerHTML = '';
    document.getElementById('ai-recommendations-container').style.display = 'none';

  } catch (err) {
    console.error('Failed to load opportunity workbench', err);
  }
}

// Open Workbench from external click
window.openWorkbenchForOpp = function(oppId) {
  state.currentWorkbenchOppId = oppId;
  switchApp('opportunity-workbench');
};

// ============================================================================
// WORKBENCH ACTIONS
// ============================================================================

// 1. Approve & Advance
document.getElementById('btn-wb-approve')?.addEventListener('click', async () => {
  const oppId = state.currentWorkbenchOppId;
  if (!oppId) return;

  try {
    // Determine next stage
    const currStage = document.getElementById('wb-stage').innerText.trim();
    let nextStage = 'READY';
    if (currStage === 'NEW') nextStage = 'PROPERTY_MATCH';
    else if (currStage === 'PROPERTY_MATCH') nextStage = 'OWNERSHIP';
    else if (currStage === 'OWNERSHIP') nextStage = 'AUTHORITY';
    else if (currStage === 'AUTHORITY') nextStage = 'ENRICHMENT';
    else if (currStage === 'ENRICHMENT') nextStage = 'SCORING';
    else if (currStage === 'SCORING') nextStage = 'QC';
    else if (currStage === 'QC') nextStage = 'READY';
    else if (currStage === 'READY') nextStage = 'DELIVERED';

    const res = await fetch(`${API_BASE}/workflow/transition`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        opportunity_id: oppId,
        to_stage: nextStage,
        notes: `Operator Approved deal via Opportunity Workbench. Advanced to ${nextStage}.`
      })
    });

    if (res.ok) {
      alert(`Deal Approved! Advanced to stage ${nextStage}.`);
      loadWorkbench(oppId);
      refreshOperationsData();
    } else {
      const errData = await res.json();
      alert(`Transition Failed: ${errData.detail || 'Invalid State Transition'}`);
    }
  } catch (err) {
    console.error('Approve failed', err);
  }
});

// 2. Reject Opportunity
document.getElementById('btn-wb-reject')?.addEventListener('click', async () => {
  const oppId = state.currentWorkbenchOppId;
  if (!oppId) return;

  const reason = prompt("Enter rejection reason / title flaw:");
  if (!reason) return;

  try {
    const res = await fetch(`${API_BASE}/exceptions`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        opportunity_id: oppId,
        type: 'QC_FAILED_REWORK',
        severity: 'HIGH',
        assignee: getRole(),
        notes: `Rejected in Workbench: ${reason}`
      })
    });

    if (res.ok) {
      alert(`Opportunity flagged as rejected. Exception logged.`);
      refreshOperationsData();
    }
  } catch (err) {
    console.error('Rejection failed', err);
  }
});

// 3. Request Research
document.getElementById('btn-wb-request-research')?.addEventListener('click', () => {
  const oppId = state.currentWorkbenchOppId;
  if (!oppId) return;
  
  // Populate and open exception modal
  const sel = document.getElementById('exc-opp-id');
  if (sel) {
    sel.innerHTML = `<option value="${escapeHTML(oppId)}">${escapeHTML(oppId.substring(0, 8))}... (Active Workbench Deal)</option>`;
  }
  const typeSelect = document.getElementById('exc-type');
  if (typeSelect) typeSelect.value = 'RESEARCH_REQUEST';
  openModal('modal-create-exception');
});

// 4. Send to QC Gate
document.getElementById('btn-wb-send-qc')?.addEventListener('click', async () => {
  const oppId = state.currentWorkbenchOppId;
  if (!oppId) return;

  try {
    const res = await fetch(`${API_BASE}/workflow/transition`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        opportunity_id: oppId,
        to_stage: 'QC',
        notes: 'Operator routed opportunity directly to QC Gate 6.'
      })
    });

    if (res.ok) {
      alert('Deal routed to QC Gate 6!');
      loadWorkbench(oppId);
      refreshOperationsData();
    } else {
      const err = await res.json();
      alert(`Routing Failed: ${err.detail}`);
    }
  } catch (err) {
    console.error('QC routing failed', err);
  }
});

// 5. Generate Live POF
document.getElementById('btn-wb-generate-pof')?.addEventListener('click', async () => {
  const oppId = state.currentWorkbenchOppId;
  if (!oppId) return;

  try {
    const res = await fetch(`${API_BASE}/opportunities/${oppId}/pof/generate`, {
      method: 'POST',
      headers: authHeaders()
    });

    if (!res.ok) {
      alert("Failed to generate POF dossier.");
      return;
    }

    const data = await res.json();
    state.currentPofData = data;

    // Render in modal
    const frame = document.getElementById('pof-preview-frame');
    if (frame) {
      frame.srcdoc = data.html_dossier;
    }

    const jsonCode = document.getElementById('pof-json-code');
    if (jsonCode) {
      jsonCode.innerText = JSON.stringify(data.crm_payload, null, 2);
    }

    document.getElementById('modal-pof-title').innerText = `Dossier: ${data.estate_name} (Case: ${data.case_number})`;
    openModal('modal-pof');
  } catch (err) {
    console.error('POF generation failed', err);
  }
});

// POF Modal Tab Switching
document.getElementById('btn-pof-tab-html')?.addEventListener('click', () => {
  document.getElementById('pof-frame-container').style.display = 'block';
  document.getElementById('pof-json-container').style.display = 'none';
  document.getElementById('btn-pof-tab-html').style.color = '#FFFFFF';
  document.getElementById('btn-pof-tab-json').style.color = 'var(--text-secondary)';
});

document.getElementById('btn-pof-tab-json')?.addEventListener('click', () => {
  document.getElementById('pof-frame-container').style.display = 'none';
  document.getElementById('pof-json-container').style.display = 'block';
  document.getElementById('btn-pof-tab-json').style.color = '#FFFFFF';
  document.getElementById('btn-pof-tab-html').style.color = 'var(--text-secondary)';
});

// Copy CRM JSON Button
document.getElementById('btn-copy-crm-payload')?.addEventListener('click', () => {
  if (state.currentPofData?.crm_payload) {
    navigator.clipboard.writeText(JSON.stringify(state.currentPofData.crm_payload, null, 2));
    alert('CRM Webhook JSON copied to clipboard!');
  }
});

// Open HTML in New Tab
document.getElementById('btn-open-pof-new-tab')?.addEventListener('click', () => {
  if (state.currentWorkbenchOppId) {
    window.open(`${API_BASE}/opportunities/${state.currentWorkbenchOppId}/pof/html`, '_blank');
  }
});

// ============================================================================
// EMBEDDED AI ASSISTANT (COPILOT) CONTROLLER
// ============================================================================

async function queryAIAssistant(promptText) {
  const oppId = state.currentWorkbenchOppId;
  if (!oppId) {
    alert("Please select an opportunity in the Workbench first.");
    return;
  }

  const narrativeEl = document.getElementById('ai-narrative-text');
  const citationsEl = document.getElementById('ai-citations-container');
  const recsEl = document.getElementById('ai-recommendations-container');

  narrativeEl.innerHTML = `<span style="color: var(--accent-cyan);">🤖 Consulting Intelligence Agents (ARE, OIE, CIE, OSE)...</span>`;
  citationsEl.innerHTML = '';
  recsEl.style.display = 'none';

  try {
    const res = await fetch(`${API_BASE}/ai/investigate`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        opportunity_id: oppId,
        query: promptText
      })
    });

    if (!res.ok) {
      narrativeEl.innerText = "Intelligence agent unavailable.";
      return;
    }

    const data = await res.json();
    narrativeEl.innerText = data.narrative;

    // Render citations
    if (data.citations && data.citations.length > 0) {
      citationsEl.innerHTML = data.citations.map(c => `
        <span class="ai-citation-tag" title="${escapeHTML(c.details)}">
          [${escapeHTML(c.source)}] ${escapeHTML(c.citation_id)}
        </span>
      `).join('');
    }

    // Render recommendations
    if (data.recommendations && data.recommendations.length > 0) {
      recsEl.style.display = 'flex';
      recsEl.innerHTML = `<strong>Operational Next Steps:</strong>` + 
        data.recommendations.map(r => `<div>&bull; ${escapeHTML(r)}</div>`).join('');
    }
  } catch (err) {
    console.error('AI query failed', err);
    narrativeEl.innerText = "Error contacting AI Investigator service.";
  }
}

// Bind AI Prompt Pills
document.querySelectorAll('.ai-pill').forEach(pill => {
  pill.addEventListener('click', () => {
    const promptText = pill.getAttribute('data-prompt');
    const input = document.getElementById('ai-input-query');
    if (input) input.value = promptText;
    queryAIAssistant(promptText);
  });
});

// Bind Custom AI Submit
document.getElementById('btn-ai-submit')?.addEventListener('click', () => {
  const input = document.getElementById('ai-input-query');
  if (input && input.value.trim()) {
    queryAIAssistant(input.value.trim());
  }
});

// Standalone AI Investigator Console Submit
document.getElementById('btn-ai-standalone-submit')?.addEventListener('click', async () => {
  const q = document.getElementById('ai-standalone-query')?.value?.trim();
  const respBox = document.getElementById('ai-standalone-response');
  if (!q || !respBox) return;

  respBox.innerHTML = `<span style="color: var(--accent-cyan);">Running deep multi-agent synthesis...</span>`;
  const oppId = state.currentWorkbenchOppId || state.allOpportunities[0]?.id;

  if (!oppId) {
    respBox.innerText = "No opportunities available for context.";
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/ai/investigate`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ opportunity_id: oppId, query: q })
    });
    const data = await res.json();
    respBox.textContent = '';
    const narrDiv = document.createElement('div');
    narrDiv.style.cssText = "font-size: 14px; line-height: 1.6; color: #F8FAFC;";
    narrDiv.textContent = data.narrative || '';
    respBox.appendChild(narrDiv);

    if (Array.isArray(data.citations) && data.citations.length > 0) {
      const citeDiv = document.createElement('div');
      citeDiv.style.cssText = "margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap;";
      data.citations.forEach(c => {
        const tag = document.createElement('span');
        tag.className = 'ai-citation-tag';
        tag.textContent = `[${c.source}] ${c.citation_id}: ${c.details}`;
        citeDiv.appendChild(tag);
      });
      respBox.appendChild(citeDiv);
    }
  } catch (err) {
    respBox.innerText = "Failed to run autonomous investigation.";
  }
});

// ============================================================================
// APP 4: CLIENT PORTAL CONTROLLER (REVENUE PRODUCT & TELEMETRY ENGINE)
// ============================================================================

async function loadClientPortal() {
  try {
    // 1. Load Partner Profile & Delivery Quotas
    const profileRes = await fetch(`${API_BASE}/client/partner-profile`);
    if (profileRes.ok) {
      const prof = await profileRes.json();
      const badgeEl = document.getElementById('cp-license-badge');
      if (badgeEl) badgeEl.innerText = `🏛️ Exclusive License: ${prof.exclusive_county}`;
      
      const nameEl = document.getElementById('client-partner-name');
      if (nameEl) nameEl.innerText = prof.partner_name;

      const quotaTextEl = document.getElementById('cp-quota-text');
      if (quotaTextEl) quotaTextEl.innerText = `${prof.quota_fulfilled_count} / ${prof.monthly_quota_target} Delivered`;

      const quotaPctEl = document.getElementById('cp-quota-pct');
      if (quotaPctEl) quotaPctEl.innerText = `${prof.quota_progress_pct}% Target Met`;

      const barEl = document.getElementById('cp-quota-bar');
      if (barEl) barEl.style.width = `${prof.quota_progress_pct}%`;
    }

    // 2. Load Telemetry Statistics
    const statsRes = await fetch(`${API_BASE}/client/telemetry/stats`);
    if (statsRes.ok) {
      const stats = await statsRes.json();
      const elOffers = document.getElementById('cp-stat-offers');
      if (elOffers) elOffers.innerText = stats.offer_count;

      const elVolume = document.getElementById('cp-stat-offer-volume');
      if (elVolume) elVolume.innerText = `$${Number(stats.total_offer_volume || 0).toLocaleString()} pipeline volume`;

      const elContracts = document.getElementById('cp-stat-contracts');
      if (elContracts) elContracts.innerText = stats.contract_count;

      const elWinRate = document.getElementById('cp-stat-win-rate');
      if (elWinRate) elWinRate.innerText = `Win Rate: ${stats.win_rate_pct}%`;

      const elSpeed = document.getElementById('cp-stat-speed');
      if (elSpeed) elSpeed.innerText = `${stats.avg_response_time_hours}h`;
    }

    // 3. Load Filtered Feed
    const searchVal = document.getElementById('client-feed-search')?.value?.trim() || '';
    const feedUrl = `${API_BASE}/client/feed?filter_type=${state.clientFilter}${searchVal ? `&search=${encodeURIComponent(searchVal)}` : ''}`;
    const feedRes = await fetch(feedUrl);
    if (!feedRes.ok) return;
    const feed = await feedRes.json();
    state.clientFeed = feed;

    const activeCountEl = document.getElementById('cp-stat-active');
    if (activeCountEl) activeCountEl.innerText = feed.length;

    const container = document.getElementById('client-feed-container');
    if (!container) return;

    if (feed.length === 0) {
      container.innerHTML = `
        <div class="text-center text-muted" style="grid-column: 1 / -1; padding: 40px; background: var(--bg-secondary); border-radius: var(--radius-md);">
          No exclusive opportunities matching '${escapeHTML(state.clientFilter)}' filter at this time.
        </div>
      `;
      return;
    }

    container.innerHTML = feed.map(item => {
      const isPrioA = item.priority_tier?.includes('A');
      const stage = item.funnel_stage || 'NEW_DISPATCH';

      // Helper to compute node class for 5-step stepper
      const getStepClass = (stepName, stepIndex) => {
        const order = ['CONTACTED', 'CONVERSATION', 'OFFER', 'CONTRACT'];
        const currIndex = order.indexOf(stage);
        if (stage === 'DEAD') {
          return stepName === 'DEAD' ? 'step-node-btn dead-state' : 'step-node-btn';
        }
        if (stepName === 'DEAD') return 'step-node-btn';
        if (currIndex > stepIndex) return 'step-node-btn completed';
        if (currIndex === stepIndex) return 'step-node-btn active';
        return 'step-node-btn';
      };

      return `
      <div class="client-feed-card" id="card-${escapeHTML(item.id)}">
        <!-- Top Header & Net Equity -->
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px;">
          <div>
            <div style="display: flex; gap: 6px; align-items: center; margin-bottom: 4px;">
              <span class="badge ${isPrioA ? 'badge-accent' : 'badge-warning'}">${escapeHTML(item.priority_tier)}</span>
              <span class="code-badge" style="font-size: 10px;">${escapeHTML(item.case_number)}</span>
              ${isPrioA ? '<span class="badge badge-danger" style="font-size: 10px;">⚡ 4h Flash</span>' : ''}
            </div>
            <h4 style="font-size: 16px; font-weight: 700; color: #FFFFFF;">${escapeHTML(item.situs_address)}</h4>
            <p style="font-size: 11.5px; color: var(--text-muted);">${escapeHTML(item.estate_name)} (${escapeHTML(item.county)} County, WA)</p>
          </div>
          <div style="text-align: right; background: rgba(16, 185, 129, 0.08); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(16, 185, 129, 0.2);">
            <div class="mono text-emerald" style="font-size: 20px; font-weight: 800;">$${Number(item.net_equity || 0).toLocaleString()}</div>
            <div style="font-size: 10px; color: var(--text-secondary); font-weight: 600;">${escapeHTML(item.net_equity_pct)}% Net Equity Spread</div>
          </div>
        </div>

        <!-- Financial Spreads -->
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; font-size: 11.5px; background: var(--bg-surface); padding: 10px; border-radius: 6px; border: 1px solid var(--border-subtle);">
          <div>
            <span style="color: var(--text-muted); display: block; font-size: 10px;">EST. ARV</span>
            <strong>$${Number(item.avm || 0).toLocaleString()}</strong>
          </div>
          <div>
            <span style="color: var(--text-muted); display: block; font-size: 10px;">TARGET MAO</span>
            <strong class="text-accent mono">$${Number(item.target_mao || 0).toLocaleString()}</strong>
          </div>
          <div>
            <span style="color: var(--text-muted); display: block; font-size: 10px;">PARCEL APN</span>
            <span class="mono">${escapeHTML(item.apn || '022128...')}</span>
          </div>
        </div>

        <!-- Statutory Authority Verification -->
        <div class="client-authority-pill">
          <span>⚖️</span>
          <span><strong>${escapeHTML(item.authority_tier)}:</strong> Nonintervention Powers Confirmed under ${escapeHTML(item.statutory_basis)} (Autonomous Personal Representative)</span>
        </div>

        <!-- Decision Maker & Outreach Strategy -->
        <div style="font-size: 12px; display: flex; flex-direction: column; gap: 4px;">
          <div><strong>Personal Representative:</strong> ${escapeHTML(item.primary_decision_maker)} (${escapeHTML(item.relationship)}) — <span class="text-emerald">${escapeHTML(item.occupancy)}</span></div>
          <div class="script-quote-box">
            "${escapeHTML(item.recommended_script || 'Empathetic as-is cash convenience proposal with zero cleanout burden.')}"
          </div>
        </div>

        <!-- Action Control Strip -->
        <div style="display: flex; gap: 8px; align-items: center; justify-content: space-between;">
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-sm btn-primary" onclick="openClientPof('${escapeHTML(item.id)}')">
              📄 View Full POF
            </button>
            <button class="btn btn-sm btn-secondary" onclick="exportToCRM('${escapeHTML(item.id)}')" title="Dispatch to GoHighLevel CRM">
              ⚡ Push to CRM
            </button>
            <button class="btn btn-sm btn-secondary" onclick="window.open('${API_BASE}/opportunities/${escapeHTML(item.id)}/pof/html', '_blank')">
              🖨️ PDF
            </button>
          </div>
          <span class="badge ${stage === 'CONTRACT' ? 'badge-success' : (stage === 'OFFER' ? 'badge-warning' : 'badge-accent')}">
            Status: ${escapeHTML(stage)}
          </span>
        </div>

        <!-- Interactive 5-Step Disposition Telemetry Stepper -->
        <div>
          <div style="font-size: 10px; color: var(--text-muted); margin-bottom: 4px; display: flex; justify-content: space-between;">
            <span>DISPOSITION TELEMETRY PIPELINE:</span>
            <span style="color: #67E8F9; font-weight: 600;">Click to advance funnel</span>
          </div>
          <div class="client-disposition-stepper">
            <button class="${getStepClass('CONTACTED', 0)}" onclick="openClientFeedbackModal('${escapeHTML(item.id)}', 'CONTACTED')">
              <span class="node-dot"></span>
              <span>1. Contact</span>
            </button>
            <span style="color: var(--border-subtle); font-size: 10px;">➔</span>
            <button class="${getStepClass('CONVERSATION', 1)}" onclick="openClientFeedbackModal('${escapeHTML(item.id)}', 'CONVERSATION')">
              <span class="node-dot"></span>
              <span>2. Consult</span>
            </button>
            <span style="color: var(--border-subtle); font-size: 10px;">➔</span>
            <button class="${getStepClass('OFFER', 2)}" onclick="openClientFeedbackModal('${escapeHTML(item.id)}', 'OFFER')">
              <span class="node-dot"></span>
              <span>3. Offer</span>
            </button>
            <span style="color: var(--border-subtle); font-size: 10px;">➔</span>
            <button class="${getStepClass('CONTRACT', 3)}" onclick="openClientFeedbackModal('${escapeHTML(item.id)}', 'CONTRACT')">
              <span class="node-dot"></span>
              <span>4. Contract</span>
            </button>
            <span style="color: var(--border-subtle); font-size: 10px;">|</span>
            <button class="${getStepClass('DEAD', 4)}" onclick="openClientFeedbackModal('${escapeHTML(item.id)}', 'DEAD')">
              <span class="node-dot"></span>
              <span>5. Dead</span>
            </button>
          </div>
        </div>
      </div>
    `;
    }).join('');
  } catch (err) {
    console.error('Failed to load client portal', err);
  }
}

// Client search listener
const clientSearchInput = document.getElementById('client-feed-search');
if (clientSearchInput) {
  clientSearchInput.addEventListener('input', () => {
    loadClientPortal();
  });
}

// Client filter tabs listener
document.querySelectorAll('[data-client-filter]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('[data-client-filter]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.clientFilter = btn.getAttribute('data-client-filter');
    loadClientPortal();
  });
});

// View POF from client portal
window.openClientPof = function(oppId) {
  state.currentWorkbenchOppId = oppId;
  document.getElementById('btn-wb-generate-pof')?.click();
};

// Dispatch to CRM
window.exportToCRM = async function(oppId) {
  try {
    const res = await fetch(`${API_BASE}/client/export/crm`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        opportunity_id: oppId,
        crm_platform: 'GoHighLevel'
      })
    });

    if (res.ok) {
      const data = await res.json();
      alert(`Deal Dispatched to ${data.crm_platform}!\nWebhook endpoint triggered successfully with canonical POF payload.`);
    } else {
      alert("Failed to export to CRM.");
    }
  } catch (err) {
    console.error('CRM export error', err);
  }
};

// Open Client Feedback / Offer Modal
window.openClientFeedbackModal = function(oppId, targetStage, address) {
  document.getElementById('cf-opp-id').value = oppId;
  const opp = state.clientFeed?.find(f => f.id === oppId);
  const addr = address || (opp ? opp.situs_address : oppId.substring(0, 8));
  document.getElementById('cf-opp-label').innerText = addr;
  
  const stageSelect = document.getElementById('cf-stage');
  if (stageSelect) {
    stageSelect.value = targetStage;
    updateFeedbackModalFields(targetStage);
  }

  openModal('modal-client-feedback');
};

function updateFeedbackModalFields(stage) {
  const offerGroup = document.getElementById('cf-group-offer');
  const closeGroup = document.getElementById('cf-group-close-days');
  const deadGroup = document.getElementById('cf-group-dead');

  if (stage === 'OFFER' || stage === 'CONTRACT') {
    if (offerGroup) offerGroup.style.display = 'flex';
    if (closeGroup) closeGroup.style.display = 'flex';
    if (deadGroup) deadGroup.style.display = 'none';
  } else if (stage === 'DEAD') {
    if (offerGroup) offerGroup.style.display = 'none';
    if (closeGroup) closeGroup.style.display = 'none';
    if (deadGroup) deadGroup.style.display = 'flex';
  } else {
    if (offerGroup) offerGroup.style.display = 'none';
    if (closeGroup) closeGroup.style.display = 'none';
    if (deadGroup) deadGroup.style.display = 'none';
  }
}

// Stage select change listener in modal
document.getElementById('cf-stage')?.addEventListener('change', (e) => {
  updateFeedbackModalFields(e.target.value);
});

// Submit Client Feedback / Offer
document.getElementById('btn-submit-client-feedback')?.addEventListener('click', async () => {
  const oppId = document.getElementById('cf-opp-id').value;
  const stage = document.getElementById('cf-stage').value;
  const offerAmount = parseFloat(document.getElementById('cf-offer-amount').value) || null;
  const closeDays = parseInt(document.getElementById('cf-close-days').value) || null;
  const deadReason = stage === 'DEAD' ? document.getElementById('cf-dead-reason').value : null;
  const notes = document.getElementById('cf-notes').value.trim();

  try {
    const res = await fetch(`${API_BASE}/client/feedback`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        opportunity_id: oppId,
        stage: stage,
        client_name: 'Sound Capital Acquisitions',
        offer_amount: offerAmount,
        estimated_close_days: closeDays,
        dead_reason: deadReason,
        notes: notes
      })
    });

    if (res.ok) {
      closeModal('modal-client-feedback');
      loadClientPortal();
      refreshOperationsData();
      alert(`Telemetry Confirmed: [${stage}] logged into reinforcement learning engine.`);
    } else {
      const err = await res.json();
      alert(`Failed: ${err.detail}`);
    }
  } catch (err) {
    console.error('Feedback submit failed', err);
  }
});

// ============================================================================
// SLIDE-OUT DETAIL DRAWER & AUDIT TIMELINE
// ============================================================================

window.openDrawerForOpp = async function(oppId) {
  const drawer = document.getElementById('drawer-detail');
  if (!drawer) return;

  drawer.classList.add('open');
  document.getElementById('drawer-sub').innerText = oppId.substring(0, 8);

  try {
    const res = await fetch(`${API_BASE}/opportunities/${oppId}`);
    if (res.ok) {
      const opp = await res.json();
      document.getElementById('drawer-case-num').innerText = opp.case_id;
      document.getElementById('drawer-county').innerText = opp.county_id;
      document.getElementById('drawer-stage').innerText = opp.workflow_stage;
      document.getElementById('drawer-score').innerText = `${opp.score}/100`;
    }

    // Fetch audit timeline
    const logRes = await fetch(`${API_BASE}/workflow/audit-logs/${oppId}`);
    const timelineEl = document.getElementById('drawer-timeline');
    if (logRes.ok && timelineEl) {
      const logs = await logRes.json();
      if (logs.length === 0) {
        timelineEl.innerHTML = `<div class="text-muted" style="font-size: 12px;">Initialized at stage NEW. No downstream transitions recorded yet.</div>`;
      } else {
        timelineEl.innerHTML = logs.map(l => `
          <div class="timeline-event">
            <div class="timeline-marker"></div>
            <div class="timeline-content">
              <div style="display: flex; justify-content: space-between; font-weight: 600; color: #FFFFFF;">
                <span>${escapeHTML(l.from_stage)} ➔ ${escapeHTML(l.to_stage)}</span>
                <span class="mono" style="font-size: 10px; color: var(--text-muted);">${new Date(l.timestamp).toLocaleTimeString()}</span>
              </div>
              <div style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">
                Operator: <strong>${escapeHTML(l.transitioned_by)}</strong>
              </div>
              ${l.notes ? `<div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;"><em>&quot;${escapeHTML(l.notes)}&quot;</em></div>` : ''}
            </div>
          </div>
        `).join('');
      }
    }

    // Bind drawer buttons
    const btnWb = document.getElementById('btn-drawer-open-workbench');
    if (btnWb) {
      btnWb.onclick = () => {
        drawer.classList.remove('open');
        openWorkbenchForOpp(oppId);
      };
    }

    const btnTrans = document.getElementById('btn-drawer-transition');
    if (btnTrans) {
      btnTrans.onclick = () => {
        drawer.classList.remove('open');
        openTransitionModal(oppId);
      };
    }
  } catch (err) {
    console.error('Failed to open drawer', err);
  }
};

document.getElementById('btn-close-drawer')?.addEventListener('click', () => {
  document.getElementById('drawer-detail')?.classList.remove('open');
});

// ============================================================================
// MODALS LOGIC (CREATE CASE, TRANSITION, EXCEPTION)
// ============================================================================

window.openTransitionModal = async function(oppId) {
  document.getElementById('trans-opp-id').value = oppId;
  document.getElementById('trans-opp-label').innerText = oppId.substring(0, 8);

  try {
    const oppRes = await fetch(`${API_BASE}/opportunities/${oppId}`);
    if (oppRes.ok) {
      const opp = await oppRes.json();
      document.getElementById('trans-current-stage').innerText = opp.workflow_stage;

      const transRes = await fetch(`${API_BASE}/workflow/allowed-transitions/${opp.workflow_stage}`);
      const select = document.getElementById('trans-target-stage');
      if (transRes.ok) {
        const transData = await transRes.json();
        select.innerHTML = transData.allowed_transitions.map(t => `<option value="${escapeHTML(t)}">${escapeHTML(t)}</option>`).join('');
      }
    }
  } catch (err) {
    console.error(err);
  }

  openModal('modal-transition');
};

document.getElementById('btn-submit-transition')?.addEventListener('click', async () => {
  const oppId = document.getElementById('trans-opp-id').value;
  const toStage = document.getElementById('trans-target-stage').value;
  const notes = document.getElementById('trans-notes').value;

  try {
    const res = await fetch(`${API_BASE}/workflow/transition`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ opportunity_id: oppId, to_stage: toStage, notes: notes })
    });

    if (res.ok) {
      closeModal('modal-transition');
      refreshOperationsData();
      if (state.currentWorkbenchOppId === oppId) {
        loadWorkbench(oppId);
      }
    } else {
      const err = await res.json();
      alert(`Transition Failed: ${err.detail}`);
    }
  } catch (err) {
    console.error(err);
  }
});

// Ingest Case Modal
document.getElementById('btn-open-create-case')?.addEventListener('click', async () => {
  try {
    const res = await fetch(`${API_BASE}/counties`);
    if (res.ok) {
      const counties = await res.json();
      const countySelect = document.getElementById('case-county');
      countySelect.innerHTML = counties.map(c => `<option value="${escapeHTML(c.id)}">${escapeHTML(c.name)} (${escapeHTML(c.state)})</option>`).join('');
    }
  } catch (err) {
    console.error(err);
  }
  openModal('modal-create-case');
});

document.getElementById('btn-submit-case')?.addEventListener('click', async () => {
  const caseNum = document.getElementById('case-num').value.trim();
  const countyId = document.getElementById('case-county').value;
  const decedent = document.getElementById('case-decedent').value.trim();
  const filingDate = document.getElementById('case-date').value || new Date().toISOString().split('T')[0];
  const autoCreateOpp = document.getElementById('case-auto-create-opp').checked;

  if (!caseNum || !decedent) {
    alert("Please provide both Case Number and Decedent Name.");
    return;
  }

  try {
    const caseRes = await fetch(`${API_BASE}/cases`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        case_number: caseNum,
        county_id: countyId,
        decedent: decedent,
        filing_date: filingDate
      })
    });

    if (!caseRes.ok) {
      const err = await caseRes.json();
      alert(`Case Ingestion Failed: ${err.detail}`);
      return;
    }

    const newCase = await caseRes.json();

    if (autoCreateOpp) {
      await fetch(`${API_BASE}/opportunities`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          case_id: newCase.id,
          county_id: countyId,
          workflow_stage: 'NEW',
          priority: 'Priority A',
          authority_status: 'Tier 1: Court Certified',
          score: 88
        })
      });
    }

    closeModal('modal-create-case');
    refreshOperationsData();
    alert(`Case ${caseNum} successfully ingested into Gieni OS foundation.`);
  } catch (err) {
    console.error('Case ingestion failed', err);
  }
});

// Submit Exception Task
document.getElementById('btn-submit-exception')?.addEventListener('click', async () => {
  const oppId = document.getElementById('exc-opp-id').value;
  const excType = document.getElementById('exc-type').value;
  const severity = document.getElementById('exc-severity').value;
  const assignee = document.getElementById('exc-assignee').value.trim();
  const notes = document.getElementById('exc-notes').value.trim();

  try {
    const res = await fetch(`${API_BASE}/exceptions`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        opportunity_id: oppId,
        type: excType,
        severity: severity,
        assignee: assignee || getRole(),
        notes: notes
      })
    });

    if (res.ok) {
      closeModal('modal-create-exception');
      refreshOperationsData();
      alert('Exception / Research Task recorded.');
    }
  } catch (err) {
    console.error('Failed to log exception', err);
  }
});

// Ingest opportunity for existing case
window.ingestOpportunityForCase = async function(caseId, countyId) {
  try {
    const res = await fetch(`${API_BASE}/opportunities`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        case_id: caseId,
        county_id: countyId,
        workflow_stage: 'NEW',
        priority: 'Priority A',
        authority_status: 'Tier 1: Court Certified',
        score: 90
      })
    });
    if (res.ok) {
      refreshOperationsData();
      alert("Opportunity created in stage NEW.");
    }
  } catch (err) {
    console.error(err);
  }
};

// Global Refresh Button
document.getElementById('btn-refresh')?.addEventListener('click', () => {
  if (state.activeApp === 'operations-center') {
    refreshOperationsData();
  } else if (state.activeApp === 'opportunity-workbench') {
    initWorkbench();
  } else if (state.activeApp === 'client-portal') {
    loadClientPortal();
  }
});

// Initialize on Load
document.addEventListener('DOMContentLoaded', () => {
  refreshOperationsData();
});
