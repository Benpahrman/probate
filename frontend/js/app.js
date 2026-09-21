const API_BASE = "http://localhost:8000/api/v1";
let currentTab = "pipeline";
let cachedOpportunities = [];

document.addEventListener("DOMContentLoaded", () => {
    switchTab("pipeline");
});

function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll("#main-navigation button").forEach(b => {
        b.className = "w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white nav-btn";
    });
    const activeBtn = document.getElementById(`tab-${tab}`);
    if (activeBtn) {
        activeBtn.className = "w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg bg-indigo-600 text-white shadow-lg shadow-indigo-600/20 nav-btn";
    }

    if (tab === "pipeline") renderPipelineView();
    else if (tab === "county") renderCountyView();
    else if (tab === "exceptions") renderExceptionsView();
    else if (tab === "investigator") renderInvestigatorView();
}

function refreshCurrentTab() {
    switchTab(currentTab);
}

// -------------------------------------------------------------
// 1. PIPELINE WORKBENCH VIEW
// -------------------------------------------------------------
async function renderPipelineView() {
    document.getElementById("workspace-title").innerText = "14-Stage Opportunity Pipeline";
    const container = document.getElementById("view-container");
    container.innerHTML = `
        <div class="flex items-center space-x-3 text-slate-400 py-8">
            <svg class="animate-spin h-5 w-5 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span>Querying live pipeline state from database...</span>
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/opportunities?limit=50`);
        if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        cachedOpportunities = await res.json();

        if (cachedOpportunities.length === 0) {
            container.innerHTML = `
                <div class="text-center py-20 border-2 border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
                    <div class="text-4xl mb-3">📁</div>
                    <h3 class="text-base font-semibold text-white">Zero Active Opportunities</h3>
                    <p class="text-slate-400 text-sm mt-1">Court docket pipeline is currently empty.</p>
                    <button onclick="switchTab('county')" class="mt-5 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold shadow-lg shadow-indigo-600/30 transition">
                        Trigger Court Intake Scraper
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="overflow-x-auto bg-slate-900/90 border border-slate-800 rounded-2xl shadow-xl backdrop-blur">
                <table class="w-full text-left text-sm text-slate-300">
                    <thead class="bg-slate-800/80 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                        <tr>
                            <th class="px-6 py-4">Case # / Decedent</th>
                            <th class="px-6 py-4">Situs Address / APN</th>
                            <th class="px-6 py-4">Current OLE Stage</th>
                            <th class="px-6 py-4">Viability / DFS</th>
                            <th class="px-6 py-4">Priority Tier</th>
                            <th class="px-6 py-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800/60">
                        ${cachedOpportunities.map(o => `
                            <tr class="hover:bg-slate-800/40 transition">
                                <td class="px-6 py-4 font-medium text-white">
                                    <div class="font-mono text-indigo-300">${o.case_number}</div>
                                    <div class="text-xs text-slate-400 mt-0.5">${o.decedent_name}</div>
                                </td>
                                <td class="px-6 py-4">
                                    <div class="text-slate-200">${o.street}</div>
                                    <div class="text-xs text-slate-500 font-mono mt-0.5">APN: ${o.apn}</div>
                                </td>
                                <td class="px-6 py-4">
                                    <span class="px-2.5 py-1 text-xs font-semibold rounded-md bg-slate-800 text-indigo-300 border border-slate-700 font-mono">
                                        ${o.lifecycle_stage}
                                    </span>
                                </td>
                                <td class="px-6 py-4">
                                    <span class="font-bold text-white text-base">${o.composite_viability_score}</span>
                                    <span class="text-xs text-rose-400 font-semibold ml-1">-${o.deal_friction_score} DFS</span>
                                </td>
                                <td class="px-6 py-4">
                                    <span class="px-2.5 py-1 text-xs font-black rounded-md badge-${o.priority_tier.toLowerCase().replace('_', '-')}">
                                        ${o.priority_tier}
                                    </span>
                                </td>
                                <td class="px-6 py-4 text-right space-x-2">
                                    <button onclick="executeQCAudit('${o.opportunity_id}')" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-md text-xs font-semibold shadow-sm transition">
                                        Audit 6 Gates
                                    </button>
                                    <button onclick="openTransitionModal('${o.opportunity_id}')" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-md text-xs font-semibold border border-slate-700 transition">
                                        Advance Stage
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (err) {
        container.innerHTML = `
            <div class="p-6 bg-rose-950/40 border border-rose-800/80 text-rose-200 rounded-xl space-y-2">
                <div class="font-bold flex items-center space-x-2">
                    <span>⚠️</span>
                    <span>API Connection Error</span>
                </div>
                <div class="text-xs">${err.message}</div>
                <div class="text-xs text-rose-400">Verify that the backend server is running on http://localhost:8000.</div>
            </div>
        `;
    }
}

