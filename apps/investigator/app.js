/**
 * Gieni OS | AI Investigator (App 3)
 * Multi-Agent Reasoning & Cross-Examination Console
 */

let currentOppId = null;
let opportunities = [];

document.addEventListener('DOMContentLoaded', async () => {
  initListeners();
  await Promise.all([
    loadOpportunities(),
    loadLLMStatus()
  ]);
});

function initListeners() {
  const select = document.getElementById('inv-opp-select');
  if (select) {
    select.addEventListener('change', (e) => {
      selectOpportunity(e.target.value);
    });
  }

  // Run button
  document.getElementById('btn-run-investigation')?.addEventListener('click', () => {
    const q = document.getElementById('investigator-query-input')?.value?.trim();
    if (q) runInvestigation(q);
  });

  // Enter key in input
  document.getElementById('investigator-query-input')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const q = e.target.value.trim();
      if (q) runInvestigation(q);
    }
  });

  // Quick probe pills
  document.querySelectorAll('.ai-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const probe = pill.getAttribute('data-probe');
      if (probe) {
        const input = document.getElementById('investigator-query-input');
        if (input) input.value = probe;
        runInvestigation(probe);
      }
    });
  });
}

async function loadOpportunities() {
  try {
    const res = await fetch('/api/opportunities');
    if (res.ok) {
      opportunities = await res.json();
    }
  } catch (err) {
    console.error('Error fetching opportunities list:', err);
  }

  const select = document.getElementById('inv-opp-select');
  if (!opportunities || opportunities.length === 0) {
    if (select) {
      select.innerHTML = '<option value="">No Active Deals (Ingest filings via Ops Center)</option>';
    }
    document.getElementById('target-estate-name').textContent = 'No Deals Ingested';
    document.getElementById('target-case-id').textContent = 'NONE';
    document.getElementById('target-county').textContent = 'N/A';
    document.getElementById('target-priority').textContent = 'EMPTY';
    return;
  }

  if (select) {
    select.innerHTML = opportunities.map(opp => {
      const name = opp.estate_name || (opp.decedent ? `Estate of ${opp.decedent}` : opp.id);
      const cty = opp.county_name || opp.county_id || 'WA';
      return `<option value="${opp.id}">${name} — ${cty} County</option>`;
    }).join('');
  }

  // Check URL params
  const urlParams = new URLSearchParams(window.location.search);
  const targetId = urlParams.get('oppId') || opportunities[0]?.id;
  if (targetId) {
    selectOpportunity(targetId);
  }
}

function selectOpportunity(oppId) {
  currentOppId = oppId;
  const opp = opportunities.find(o => o.id === oppId) || opportunities[0];

  const select = document.getElementById('inv-opp-select');
  if (select) select.value = oppId;

  const estateName = opp.estate_name || (opp.decedent ? `Estate of ${opp.decedent}` : 'Estate of Record');
  const cty = opp.county_name || opp.county_id || 'WA';

  document.getElementById('target-estate-name').textContent = estateName;
  document.getElementById('target-case-id').textContent = opp.case_number || opp.id;
  document.getElementById('target-county').textContent = `${cty} County`;
  document.getElementById('target-priority').textContent = opp.priority || 'Priority A';
}

async function runInvestigation(query) {
  if (!currentOppId) {
    if (!opportunities || opportunities.length === 0) return;
    currentOppId = opportunities[0]?.id;
  }

  const resultCard = document.getElementById('investigation-result-card');
  const narrativeBox = document.getElementById('res-narrative');
  const queryEcho = document.getElementById('res-query-echo');

  if (resultCard) resultCard.style.display = 'block';
  if (queryEcho) queryEcho.textContent = `Query: "${query}"`;
  if (narrativeBox) narrativeBox.innerHTML = '<div style="color: var(--text-muted);">Agents collaborating: Parsing RCW Title 11, deed chains, and court dockets...</div>';

  try {
    const res = await fetch('/api/ai/investigate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-clerk-user-id': 'user_ai_investigator',
        'x-clerk-role': 'Research Lead'
      },
      body: JSON.stringify({
        opportunity_id: currentOppId,
        query: query,
        question: query
      })
    });

    if (res.ok) {
      const data = await res.json();
      renderInvestigationResult(data);
      return;
    }
  } catch (err) {
    console.error('API error querying investigation:', err);
  }

  renderInvestigationResult({
    query: query,
    confidence_score: 0.0,
    connected_agents: ['API_OFFLINE'],
    narrative: `Unable to complete investigation. Please ensure the backend server is reachable and the opportunity exists in the database.`,
    citations: [],
    recommendations: ['Verify system connectivity to Gieni OS API.']
  });
}

