/* =========================================================
   BAMI COMPREHENSIVE ADMET PROFILING CONTROLLER
   Pure Vanilla JavaScript for Absorption, Distribution, Metabolism,
   Excretion, and Toxicity prediction dashboard.
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    const API_HOST = window.location.hostname || "127.0.0.1";
    const API_BASE_URL = ["localhost", "127.0.0.1"].includes(API_HOST)
        ? (window.location.port === "8000" ? "/api/v1" : `http://${API_HOST}:8000/api/v1`)
        : (window.location.origin && window.location.origin !== "null" && !window.location.origin.startsWith("file:")
            ? `${window.location.origin}/api/v1`
            : "http://127.0.0.1:8000/api/v1");
    const ADMET_PREDICT_URL = `${API_BASE_URL}/admet-predict`;
    const PUBCHEM_NAME_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name";

    // Form and input elements
    const admetForm = document.getElementById('admet-form');
    const smilesInput = document.getElementById('admet-smiles-input');
    const lookupNameBtn = document.getElementById('admet-lookup-name-btn');
    const submitBtn = document.getElementById('admet-submit-btn');
    const clearBtn = document.getElementById('admet-clear-btn');
    const statusMsg = document.getElementById('admet-status');
    const errorMsg = document.getElementById('admet-error');
    const resultsContainer = document.getElementById('admet-results-container');
    const bioactivityCheckbox = document.getElementById('include-bioactivity-checkbox');

    // Sample buttons
    const sampleButtons = document.querySelectorAll('.sample-pill-btn');

    let currentCompoundName = "";
    let lastAdmetData = null;

    // Auth header lookup helper
    async function getAuthHeaders() {
        if (typeof window.getFirebaseAuthHeaders === 'function') {
            try {
                return await window.getFirebaseAuthHeaders();
            } catch (e) {}
        }
        for (let i = 0; i < 15; i++) {
            await new Promise((resolve) => setTimeout(resolve, 60));
            if (typeof window.getFirebaseAuthHeaders === 'function') {
                try {
                    return await window.getFirebaseAuthHeaders();
                } catch (e) {}
            }
        }
        return {};
    }

    // =========================================================
    // SAMPLE PILLS HANDLER
    // =========================================================
    sampleButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const smiles = this.dataset.smiles;
            const name = this.dataset.name;
            if (smiles) {
                smilesInput.value = smiles;
                currentCompoundName = name || "";
                clearError();
                setStatus(`Loaded benchmark sample: ${name}. Click Run Comprehensive ADMET to profile.`);
                smilesInput.focus();
            }
        });
    });

    // =========================================================
    // PUBCHEM NAME RESOLUTION
    // =========================================================
    lookupNameBtn.addEventListener('click', async function () {
        const query = smilesInput.value.trim();
        if (!query) {
            showError("Please enter a drug name or chemical term to look up.");
            return;
        }

        clearError();
        setStatus(`Querying PubChem for "${query}"...`);
        lookupNameBtn.disabled = true;

        try {
            const url = `${PUBCHEM_NAME_URL}/${encodeURIComponent(query)}/property/IsomericSMILES,CanonicalSMILES,Title/JSON`;
            const resp = await fetch(url);
            if (!resp.ok) {
                throw new Error(`PubChem could not find compound "${query}". Please verify spelling or provide a SMILES string directly.`);
            }

            const data = await resp.json();
            const props = data?.PropertyTable?.Properties?.[0];
            const resolvedSmiles = props?.IsomericSMILES || props?.CanonicalSMILES;

            if (!resolvedSmiles) {
                throw new Error(`PubChem returned no SMILES structure for "${query}".`);
            }

            smilesInput.value = resolvedSmiles;
            currentCompoundName = props.Title || query;
            setStatus(`Resolved "${query}" to SMILES successfully: ${resolvedSmiles}`);
        } catch (err) {
            showError(err.message || "Failed to resolve drug name via PubChem.");
        } finally {
            lookupNameBtn.disabled = false;
        }
    });

    // =========================================================
    // CLEAR HANDLER
    // =========================================================
    clearBtn.addEventListener('click', function () {
        smilesInput.value = '';
        currentCompoundName = '';
        clearError();
        clearStatus();
        resultsContainer.hidden = true;
        smilesInput.focus();
    });

    // =========================================================
    // FORM SUBMISSION & PREDICTION
    // =========================================================
    admetForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const smiles = smilesInput.value.trim();

        if (!smiles) {
            showError("Please enter a valid SMILES string or drug name.");
            smilesInput.focus();
            return;
        }

        // Set Loading State
        setLoading(true);
        clearError();
        setStatus("Computing 2058-D molecular features and executing 10 ADMET models...");

        try {
            const authHeaders = await getAuthHeaders();
            const payload = {
                smiles: smiles,
                name: currentCompoundName || null,
                include_bioactivity: bioactivityCheckbox.checked
            };

            const response = await fetch(ADMET_PREDICT_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...authHeaders
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json().catch(() => null);

            if (!response.ok || !data) {
                const detail = data?.detail || data?.message || (response.status === 404 || response.status === 501
                    ? "Cannot connect to ADMET API on port 8000. Please ensure the FastAPI backend is running."
                    : "ADMET prediction failed. Please verify the molecular SMILES.");
                throw new Error(detail);
            }

            if (data.status !== 'success') {
                throw new Error(data.message || "Prediction returned an unsuccessful status.");
            }

            // Render complete results
            renderAdmetDashboard(data);
            clearStatus();
            resultsContainer.hidden = false;
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (err) {
            showError(err.message || "An unexpected error occurred during ADMET screening.");
            resultsContainer.hidden = true;
        } finally {
            setLoading(false);
        }
    });

    // =========================================================
    // DASHBOARD RENDERING ENGINE
    // =========================================================
    function renderAdmetDashboard(data) {
        lastAdmetData = data;
        const sc = data.scorecard || {};
        const admet = data.admet_results || {};
        const desc = data.descriptors || {};
        const bio = data.target_bioactivity || {};

        // 1. Executive Scorecard
        renderScorecard(sc);

        // 2. Molecule Overview & Descriptors
        renderMoleculeOverview(data.canonical_smiles, data.compound_name, data.svg_depiction, desc);

        // 3. Bioactivity Screening
        renderBioactivity(bio);

        // 4. Five ADMET Categories
        renderAbsorption(admet);
        renderDistribution(admet);
        renderMetabolism(admet);
        renderExcretion(admet);
        renderToxicity(admet);
    }

    // 1. SCORECARD
    function renderScorecard(sc) {
        const verdictBox = document.getElementById('scorecard-verdict-box');
        const verdictBadge = document.getElementById('scorecard-verdict-badge');
        const verdictSub = document.getElementById('scorecard-verdict-sub');
        const summaryText = document.getElementById('scorecard-summary-text');

        const favourableEl = document.getElementById('count-favourable');
        const moderateEl = document.getElementById('count-moderate');
        const riskEl = document.getElementById('count-risk');

        const alertsContainer = document.getElementById('critical-alerts-container');
        const alertsList = document.getElementById('critical-alerts-list');
        const recsContainer = document.getElementById('recommendations-container');
        const recsList = document.getElementById('recommendations-list');

        verdictBadge.textContent = sc.badge || 'Evaluated';
        verdictSub.textContent = sc.status || '';
        summaryText.textContent = sc.summary || '';

        // Color theme
        verdictBox.className = `scorecard-verdict-box theme-${sc.color || 'amber'}`;

        favourableEl.textContent = sc.favourable_count || 0;
        moderateEl.textContent = sc.moderate_count || 0;
        riskEl.textContent = sc.risk_count || 0;

        // Alerts
        alertsList.innerHTML = '';
        if (sc.critical_alerts && sc.critical_alerts.length > 0) {
            alertsContainer.hidden = false;
            sc.critical_alerts.forEach(alertText => {
                const li = document.createElement('li');
                li.className = 'alert-item';
                li.innerHTML = `<span class="bullet-alert">⚠️</span> <span>${escapeHtml(alertText)}</span>`;
                alertsList.appendChild(li);
            });
        } else {
            alertsContainer.hidden = false;
            const li = document.createElement('li');
            li.className = 'alert-item alert-clean';
            li.innerHTML = `<span class="bullet-clean">✓</span> <span>No high-risk toxicological or severe pharmacokinetic liabilities flagged.</span>`;
            alertsList.appendChild(li);
        }

        // Recommendations
        recsList.innerHTML = '';
        if (sc.actionable_recommendations && sc.actionable_recommendations.length > 0) {
            recsContainer.hidden = false;
            sc.actionable_recommendations.forEach(recText => {
                const li = document.createElement('li');
                li.className = 'rec-item';
                li.innerHTML = `<span class="bullet-rec">✦</span> <span>${escapeHtml(recText)}</span>`;
                recsList.appendChild(li);
            });
        }
    }

    // 2. MOLECULE OVERVIEW
    function renderMoleculeOverview(canonicalSmiles, name, svg, desc) {
        const svgContainer = document.getElementById('admet-svg-container');
        const smilesCode = document.getElementById('admet-canonical-smiles');
        const nameEl = document.getElementById('admet-compound-name');
        const copyBtn = document.getElementById('btn-copy-admet-smiles');
        const badgesContainer = document.getElementById('compliance-badges-container');

        svgContainer.innerHTML = svg || '<div class="no-svg-placeholder">2D Structure Unavailable</div>';
        smilesCode.textContent = canonicalSmiles || '';
        nameEl.textContent = name || 'Investigational Molecule';

        copyBtn.onclick = function () {
            if (canonicalSmiles) {
                navigator.clipboard.writeText(canonicalSmiles).then(() => {
                    const original = copyBtn.textContent;
                    copyBtn.textContent = '✓ Copied!';
                    setTimeout(() => { copyBtn.textContent = original; }, 1800);
                });
            }
        };

        // Compliance Badges
        badgesContainer.innerHTML = '';
        const lipinskiPass = desc.lipinski_compliant;
        const lipBadge = document.createElement('span');
        lipBadge.className = `rule-badge ${lipinskiPass ? 'badge-pass' : 'badge-fail'}`;
        lipBadge.textContent = lipinskiPass 
            ? 'Lipinski Ro5: Compliant' 
            : `Lipinski: ${desc.lipinski_violations_count} Violation(s)`;
        badgesContainer.appendChild(lipBadge);

        const veberPass = desc.veber_compliant;
        const veberBadge = document.createElement('span');
        veberBadge.className = `rule-badge ${veberPass ? 'badge-pass' : 'badge-fail'}`;
        veberBadge.textContent = veberPass 
            ? 'Veber Rules: Compliant' 
            : `Veber: ${desc.veber_violations_count} Violation(s)`;
        badgesContainer.appendChild(veberBadge);

        // Descriptors
        document.getElementById('desc-formula').textContent = desc.formula || '--';
        document.getElementById('desc-mw').innerHTML = `${desc.molecular_weight || '--'} <span class="unit">g/mol</span>`;
        document.getElementById('desc-logp').textContent = desc.logp !== undefined ? desc.logp : '--';
        document.getElementById('desc-tpsa').innerHTML = `${desc.tpsa || '--'} <span class="unit">Å²</span>`;
        document.getElementById('desc-hbd').textContent = desc.hbd !== undefined ? desc.hbd : '--';
        document.getElementById('desc-hba').textContent = desc.hba !== undefined ? desc.hba : '--';
        document.getElementById('desc-rotb').textContent = desc.rotatable_bonds !== undefined ? desc.rotatable_bonds : '--';
        document.getElementById('desc-arom-rings').textContent = desc.aromatic_rings !== undefined ? desc.aromatic_rings : '--';
        document.getElementById('desc-fsp3').textContent = desc.fraction_csp3 !== undefined ? desc.fraction_csp3 : '--';
        document.getElementById('desc-qed').textContent = desc.qed !== undefined ? desc.qed : '--';
    }

    // 3. TARGET BIOACTIVITY
    function renderBioactivity(bio) {
        const bioSection = document.getElementById('bioactivity-co-screen-section');
        const cox2 = bio.cox2 || {};
        const egfr = bio.egfr || {};

        if (cox2.status === 'not_requested' && egfr.status === 'not_requested') {
            bioSection.hidden = true;
            return;
        }

        bioSection.hidden = false;

        // COX-2
        const cox2Badge = document.getElementById('bio-cox2-badge');
        const cox2Class = document.getElementById('bio-cox2-class');
        const cox2Prob = document.getElementById('bio-cox2-prob');
        const cox2Fill = document.getElementById('bio-cox2-fill');

        if (cox2.status === 'success') {
            const isActive = cox2.prediction === 'Active';
            cox2Badge.textContent = cox2.prediction;
            cox2Badge.className = `target-badge ${isActive ? 'active' : 'inactive'}`;
            cox2Class.textContent = cox2.prediction;
            const probPct = Math.round((cox2.probability_active || 0) * 100);
            cox2Prob.textContent = `${probPct}%`;
            cox2Fill.style.width = `${probPct}%`;
            cox2Fill.className = `bio-progress-fill ${isActive ? 'active' : 'inactive'}`;
        } else {
            cox2Badge.textContent = 'Unavailable';
            cox2Class.textContent = '--';
            cox2Prob.textContent = '--';
            cox2Fill.style.width = '0%';
        }

        // EGFR
        const egfrBadge = document.getElementById('bio-egfr-badge');
        const egfrClass = document.getElementById('bio-egfr-class');
        const egfrProb = document.getElementById('bio-egfr-prob');
        const egfrFill = document.getElementById('bio-egfr-fill');

        if (egfr.status === 'success') {
            const isActive = egfr.prediction === 'Active';
            egfrBadge.textContent = egfr.prediction;
            egfrBadge.className = `target-badge ${isActive ? 'active' : 'inactive'}`;
            egfrClass.textContent = egfr.prediction;
            const probPct = Math.round((egfr.probability_active || 0) * 100);
            egfrProb.textContent = `${probPct}%`;
            egfrFill.style.width = `${probPct}%`;
            egfrFill.className = `bio-progress-fill ${isActive ? 'active' : 'inactive'}`;
        } else {
            egfrBadge.textContent = 'Unavailable';
            egfrClass.textContent = '--';
            egfrProb.textContent = '--';
            egfrFill.style.width = '0%';
        }
    }

    // 4. ABSORPTION
    function renderAbsorption(admet) {
        // Solubility
        const sol = admet.solubility || {};
        const badgeSol = document.getElementById('badge-solubility');
        const valSol = document.getElementById('val-solubility');
        const fillSol = document.getElementById('fill-solubility');
        const interpSol = document.getElementById('interp-solubility');

        badgeSol.textContent = sol.badge || '--';
        badgeSol.className = `ep-badge ${sol.risk_level || 'favourable'}`;
        valSol.textContent = sol.predicted_value !== undefined ? sol.predicted_value.toFixed(2) : '--';
        interpSol.textContent = sol.clinical_interpretation || '';

        // Map logS from range [-10, 0] to 0-100%
        const solPct = Math.max(5, Math.min(95, ((sol.predicted_value || -5) + 10) * 10));
        fillSol.style.width = `${solPct}%`;
        fillSol.className = `meter-bar-fill fill-${sol.risk_level || 'favourable'}`;

        // Caco-2
        const caco = admet.caco2 || {};
        const badgeCaco = document.getElementById('badge-caco2');
        const valCaco = document.getElementById('val-caco2');
        const fillCaco = document.getElementById('fill-caco2');
        const interpCaco = document.getElementById('interp-caco2');

        badgeCaco.textContent = caco.badge || '--';
        badgeCaco.className = `ep-badge ${caco.risk_level || 'favourable'}`;
        valCaco.textContent = caco.predicted_value !== undefined ? caco.predicted_value.toFixed(2) : '--';
        interpCaco.textContent = caco.clinical_interpretation || '';

        // Map log Papp from range [-7, -4] to 0-100%
        const cacoPct = Math.max(5, Math.min(95, (((caco.predicted_value || -5.5) + 7) / 3) * 100));
        fillCaco.style.width = `${cacoPct}%`;
        fillCaco.className = `meter-bar-fill fill-${caco.risk_level || 'favourable'}`;

        // HIA
        const hia = admet.hia || {};
        const badgeHia = document.getElementById('badge-hia');
        const valHia = document.getElementById('val-hia');
        const probHia = document.getElementById('prob-hia');
        const fillHia = document.getElementById('fill-hia');
        const interpHia = document.getElementById('interp-hia');

        badgeHia.textContent = hia.badge || '--';
        badgeHia.className = `ep-badge ${hia.risk_level || 'favourable'}`;
        valHia.textContent = hia.tier || '--';
        const hiaConf = Math.round(((hia.probability_positive || 0.5) >= 0.5 ? hia.probability_positive : hia.probability_negative) * 100);
        probHia.textContent = `Confidence ${hiaConf}%`;
        fillHia.style.width = `${hiaConf}%`;
        fillHia.className = `meter-bar-fill fill-${hia.risk_level || 'favourable'}`;
        interpHia.textContent = hia.clinical_interpretation || '';
    }

    // 5. DISTRIBUTION
    function renderDistribution(admet) {
        // BBBP
        const bbbp = admet.bbbp || {};
        const badgeBbbp = document.getElementById('badge-bbbp');
        const valBbbp = document.getElementById('val-bbbp');
        const probBbbp = document.getElementById('prob-bbbp');
        const fillBbbp = document.getElementById('fill-bbbp');
        const interpBbbp = document.getElementById('interp-bbbp');

        badgeBbbp.textContent = bbbp.badge || '--';
        badgeBbbp.className = `ep-badge ${bbbp.risk_level === 'info' ? 'info' : 'favourable'}`;
        valBbbp.textContent = bbbp.tier || '--';
        const bbbpConf = Math.round(((bbbp.probability_positive || 0.5) >= 0.5 ? bbbp.probability_positive : bbbp.probability_negative) * 100);
        probBbbp.textContent = `Confidence ${bbbpConf}%`;
        fillBbbp.style.width = `${bbbpConf}%`;
        fillBbbp.className = `meter-bar-fill fill-${bbbp.risk_level === 'info' ? 'info' : 'favourable'}`;
        interpBbbp.textContent = bbbp.clinical_interpretation || '';

        // PPB
        const ppb = admet.ppb || {};
        const badgePpb = document.getElementById('badge-ppb');
        const valPpb = document.getElementById('val-ppb');
        const valFu = document.getElementById('val-fu');
        const fillPpb = document.getElementById('fill-ppb');
        const interpPpb = document.getElementById('interp-ppb');

        badgePpb.textContent = ppb.badge || '--';
        badgePpb.className = `ep-badge ${ppb.risk_level || 'favourable'}`;
        valPpb.textContent = `${ppb.predicted_value || '--'}%`;
        valFu.textContent = `Fraction Unbound fu: ${ppb.fraction_unbound_pct || '--'}%`;
        fillPpb.style.width = `${Math.min(100, Math.max(5, ppb.predicted_value || 50))}%`;
        fillPpb.className = `meter-bar-fill fill-${ppb.risk_level || 'favourable'}`;
        interpPpb.textContent = ppb.clinical_interpretation || '';
    }

    // 6. METABOLISM
    function renderMetabolism(admet) {
        const cypList = [
            { key: 'cyp3a4', bId: 'badge-cyp3a4', vId: 'val-cyp3a4', pId: 'prob-cyp3a4', fId: 'fill-cyp3a4', iId: 'interp-cyp3a4' },
            { key: 'cyp2d6', bId: 'badge-cyp2d6', vId: 'val-cyp2d6', pId: 'prob-cyp2d6', fId: 'fill-cyp2d6', iId: 'interp-cyp2d6' },
            { key: 'cyp2c9', bId: 'badge-cyp2c9', vId: 'val-cyp2c9', pId: 'prob-cyp2c9', fId: 'fill-cyp2c9', iId: 'interp-cyp2c9' }
        ];

        cypList.forEach(c => {
            const data = admet[c.key] || {};
            const badge = document.getElementById(c.bId);
            const val = document.getElementById(c.vId);
            const prob = document.getElementById(c.pId);
            const fill = document.getElementById(c.fId);
            const interp = document.getElementById(c.iId);

            badge.textContent = data.badge || '--';
            badge.className = `ep-badge ${data.risk_level || 'favourable'}`;
            val.textContent = data.tier || '--';
            const conf = Math.round(((data.probability_positive || 0.5) >= 0.5 ? data.probability_positive : data.probability_negative) * 100);
            prob.textContent = `Confidence ${conf}%`;
            fill.style.width = `${conf}%`;
            fill.className = `meter-bar-fill fill-${data.risk_level || 'favourable'}`;
            interp.textContent = data.clinical_interpretation || '';
        });
    }

    // 7. EXCRETION
    function renderExcretion(admet) {
        // QED
        const qed = admet.qed || {};
        const badgeQed = document.getElementById('badge-qed');
        const valQed = document.getElementById('val-qed');
        const fillQed = document.getElementById('fill-qed');
        const interpQed = document.getElementById('interp-qed');

        badgeQed.textContent = qed.badge || '--';
        badgeQed.className = `ep-badge ${qed.risk_level || 'favourable'}`;
        valQed.textContent = qed.predicted_value !== undefined ? qed.predicted_value.toFixed(3) : '--';
        fillQed.style.width = `${Math.round((qed.predicted_value || 0.5) * 100)}%`;
        fillQed.className = `meter-bar-fill fill-${qed.risk_level || 'favourable'}`;
        interpQed.textContent = qed.clinical_interpretation || '';

        // Clearance
        const cl = admet.clearance || {};
        const badgeCl = document.getElementById('badge-clearance');
        const valCl = document.getElementById('val-clearance');
        const interpCl = document.getElementById('interp-clearance');

        badgeCl.textContent = cl.badge || 'Route';
        valCl.textContent = cl.tier || '--';
        interpCl.textContent = cl.clinical_interpretation || '';
    }

    // 8. TOXICITY
    function renderToxicity(admet) {
        const toxList = [
            { key: 'ames', bId: 'badge-ames', vId: 'val-ames', pId: 'prob-ames', fId: 'fill-ames', iId: 'interp-ames' },
            { key: 'dili', bId: 'badge-dili', vId: 'val-dili', pId: 'prob-dili', fId: 'fill-dili', iId: 'interp-dili' },
            { key: 'herg', bId: 'badge-herg', vId: 'val-herg', pId: 'prob-herg', fId: 'fill-herg', iId: 'interp-herg' }
        ];

        toxList.forEach(t => {
            const data = admet[t.key] || {};
            const badge = document.getElementById(t.bId);
            const val = document.getElementById(t.vId);
            const prob = document.getElementById(t.pId);
            const fill = document.getElementById(t.fId);
            const interp = document.getElementById(t.iId);

            badge.textContent = data.badge || '--';
            badge.className = `ep-badge ${data.risk_level || 'favourable'}`;
            val.textContent = data.tier || '--';
            const conf = Math.round(((data.probability_positive || 0.5) >= 0.5 ? data.probability_positive : data.probability_negative) * 100);
            prob.textContent = `Confidence ${conf}%`;
            fill.style.width = `${conf}%`;
            fill.className = `meter-bar-fill fill-${data.risk_level || 'favourable'}`;
            interp.textContent = data.clinical_interpretation || '';
        });
    }

    // =========================================================
    // UI HELPERS
    // =========================================================
    function setLoading(isLoading) {
        submitBtn.disabled = isLoading;
        const spinner = submitBtn.querySelector('.spinner');
        const btnText = submitBtn.querySelector('.btn-text');
        if (spinner) spinner.hidden = !isLoading;
        if (btnText) {
            btnText.textContent = isLoading ? 'Profiling 10 Endpoints...' : 'Run Comprehensive ADMET Screening';
        }
    }

    function setStatus(msg) {
        statusMsg.textContent = msg;
        statusMsg.hidden = !msg;
    }

    function clearStatus() {
        statusMsg.textContent = '';
        statusMsg.hidden = true;
    }

    function showError(msg) {
        errorMsg.textContent = msg;
        errorMsg.hidden = !msg;
    }

    function clearError() {
        errorMsg.textContent = '';
        errorMsg.hidden = true;
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // =========================================================
    // SCIENTIFIC PDF REPORT DOWNLOAD
    // =========================================================
    const admetDownloadBtn = document.getElementById('admet-download-pdf-btn');
    if (admetDownloadBtn) {
        admetDownloadBtn.addEventListener('click', async function () {
            const smiles = (lastAdmetData?.canonical_smiles || lastAdmetData?.smiles || (smilesInput ? smilesInput.value.trim() : '')).trim();
            if (!smiles) {
                alert('Please submit a molecule to profile before downloading the report.');
                return;
            }

            const origHtml = admetDownloadBtn.innerHTML;
            admetDownloadBtn.disabled = true;
            admetDownloadBtn.classList.add('loading');
            admetDownloadBtn.innerHTML = '<span class="pdf-spinner" aria-hidden="true"></span> <span class="btn-text">Generating PDF...</span>';

            try {
                let authHeaders = {};
                if (typeof window.getFirebaseAuthHeaders === 'function') {
                    try {
                        authHeaders = await window.getFirebaseAuthHeaders();
                    } catch {
                        authHeaders = {};
                    }
                }

                const response = await fetch(`${API_BASE_URL}/download-report`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...authHeaders
                    },
                    body: JSON.stringify({
                        smiles: smiles,
                        name: currentCompoundName || lastAdmetData?.compound_name || '',
                        include_admet: true
                    })
                });

                if (!response.ok) {
                    const err = await response.json().catch(() => ({}));
                    throw new Error(err.detail || `Server returned HTTP ${response.status}`);
                }

                const blob = await response.blob();
                let filename = `BAMI_ADMET_Report_${(currentCompoundName || 'Molecule').replace(/[^a-zA-Z0-9_-]/g, '_')}.pdf`;
                const disp = response.headers.get('Content-Disposition');
                if (disp && disp.includes('filename=')) {
                    const m = disp.match(/filename="?([^";]+)"?/);
                    if (m && m[1]) filename = m[1].trim();
                }

                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                setTimeout(() => window.URL.revokeObjectURL(url), 2000);
            } catch (err) {
                console.error('ADMET PDF error:', err);
                alert(`Could not download report: ${err.message}`);
            } finally {
                admetDownloadBtn.disabled = false;
                admetDownloadBtn.classList.remove('loading');
                admetDownloadBtn.innerHTML = origHtml;
            }
        });
    }

    // =========================================================
    // URL PRELOAD (e.g., from Predictor page shortcut)
    // =========================================================
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const preSmiles = urlParams.get('smiles');
        const preName = urlParams.get('name');
        if (preSmiles && smilesInput) {
            smilesInput.value = preSmiles;
            currentCompoundName = preName || '';
            // Trigger auto-submit
            setTimeout(() => {
                admetForm.dispatchEvent(new Event('submit', { cancelable: true }));
            }, 100);
        }
    } catch (e) {
        console.warn('URL preload failed:', e);
    }
});