// -------------------------------------------------------------
// 2. QUALITY CONTROL & STATE TRANSITIONS
// -------------------------------------------------------------
async function executeQCAudit(opportunityId) {
    showModal("Evaluating Quality Gates", `
        <div class="flex items-center space-x-3 py-4 text-slate-300">
            <svg class="animate-spin h-5 w-5 text-indigo-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span>Executing 6 Deterministic Quality Assurance Gates against live database...</span>
        </div>
    `, []);

    try {
        const res = await fetch(`${API_BASE}/opportunities/${opportunityId}/execute-qc`, { method: "POST" });
        const data = await res.json();
        
        let message = "";
        if (data.is_fully_certified) {
            message = `
                <div class="p-5 bg-emerald-950/60 border border-emerald-800 text-emerald-200 rounded-xl space-y-2">
                    <div class="font-bold text-base flex items-center space-x-2 text-emerald-300">
                        <span>✓</span>
                        <span>Full Gate Certification Passed!</span>
                    </div>
                    <div class="text-xs text-slate-300 leading-relaxed">
                        The opportunity cleared all 6 deterministic gates in sequence (Docket Integrity, Title Reconciliation, Net Equity, Fiduciary Authority, Contact Scrubbing, and Partner Buy-box).
                    </div>
                    <div class="pt-2 border-t border-emerald-900/60 flex items-center justify-between text-xs">
                        <span>New Stage: <strong class="text-emerald-300 font-mono">${data.current_lifecycle_stage}</strong></span>
                        <span>Composite Score: <strong class="text-white">${data.composite_viability_score}</strong> (${data.priority_tier})</span>
                    </div>
                </div>
            `;
        } else {
            message = `
                <div class="p-5 bg-amber-950/60 border border-amber-800 text-amber-200 rounded-xl space-y-2">
                    <div class="font-bold text-base flex items-center space-x-2 text-amber-300">
                        <span>✗</span>
                        <span>Pipeline Intercepted at Gate ${data.failed_gate}</span>
                    </div>
                    <div class="text-xs text-amber-100">${data.disqualification_reason}</div>
                    <div class="text-xs text-slate-400 mt-2">File automatically quarantined into Tasks & Exceptions Queue with assigned resolution SLA.</div>
                </div>
            `;
        }
        showModal("QC Audit Verdict", message, [
            `<button onclick="closeModal(); refreshCurrentTab();" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow transition">Acknowledge</button>`
        ]);
    } catch (err) {
        showModal("Audit Execution Error", `<div class="text-rose-400 text-xs">${err.message}</div>`, [
            `<button onclick="closeModal()" class="px-4 py-2 bg-slate-800 text-white rounded text-xs">Close</button>`
        ]);
    }
}

function openTransitionModal(opportunityId) {
    const opp = cachedOpportunities.find(o => o.opportunity_id === opportunityId);
    const stages = [
        "PROPERTY_IDENTIFIED", "OWNERSHIP_RESOLVED", "CONTROL_MAPPED", 
        "AUTHORITY_RESOLVED", "SCORED", "DELIVERED", "CLOSED_WON", "ARCHIVED"
    ];

    const body = `
        <p class="text-slate-300 mb-3 text-sm">Select target destination stage for docket <strong class="text-indigo-300 font-mono">${opp ? opp.case_number : ''}</strong>:</p>
        <select id="stage-select" class="w-full bg-slate-800 border border-slate-700 p-2.5 rounded-lg text-white font-mono text-sm focus:outline-none focus:border-indigo-500">
            ${stages.map(s => `<option value="${s}">${s}</option>`).join('')}
        </select>
        <p class="text-xs text-slate-500 mt-2">Note: Stage progression is governed by forward-only FSM rules. Skipping stages or reaching DELIVERED without QC certification will be rejected.</p>
    `;
    const actions = [
        `<button onclick="closeModal()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold transition">Cancel</button>`,
        `<button onclick="submitTransition('${opportunityId}')" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold shadow transition">Commit State</button>`
    ];
    showModal("Advance Opportunity Lifecycle", body, actions);
}