function renderInvestigationResult(data) {
  // Provider badge & Latency
  const provEl = document.getElementById('res-provider-badge');
  if (provEl) {
    provEl.textContent = data.model_name || data.provider_used || 'STATUTORY_ARE';
  }
  const latencyEl = document.getElementById('res-latency');
  if (latencyEl) {
    latencyEl.textContent = data.latency_ms ? `${Math.round(data.latency_ms)}ms` : '--';
  }

  // Confidence
  const confEl = document.getElementById('res-confidence');
  if (confEl) {
    const pct = Math.round((data.confidence_score || 0.95) * 100);
    confEl.textContent = `${pct}%`;
  }

  // Active agents
  const agentsEl = document.getElementById('res-active-agents');
  if (agentsEl && Array.isArray(data.connected_agents)) {
    agentsEl.textContent = '';
    data.connected_agents.forEach(a => {
      const span = document.createElement('span');
      span.className = 'badge badge-accent';
      span.style.marginRight = '6px';
      span.textContent = a;
      agentsEl.appendChild(span);
    });
  }

  // Narrative
  const narrativeEl = document.getElementById('res-narrative');
  if (narrativeEl) {
    narrativeEl.textContent = data.narrative || '';
  }

  // Citations
  const citationsList = document.getElementById('res-citations-list');
  if (citationsList) {
    citationsList.textContent = '';
    if (Array.isArray(data.citations) && data.citations.length > 0) {
      data.citations.forEach(c => {
        const item = document.createElement('div');
        item.style.cssText = "background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;";
        const header = document.createElement('div');
        header.style.cssText = "display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;";
        const src = document.createElement('span');
        src.style.cssText = "font-weight: 600; font-size: 12px; color: #FFFFFF;";
        src.textContent = c.source || '';
        const idBadge = document.createElement('span');
        idBadge.className = "code-badge";
        idBadge.style.fontSize = "10px";
        idBadge.textContent = c.citation_id || '';
        header.appendChild(src);
        header.appendChild(idBadge);
        const details = document.createElement('div');
        details.style.cssText = "font-size: 12px; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace;";
        details.textContent = c.details || '';
        item.appendChild(header);
        item.appendChild(details);
        citationsList.appendChild(item);
      });
    } else {
      const emptyDiv = document.createElement('div');
      emptyDiv.style.cssText = "font-size: 12px; color: var(--text-muted);";
      emptyDiv.textContent = 'No external citations required.';
      citationsList.appendChild(emptyDiv);
    }
  }

  // Recommendations
  const recsList = document.getElementById('res-recommendations-list');
  if (recsList) {
    recsList.textContent = '';
    if (Array.isArray(data.recommendations) && data.recommendations.length > 0) {
      data.recommendations.forEach(r => {
        const li = document.createElement('li');
        li.style.marginBottom = '8px';
        li.textContent = r;
        recsList.appendChild(li);
      });
    } else {
      const li = document.createElement('li');
      li.textContent = 'Proceed with standard institutional workflow.';
      recsList.appendChild(li);
    }
  }
}

async function loadLLMStatus() {
  const badgeLabel = document.getElementById('llm-provider-label');
  const badgeContainer = document.getElementById('llm-provider-badge');
  if (!badgeLabel) return;

  try {
    const res = await fetch('/api/llm/status');
    if (res.ok) {
      const data = await res.json();
      const active = data.active_provider;
      const model = data.active_model;
      if (active === 'AZURE_OPENAI') {
        badgeLabel.textContent = `Azure OpenAI: ${model}`;
        if (badgeContainer) {
          badgeContainer.style.background = 'rgba(16, 185, 129, 0.15)';
          badgeContainer.style.borderColor = 'rgba(16, 185, 129, 0.3)';
          badgeContainer.style.color = '#34d399';
        }
      } else if (active === 'OLLAMA') {
        badgeLabel.textContent = `Ollama: ${model}`;
        if (badgeContainer) {
          badgeContainer.style.background = 'rgba(245, 158, 11, 0.15)';
          badgeContainer.style.borderColor = 'rgba(245, 158, 11, 0.3)';
          badgeContainer.style.color = '#fbbf24';
        }
      } else {
        badgeLabel.textContent = `RCW Title 11 Engine`;
        if (badgeContainer) {
          badgeContainer.style.background = 'rgba(99, 102, 241, 0.15)';
          badgeContainer.style.borderColor = 'rgba(99, 102, 241, 0.3)';
          badgeContainer.style.color = '#818cf8';
        }
      }
      return;
    }
  } catch (err) {
    console.error('Error fetching LLM status:', err);
  }

  badgeLabel.textContent = 'Statutory Engine (Offline)';
}