async function submitTransition(opportunityId) {
    const targetStage = document.getElementById("stage-select").value;
    try {
        const res = await fetch(`${API_BASE}/opportunities/${opportunityId}/transition`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ target_stage: targetStage })
        });
        if (!res.ok) {
            const errData = await res.json();
            alert(`FSM Validation Rejected:\n${errData.detail}`);
            return;
        }
        closeModal();
        refreshCurrentTab();
    } catch (err) {
        alert(`Transition Error: ${err.message}`);
    }
}

// -------------------------------------------------------------
// 3. COUNTY INGESTION WORKSPACE
// -------------------------------------------------------------
async function renderCountyView() {
    document.getElementById("workspace-title").innerText = "Municipal Court Scraper & Intake Monitor";
    const container = document.getElementById("view-container");
    container.innerHTML = `
        <div class="max-w-2xl bg-slate-900/90 border border-slate-800 rounded-2xl p-7 space-y-5 shadow-xl backdrop-blur">
            <div>
                <h3 class="font-bold text-white text-base flex items-center space-x-2">
                    <span>🏛️</span>
                    <span>Trigger Municipal Intake Worker</span>
                </h3>
                <p class="text-xs text-slate-400 mt-1 leading-relaxed">
                    Dispatches headless Playwright browser to query court docket registries, download petition pleadings, generate SHA-256 hashes, and commit cases into the database at stage <code class="text-indigo-300 font-mono">DISCOVERED</code>.
                </p>
            </div>
            
            <div class="space-y-2">
                <label class="text-xs font-semibold text-slate-300 tracking-wide">County Jurisdiction FIPS</label>
                <div class="flex space-x-3">
                    <input id="fips-input" value="53067" class="flex-1 bg-slate-800/80 border border-slate-700 rounded-lg px-3.5 py-2.5 text-white font-mono text-sm focus:outline-none focus:border-indigo-500" />
                    <span class="text-xs text-slate-500 self-center font-mono">Thurston, WA</span>
                </div>
            </div>

            <div class="pt-2">
                <button onclick="triggerScraper()" id="scrape-btn" class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg text-xs tracking-wide shadow-lg shadow-indigo-600/30 transition flex items-center space-x-2">
                    <span>🚀</span>
                    <span>Launch Headless Scraper</span>
                </button>
            </div>

            <div id="scrape-console" class="hidden p-4 bg-black/90 border border-slate-800 font-mono text-xs text-emerald-400 rounded-xl leading-relaxed whitespace-pre-wrap"></div>
        </div>
    `;
}

async function triggerScraper() {
    const fips = document.getElementById("fips-input").value;
    const btn = document.getElementById("scrape-btn");
    const term = document.getElementById("scrape-console");
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin mr-1">⏳</span> Running Playwright Worker...`;
    term.classList.remove("hidden");
    term.innerText = `[${new Date().toISOString()}] Initializing headless Chromium worker for FIPS: ${fips}...\n[${new Date().toISOString()}] Interrogating county probate registry...`;

    try {
        const res = await fetch(`${API_BASE}/cases/ingest`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ county_fips: fips })
        });
        const data = await res.json();
        term.innerText += `\n[${new Date().toISOString()}] Extraction complete. Ingested ${data.cases_ingested_count} new cases at stage DISCOVERED.`;
        btn.disabled = false;
        btn.innerHTML = `<span>🚀</span><span>Run Scraper Again</span>`;
    } catch (err) {
        term.innerText += `\n[ERROR] Worker failed: ${err.message}`;
        btn.disabled = false;
        btn.innerHTML = `<span>🚀</span><span>Run Scraper Again</span>`;
    }
}

// -------------------------------------------------------------
// 4. TASKS & EXCEPTIONS VIEW
// -------------------------------------------------------------
async function renderExceptionsView() {
    document.getElementById("workspace-title").innerText = "Tasks & Exceptions Triage Queue";
    const container = document.getElementById("view-container");

    try {
        const res = await fetch(`${API_BASE}/exceptions`);
        const list = await res.json();

        if (list.length === 0) {
            container.innerHTML = `
                <div class="p-16 text-center text-slate-500 border border-slate-800 rounded-2xl bg-slate-900/30">
                    <div class="text-3xl mb-2">🛡️</div>
                    <div class="font-semibold text-slate-300">Zero Open Pipeline Exceptions</div>
                    <div class="text-xs text-slate-500 mt-1">All processed records satisfy quality gate constraints with zero defects active.</div>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="overflow-x-auto bg-slate-900/90 border border-slate-800 rounded-2xl shadow-xl backdrop-blur">
                <table class="w-full text-left text-sm text-slate-300">
                    <thead class="bg-slate-800/80 text-xs uppercase text-slate-400 border-b border-slate-800">
                        <tr>
                            <th class="px-6 py-4">Case #</th>
                            <th class="px-6 py-4">Failed Gate</th>
                            <th class="px-6 py-4">Exception Type</th>
                            <th class="px-6 py-4">SLA Priority</th>
                            <th class="px-6 py-4">Resolution Notes</th>
                            <th class="px-6 py-4 text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800/60">
                        ${list.map(e => `
                            <tr class="hover:bg-slate-800/40 transition">
                                <td class="px-6 py-4 font-bold text-white font-mono">${e.case_number}</td>
                                <td class="px-6 py-4 text-amber-400 font-bold font-mono">Gate ${e.failed_gate}</td>
                                <td class="px-6 py-4 text-slate-200">${e.exception_type}</td>
                                <td class="px-6 py-4">
                                    <span class="px-2.5 py-1 text-xs font-bold rounded-md ${e.priority === 'CRITICAL' ? 'bg-red-600/90 shadow-sm shadow-red-600/50' : 'bg-blue-600/90'} text-white font-mono">
                                        ${e.priority}
                                    </span>
                                </td>
                                <td class="px-6 py-4 text-xs text-slate-400 max-w-xs truncate">${e.resolution_notes}</td>
                                <td class="px-6 py-4 text-right">
                                    <button onclick="resolveExceptionTicket('${e.exception_id}')" class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-semibold shadow transition">
                                        Resolve
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<div class="p-4 bg-red-950 border border-red-800 text-red-300 rounded-xl">Failed to load exceptions: ${err.message}</div>`;
    }
}

async function resolveExceptionTicket(id) {
    const note = prompt("Enter resolution corrective action notes:");
    if (!note) return;
    try {
        await fetch(`${API_BASE}/exceptions/${id}/resolve?resolution_text=${encodeURIComponent(note)}`, { method: "POST" });
        refreshCurrentTab();
    } catch (err) {
        alert(`Resolution failed: ${err.message}`);
    }
}

// -------------------------------------------------------------
// 5. PROPERTY INVESTIGATOR VIEW
// -------------------------------------------------------------
function renderInvestigatorView() {
    document.getElementById("workspace-title").innerText = "Property Investigator & Decision Dossier";
    const container = document.getElementById("view-container");
    container.innerHTML = `
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="lg:col-span-2 space-y-6">
                <div class="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl space-y-4 shadow-xl backdrop-blur">
                    <h3 class="font-bold text-white text-base flex items-center space-x-2">
                        <span>💵</span>
                        <span>Verified Net Actionable Equity Waterfall</span>
                    </h3>
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div class="p-4 bg-slate-800/60 border border-slate-700/50 rounded-xl">
                            <span class="text-slate-400 text-xs uppercase tracking-wide font-semibold">AVM Gross Market Value</span>
                            <div class="text-xl font-bold text-white mt-1">$450,000.00</div>
                        </div>
                        <div class="p-4 bg-slate-800/60 border border-slate-700/50 rounded-xl">
                            <span class="text-slate-400 text-xs uppercase tracking-wide font-semibold">Total Encumbrances Audited</span>
                            <div class="text-xl font-bold text-rose-400 mt-1">-$126,000.00</div>
                        </div>
                    </div>
                    <div class="p-5 bg-emerald-950/40 border border-emerald-800/60 rounded-xl flex justify-between items-center">
                        <div>
                            <span class="text-xs text-emerald-400 font-bold uppercase tracking-wider">Net Actionable Equity</span>
                            <div class="text-2xl font-black text-emerald-300 mt-0.5">$324,000.00</div>
                        </div>
                        <span class="px-3.5 py-1.5 bg-emerald-600 text-white font-black text-xs rounded-lg shadow-sm">72.0% (EXCEPTIONAL)</span>
                    </div>
                </div>

                <div class="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl space-y-3 shadow-xl backdrop-blur">
                    <h3 class="font-bold text-white text-base flex items-center space-x-2">
                        <span>📜</span>
                        <span>Fiduciary Authority & Signatory Path</span>
                    </h3>
                    <p class="text-xs text-slate-300 leading-relaxed">
                        Authority Tier: <strong class="text-emerald-400 font-semibold">TIER 1 (CONFIRMED)</strong> | Letters of Administration Issued with Independent Administration Powers. Direct deed conveyance authorized without prior court confirmation hearing.
                    </p>
                </div>
            </div>

            <div class="space-y-6">
                <div class="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl space-y-3 shadow-xl backdrop-blur">
                    <h3 class="font-bold text-white text-base flex items-center space-x-2">
                        <span>👥</span>
                        <span>Decision Dynamics (CIE)</span>
                    </h3>
                    <p class="text-xs text-slate-400">Archetype: <strong class="text-indigo-400 font-semibold">Unified Fiduciary</strong></p>
                    <div class="text-xs text-slate-300 leading-relaxed">De-facto decision-maker is the sole adult child residing at the property. High transaction velocity profile.</div>
                </div>

                <div class="bg-slate-900/90 border border-slate-800 p-6 rounded-2xl space-y-3 shadow-xl backdrop-blur">
                    <h3 class="font-bold text-white text-base flex items-center space-x-2">
                        <span>🛡️</span>
                        <span>Quality Assurance Gates</span>
                    </h3>
                    <div class="space-y-2 text-xs">
                        <div class="flex justify-between items-center text-slate-300">
                            <span>Gate 1: Docket Integrity</span>
                            <span class="text-emerald-400 font-semibold">PASSED ✓</span>
                        </div>
                        <div class="flex justify-between items-center text-slate-300">
                            <span>Gate 2: Title & PAS</span>
                            <span class="text-emerald-400 font-semibold">PASSED ✓</span>
                        </div>
                        <div class="flex justify-between items-center text-slate-300">
                            <span>Gate 3: Equity Audit</span>
                            <span class="text-emerald-400 font-semibold">PASSED ✓</span>
                        </div>
                        <div class="flex justify-between items-center text-slate-300">
                            <span>Gate 4: Authority</span>
                            <span class="text-emerald-400 font-semibold">PASSED ✓</span>
                        </div>
                        <div class="flex justify-between items-center text-slate-300">
                            <span>Gate 5: DNC / Contact</span>
                            <span class="text-emerald-400 font-semibold">PASSED ✓</span>
                        </div>
                        <div class="flex justify-between items-center text-slate-300">
                            <span>Gate 6: Pre-Delivery</span>
                            <span class="text-emerald-400 font-semibold">PASSED ✓</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// -------------------------------------------------------------
// 6. MODAL SYSTEM
// -------------------------------------------------------------
function showModal(title, bodyHtml, actionButtons) {
    document.getElementById("modal-title").innerText = title;
    document.getElementById("modal-body").innerHTML = bodyHtml;
    document.getElementById("modal-actions").innerHTML = actionButtons.join('');
    const m = document.getElementById("modal-container");
    m.classList.remove("hidden");
    m.classList.add("flex");
}

function closeModal() {
    const m = document.getElementById("modal-container");
    m.classList.add("hidden");
    m.classList.remove("flex");
}
