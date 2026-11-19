/* =========================================================
   BAMI MOLECULAR SCAFFOLD ANALYSIS CONTROLLER
   Handles single-molecule and multi-molecule Bemis-Murcko core
   decomposition, peripheral substituents, Tanimoto similarity,
   and machine learning bioactivity integration.
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    const API_HOST = window.location.hostname || "127.0.0.1";
    const API_BASE_URL = ["localhost", "127.0.0.1"].includes(API_HOST)
        ? (window.location.port === "8000" ? "/api/v1" : `http://${API_HOST}:8000/api/v1`)
        : (window.location.origin && window.location.origin !== "null" && !window.location.origin.startsWith("file:")
            ? `${window.location.origin}/api/v1`
            : "http://127.0.0.1:8000/api/v1");
    const SCAFFOLD_API_URL = `${API_BASE_URL}/scaffold-analysis`;
    const PUBCHEM_NAME_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name";

    // Tab buttons and panels
    const tabBtnSingle = document.getElementById('tab-btn-single');
    const tabBtnMulti = document.getElementById('tab-btn-multi');
    const panelSingle = document.getElementById('scaffold-single-panel');
    const panelMulti = document.getElementById('scaffold-multi-panel');

    // Single form elements
    const singleForm = document.getElementById('scaffold-single-form');
    const singleSmilesInput = document.getElementById('single-smiles-input');
    const singleSubmitBtn = document.getElementById('single-submit-btn');
    const singleStatus = document.getElementById('single-status');
    const singleError = document.getElementById('single-error');
    const singleResults = document.getElementById('single-results-container');

    // Multi form elements
    const multiForm = document.getElementById('scaffold-multi-form');
    const multiSmilesInput = document.getElementById('multi-smiles-input');
    const multiSubmitBtn = document.getElementById('multi-submit-btn');
    const multiStatus = document.getElementById('multi-status');
    const multiError = document.getElementById('multi-error');
    const multiResults = document.getElementById('multi-results-container');

    // Preloaded series buttons
    const loadSeriesEgfr = document.getElementById('load-series-egfr');
    const loadSeriesCox2 = document.getElementById('load-series-cox2');
    const loadSeriesSalicylate = document.getElementById('load-series-salicylate');
    const loadSeriesDiverse = document.getElementById('load-series-diverse');

    // Auth header lookup helper
    async function getAuthHeaders() {
        if (typeof window.getFirebaseAuthHeaders === 'function') {
            try {
                return await window.getFirebaseAuthHeaders();
            } catch (e) {
                // Return empty if not authenticated
            }
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

    // Tab switching
    if (tabBtnSingle && tabBtnMulti) {
        tabBtnSingle.addEventListener('click', function () {
            tabBtnSingle.classList.add('active');
            tabBtnSingle.setAttribute('aria-selected', 'true');
            tabBtnMulti.classList.remove('active');
            tabBtnMulti.setAttribute('aria-selected', 'false');

            panelSingle.hidden = false;
            panelSingle.style.display = 'block';
            panelMulti.hidden = true;
            panelMulti.style.display = 'none';
        });

        tabBtnMulti.addEventListener('click', function () {
            tabBtnMulti.classList.add('active');
            tabBtnMulti.setAttribute('aria-selected', 'true');
            tabBtnSingle.classList.remove('active');
            tabBtnSingle.setAttribute('aria-selected', 'false');

            panelMulti.hidden = false;
            panelMulti.style.display = 'block';
            panelSingle.hidden = true;
            panelSingle.style.display = 'none';
        });
    }

    // Quick sample pills for single molecule
    document.querySelectorAll('.quick-sample-pill[data-smiles]').forEach(function (pill) {
        pill.addEventListener('click', function () {
            const smiles = this.getAttribute('data-smiles');
            const name = this.getAttribute('data-name');
            if (singleSmilesInput) {
                singleSmilesInput.value = smiles;
                singleSmilesInput.dataset.compoundName = name || '';
                runSingleScaffoldAnalysis(smiles, name || '');
            }
        });
    });

    // Curated series definitions
    const SERIES_DATA = {
        egfr: [
            "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1 Gefitinib",
            "C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1 Erlotinib",
            "CS(=O)(=O)CCNCc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)c(Cl)c4)c3c2)o1 Lapatinib"
        ].join("\n"),
        cox2: [
            "CC1=CC=C(C=C1)C2=CC(=NN2C3=CC=C(C=C3)S(=O)(=O)N)C(F)(F)F Celecoxib",
            "Cc1ccc(-c2cc(C(F)(F)F)nn2-c2ccc(S(N)(=O)=O)cc2)cc1F Mavacoxib",
            "Cc1ccc(-c2cc(C(F)(F)F)nn2-c2ccccc2)cc1 Valdecoxib-Analogue"
        ].join("\n"),
        salicylate: [
            "CC(=O)Oc1ccccc1C(=O)O Aspirin",
            "OC(=O)c1ccccc1O Salicylic Acid",
            "Oc1ccc(-c2ccc(F)cc2F)cc1C(=O)O Diflunisal"
        ].join("\n"),
        diverse: [
            "CC(=O)Oc1ccccc1C(=O)O Aspirin",
            "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1 Gefitinib",
            "CC1=CC=C(C=C1)C2=CC(=NN2C3=CC=C(C=C3)S(=O)(=O)N)C(F)(F)F Celecoxib",
            "CCCC(CCC)C(=O)O Valproic Acid"
        ].join("\n")
    };

    if (loadSeriesEgfr) {
        loadSeriesEgfr.addEventListener('click', () => populateAndRunSeries(SERIES_DATA.egfr));
    }
    if (loadSeriesCox2) {
        loadSeriesCox2.addEventListener('click', () => populateAndRunSeries(SERIES_DATA.cox2));
    }
    if (loadSeriesSalicylate) {
        loadSeriesSalicylate.addEventListener('click', () => populateAndRunSeries(SERIES_DATA.salicylate));
    }
    if (loadSeriesDiverse) {
        loadSeriesDiverse.addEventListener('click', () => populateAndRunSeries(SERIES_DATA.diverse));
    }

    function populateAndRunSeries(seriesText) {
        if (multiSmilesInput) {
            multiSmilesInput.value = seriesText;
            runMultiScaffoldAnalysis(seriesText);
        }
    }

    // Single Form Submit
    if (singleForm) {
        singleForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const rawVal = singleSmilesInput.value.trim();
            if (!rawVal) return;
            const preName = singleSmilesInput.dataset.compoundName || '';
            runSingleScaffoldAnalysis(rawVal, preName);
        });
    }

    // Resolve drug names through PubChem
    async function resolveSingleInput(input) {
        const trimmed = input.trim();
        // If looks like SMILES (contains = # ( ) @ or standard letters with no spaces and length > 3)
        // Check if PubChem lookup is needed
        if (/[\(\)=\#@\+\-\[\]]/.test(trimmed) || /^[A-Z][a-z]?\d*/.test(trimmed) && trimmed.length > 25) {
            return { smiles: trimmed, name: trimmed };
        }

        // Attempt PubChem lookup
        try {
            const url = `${PUBCHEM_NAME_URL}/${encodeURIComponent(trimmed)}/property/CanonicalSMILES,IsomericSMILES/JSON`;
            const resp = await fetch(url);
            if (resp.ok) {
                const data = await resp.json();
                const props = data?.PropertyTable?.Properties?.[0];
                const resolvedSmiles = props?.IsomericSMILES || props?.CanonicalSMILES;
                if (resolvedSmiles) {
                    return { smiles: resolvedSmiles, name: trimmed };
                }
            }
        } catch (err) {
            console.warn('PubChem lookup failed, treating as literal SMILES:', err);
        }

        return { smiles: trimmed, name: trimmed };
    }

    // Run Single Scaffold Analysis
    async function runSingleScaffoldAnalysis(rawInput, defaultName = '') {
        hideError(singleError);
        singleStatus.textContent = 'Resolving molecule structure and extracting Bemis-Murcko scaffold...';
        singleSubmitBtn.disabled = true;

        try {
            const resolved = await resolveSingleInput(rawInput);
            const compoundName = defaultName || resolved.name || 'Molecule Lead';
            const smilesToSubmit = resolved.smiles;

            const authHeaders = await getAuthHeaders();
            const response = await fetch(SCAFFOLD_API_URL, {
                method: 'POST',
                headers: {
                    ...authHeaders,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    smiles: smilesToSubmit,
                    name: compoundName
                })
            });

            const data = await response.json().catch(() => null);

            if (!response.ok || !data) {
                const msg = data?.detail || data?.error || (response.status === 404 || response.status === 501
                    ? 'Cannot connect to Scaffold Analysis API on port 8000. Please ensure the FastAPI backend is running.'
                    : 'Failed to analyze molecular scaffold. Please verify the SMILES string.');
                throw new Error(msg);
            }

            singleStatus.textContent = 'Scaffold extraction completed successfully.';
            renderSingleResults(data);
        } catch (err) {
            showError(singleError, err.message || 'Scaffold extraction failed.');
            singleStatus.textContent = '';
            singleResults.hidden = true;
            singleResults.style.display = 'none';
        } finally {
            singleSubmitBtn.disabled = false;
        }
    }

    // Render Single Results
    function renderSingleResults(data) {
        singleResults.hidden = false;
        singleResults.style.display = 'block';

        // Title & Badges
        const titleEl = document.getElementById('res-compound-title');
        const scaffoldBadge = document.getElementById('res-scaffold-type-badge');
        const ringBadge = document.getElementById('res-ring-counts-badge');

        if (titleEl) titleEl.textContent = data.name || 'Molecule Lead';

        const scaff = data.scaffold || {};
        if (scaffoldBadge) {
            if (scaff.has_scaffold) {
                scaffoldBadge.textContent = 'Bemis-Murcko Ring Scaffold';
                scaffoldBadge.className = 'scaffold-badge badge-ring';
            } else {
                scaffoldBadge.textContent = 'Acyclic (No Ring Scaffold)';
                scaffoldBadge.className = 'scaffold-badge badge-acyclic';
            }
        }

        if (ringBadge) {
            ringBadge.textContent = `${scaff.total_ring_count || 0} Total Ring${scaff.total_ring_count === 1 ? '' : 's'}`;
        }

        // Open in Predictor Button
        const openPredBtn = document.getElementById('open-in-predictor-btn');
        if (openPredBtn) {
            openPredBtn.onclick = function () {
                window.location.href = `index.html?smiles=${encodeURIComponent(data.canonical_smiles || data.input_smiles)}&name=${encodeURIComponent(data.name || '')}`;
            };
        }

        // 3 Visual Displays
        const visOrigSvg = document.getElementById('vis-original-svg');
        const visScaffSvg = document.getElementById('vis-scaffold-svg');
        const visHighSvg = document.getElementById('vis-highlighted-svg');
        const visOrigSmiles = document.getElementById('vis-original-smiles');
        const visScaffSmiles = document.getElementById('vis-scaffold-smiles');

        if (visOrigSvg) visOrigSvg.innerHTML = data.visualizations?.original_svg || '<p class="empty-vis">No structure SVG available</p>';
        if (visScaffSvg) {
            if (scaff.has_scaffold && data.visualizations?.scaffold_svg) {
                visScaffSvg.innerHTML = data.visualizations.scaffold_svg;
            } else {
                visScaffSvg.innerHTML = `
                    <div class="acyclic-scaffold-placeholder">
                        <span class="placeholder-icon">⛓️</span>
                        <p><strong>Acyclic Molecule</strong><br>No cyclic Bemis-Murcko core exists for this structure.</p>
                    </div>
                `;
            }
        }
        if (visHighSvg) visHighSvg.innerHTML = data.visualizations?.highlighted_svg || '<p class="empty-vis">No highlight SVG available</p>';

        if (visOrigSmiles) {
            visOrigSmiles.textContent = data.canonical_smiles || data.input_smiles || '--';
            visOrigSmiles.title = visOrigSmiles.textContent;
        }
        if (visScaffSmiles) {
            visScaffSmiles.textContent = scaff.has_scaffold ? (scaff.scaffold_smiles || '--') : 'Acyclic (None)';
            visScaffSmiles.title = visScaffSmiles.textContent;
        }

        // Copy scaffold button
        const copyBtn = document.getElementById('copy-scaffold-btn');
        if (copyBtn) {
            copyBtn.onclick = function () {
                const text = scaff.scaffold_smiles || '';
                if (text) copyToClipboard(text, copyBtn);
            };
        }

        // Metrics
        setText('stat-scaff-atoms', `${scaff.scaffold_heavy_atoms || 0} / ${scaff.total_heavy_atoms || 0}`);
        setText('stat-scaff-fraction', `${Math.round((scaff.scaffold_atom_fraction || 0) * 100)}%`);
        setText('stat-scaff-rings', `${scaff.scaffold_ring_count || 0}`);
        setText('stat-substituent-count', `${data.substituent_count || 0}`);

        // Generic Framework
        const genericCode = document.getElementById('generic-framework-code');
        if (genericCode) {
            genericCode.textContent = scaff.generic_framework_smiles || (scaff.has_scaffold ? 'Normalized core' : 'None (Acyclic)');
        }

        // Substituents Grid
        renderSubstituents(data.substituents || []);

        // Machine Learning Bioactivity
        renderBioactivityCards(data.bioactivity_predictions);

        // Molecular Descriptors
        const desc = data.molecular_descriptors || {};
        setText('desc-mw', formatNum(desc.molecular_weight));
        setText('desc-logp', formatNum(desc.logp));
        setText('desc-tpsa', formatNum(desc.tpsa));
        setText('desc-hbd', desc.h_bond_donors ?? '--');
        setText('desc-hba', desc.h_bond_acceptors ?? '--');
        setText('desc-rotb', desc.rotatable_bonds ?? '--');

        // Scroll into view smoothly
        singleResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Render Substituents Grid
    function renderSubstituents(subList) {
        const grid = document.getElementById('substituents-grid');
        if (!grid) return;

        if (!subList || subList.length === 0) {
            grid.innerHTML = `
                <div class="no-substituents-card">
                    <span class="info-icon">✨</span>
                    <div>
                        <h4>No Peripheral Substituents</h4>
                        <p>This molecule consists entirely of its core scaffold, or is an acyclic structure with no peripheral attachment points.</p>
                    </div>
                </div>
            `;
            return;
        }

        grid.innerHTML = '';
        subList.forEach(function (sub) {
            const card = document.createElement('div');
            card.className = 'substituent-card';
            card.innerHTML = `
                <div class="substituent-top">
                    <span class="r-badge">${escapeHtml(sub.id || 'R')}</span>
                    <span class="sub-atoms">${sub.heavy_atoms || 0} heavy atom${sub.heavy_atoms === 1 ? '' : 's'}</span>
                </div>
                <div class="sub-svg-box">
                    ${sub.svg || '<p>No preview</p>'}
                </div>
                <div class="sub-code-box">
                    <code>${escapeHtml(sub.smiles || '--')}</code>
                </div>
            `;
            grid.appendChild(card);
        });
    }

    // Render Bioactivity Cards (COX-2 & EGFR)
    function renderBioactivityCards(preds) {
        if (!preds) return;

        // COX-2
        const cox2 = preds.cox2 || {};
        const cox2Badge = document.getElementById('cox2-outcome-badge');
        const cox2Score = document.getElementById('cox2-score-val');
        if (cox2Badge) {
            const isActive = cox2.prediction === 'Active';
            cox2Badge.textContent = cox2.prediction || 'Unknown';
            cox2Badge.className = `outcome-badge ${isActive ? 'outcome-active' : 'outcome-inactive'}`;
        }
        if (cox2Score) {
            cox2Score.textContent = Number.isFinite(cox2.probability_active)
                ? `${(cox2.probability_active * 100).toFixed(1)}%`
                : '--';
        }

        // EGFR
        const egfr = preds.egfr || {};
        const egfrBadge = document.getElementById('egfr-outcome-badge');
        const egfrScore = document.getElementById('egfr-score-val');
        if (egfrBadge) {
            const isActive = egfr.prediction === 'Active';
            egfrBadge.textContent = egfr.prediction || 'Unknown';
            egfrBadge.className = `outcome-badge ${isActive ? 'outcome-active' : 'outcome-inactive'}`;
        }
        if (egfrScore) {
            egfrScore.textContent = Number.isFinite(egfr.probability_active)
                ? `${(egfr.probability_active * 100).toFixed(1)}%`
                : '--';
        }
    }

    // Multi-Molecule Form Submit
    if (multiForm) {
        multiForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const text = multiSmilesInput.value.trim();
            if (!text) return;
            runMultiScaffoldAnalysis(text);
        });
    }

    // Run Multi-Molecule Scaffold Analysis
    async function runMultiScaffoldAnalysis(rawText) {
        hideError(multiError);
        multiStatus.textContent = 'Parsing molecule list, extracting scaffolds, and calculating similarity...';
        multiSubmitBtn.disabled = true;

        try {
            const lines = rawText.split('\n').map((l) => l.trim()).filter(Boolean);
            if (lines.length === 0) {
                throw new Error('Please enter at least one molecule.');
            }

            const moleculePayload = [];
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                // Check if space separated "SMILES Name" or just SMILES
                const parts = line.split(/\s+/);
                const first = parts[0];
                const restName = parts.slice(1).join(' ') || `Compound ${i + 1}`;

                // If first part is a known name or SMILES, resolve it
                const resolved = await resolveSingleInput(first);
                moleculePayload.push({
                    smiles: resolved.smiles,
                    name: restName !== `Compound ${i + 1}` ? restName : resolved.name
                });
            }

            const authHeaders = await getAuthHeaders();
            const response = await fetch(SCAFFOLD_API_URL, {
                method: 'POST',
                headers: {
                    ...authHeaders,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    molecules: moleculePayload
                })
            });

            const data = await response.json().catch(() => null);

            if (!response.ok || !data) {
                const msg = data?.detail || data?.error || (response.status === 404 || response.status === 501
                    ? 'Cannot connect to Scaffold Analysis API on port 8000. Please ensure the FastAPI backend is running.'
                    : 'Failed to process multi-molecule comparison.');
                throw new Error(msg);
            }

            multiStatus.textContent = `Scaffold clustering and SAR comparison complete for ${data.molecule_count || 0} molecules.`;
            renderMultiResults(data);
        } catch (err) {
            showError(multiError, err.message || 'Multi-molecule analysis failed.');
            multiStatus.textContent = '';
            multiResults.hidden = true;
            multiResults.style.display = 'none';
        } finally {
            multiSubmitBtn.disabled = false;
        }
    }

    // Render Multi Results
    function renderMultiResults(data) {
        multiResults.hidden = false;
        multiResults.style.display = 'block';

        // Summary Bar
        setText('multi-total-count', data.molecule_count || 0);
        setText('multi-scaffold-count', data.unique_scaffold_count || 0);
        setText('multi-cluster-count', data.scaffold_groups?.length || 0);

        // Render Scaffold Groups
        const groupsContainer = document.getElementById('scaffold-groups-list');
        if (groupsContainer) {
            groupsContainer.innerHTML = '';
            const groups = data.scaffold_groups || [];

            if (groups.length === 0) {
                groupsContainer.innerHTML = '<p class="empty-state">No scaffold clusters identified.</p>';
            } else {
                groups.forEach(function (grp) {
                    const card = createScaffoldGroupCard(grp);
                    groupsContainer.appendChild(card);
                });
            }
        }

        // Render Tanimoto Matrix
        renderTanimotoMatrix(data.similarity_analysis);

        // Scroll to results
        multiResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Create DOM element for a Scaffold Cluster
    function createScaffoldGroupCard(group) {
        const card = document.createElement('article');
        card.className = 'scaffold-group-card';

        const isAcyclic = !group.has_scaffold;
        const badgeClass = isAcyclic ? 'badge-acyclic' : 'badge-ring';
        const scaffoldTitle = isAcyclic ? 'Acyclic Series (No Ring Core)' : (group.scaffold_smiles || 'Bemis-Murcko Core');

        // Member rows
        let rowsHtml = '';
        (group.members || []).forEach(function (m) {
            const cox2Active = m.cox2_prediction === 'Active';
            const egfrActive = m.egfr_prediction === 'Active';
            const cox2ProbStr = Number.isFinite(m.cox2_probability) ? `${(m.cox2_probability * 100).toFixed(1)}%` : '--';
            const egfrProbStr = Number.isFinite(m.egfr_probability) ? `${(m.egfr_probability * 100).toFixed(1)}%` : '--';

            rowsHtml += `
                <tr>
                    <td class="col-name"><strong>${escapeHtml(m.name || 'Compound')}</strong></td>
                    <td class="col-smiles"><code title="${escapeHtml(m.canonical_smiles || '')}">${escapeHtml(truncate(m.canonical_smiles, 34))}</code></td>
                    <td class="col-substituents">${escapeHtml(m.substituent_summary || '--')}</td>
                    <td class="col-pred">
                        <span class="outcome-pill ${cox2Active ? 'val-active' : 'val-inactive'}">
                            ${escapeHtml(m.cox2_prediction)} (${cox2ProbStr})
                        </span>
                    </td>
                    <td class="col-pred">
                        <span class="outcome-pill ${egfrActive ? 'val-active' : 'val-inactive'}">
                            ${escapeHtml(m.egfr_prediction)} (${egfrProbStr})
                        </span>
                    </td>
                    <td class="col-num">${formatNum(m.mw)}</td>
                    <td class="col-num">${formatNum(m.logp)}</td>
                </tr>
            `;
        });

        card.innerHTML = `
            <div class="group-card-header">
                <div class="group-header-left">
                    <span class="scaffold-badge ${badgeClass}">${escapeHtml(group.group_name || 'Scaffold Cluster')}</span>
                    <span class="group-count-pill">${group.member_count} Molecule${group.member_count === 1 ? '' : 's'}</span>
                </div>
            </div>

            <div class="group-card-body">
                <div class="group-scaffold-overview">
                    <div class="group-scaffold-thumb">
                        ${group.scaffold_svg ? group.scaffold_svg : '<div class="thumb-placeholder">⛓️<br><span>Acyclic</span></div>'}
                    </div>
                    <div class="group-scaffold-details">
                        <h4>${escapeHtml(scaffoldTitle)}</h4>
                        ${group.generic_framework_smiles ? `
                            <p class="generic-row"><strong>Generic Framework:</strong> <code>${escapeHtml(group.generic_framework_smiles)}</code></p>
                        ` : ''}
                        
                        <!-- Computational SAR Observation -->
                        <div class="group-sar-box">
                            <span class="sar-box-tag">Computational SAR Observation:</span>
                            <p>${escapeHtml(group.sar_observation || 'No SAR shifts detected.')}</p>
                        </div>
                    </div>
                </div>

                <!-- Analogue Comparison Table -->
                <div class="group-table-wrap">
                    <table class="group-analogue-table">
                        <thead>
                            <tr>
                                <th>Molecule</th>
                                <th>SMILES</th>
                                <th>Substituents (R-Groups)</th>
                                <th>COX-2 Prediction</th>
                                <th>EGFR Prediction</th>
                                <th>MW</th>
                                <th>LogP</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rowsHtml}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        return card;
    }

    // Render 2D Tanimoto Matrix
    function renderTanimotoMatrix(simData) {
        const table = document.getElementById('tanimoto-matrix-table');
        if (!table || !simData) return;

        const labels = simData.labels || [];
        const matrix = simData.tanimoto_matrix || [];

        let theadHtml = '<thead><tr><th>Molecule Pair</th>';
        labels.forEach(function (l) {
            theadHtml += `<th title="${escapeHtml(l)}">${escapeHtml(truncate(l, 14))}</th>`;
        });
        theadHtml += '</tr></thead>';

        let tbodyHtml = '<tbody>';
        for (let i = 0; i < matrix.length; i++) {
            const rowLabel = labels[i] || `M${i+1}`;
            tbodyHtml += `<tr><th class="matrix-row-header" title="${escapeHtml(rowLabel)}">${escapeHtml(truncate(rowLabel, 16))}</th>`;

            for (let j = 0; j < matrix[i].length; j++) {
                const val = matrix[i][j];
                const bgStyle = getHeatmapColor(val);
                tbodyHtml += `
                    <td class="matrix-cell" style="background-color: ${bgStyle.bg}; color: ${bgStyle.color};" title="${escapeHtml(labels[i])} vs ${escapeHtml(labels[j])}: Tanimoto ${val}">
                        ${Number(val).toFixed(2)}
                    </td>
                `;
            }
            tbodyHtml += '</tr>';
        }
        tbodyHtml += '</tbody>';

        table.innerHTML = theadHtml + tbodyHtml;
    }

    // Heatmap cell color generator based on Tanimoto score (0.0 to 1.0)
    function getHeatmapColor(val) {
        const num = Number(val);
        if (num >= 0.99) return { bg: '#581C87', color: '#FFFFFF' }; // 1.0 identical
        if (num >= 0.70) return { bg: '#7E22CE', color: '#FFFFFF' }; // 0.7 - 0.9 high similarity
        if (num >= 0.50) return { bg: '#A855F7', color: '#FFFFFF' }; // 0.5 - 0.7 moderate
        if (num >= 0.35) return { bg: '#DDD6FE', color: '#3B0764' }; // 0.35 - 0.5 low-moderate
        if (num >= 0.20) return { bg: '#EDE9FE', color: '#4C1D95' }; // 0.2 - 0.35 weak
        return { bg: '#F8F6FC', color: '#6B5E82' };                 // < 0.2 remote
    }

    // Check for preloaded SMILES in URL params
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const preSmiles = urlParams.get('smiles');
        const preName = urlParams.get('name');

        if (preSmiles && singleSmilesInput) {
            singleSmilesInput.value = preSmiles;
            singleSmilesInput.dataset.compoundName = preName || '';
            runSingleScaffoldAnalysis(preSmiles, preName || '');
        }
    } catch (e) {
        console.warn('URL preload failed:', e);
    }

    // Utilities
    function setText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }

    function formatNum(v) {
        return Number.isFinite(Number(v)) ? Number(v).toFixed(2) : '--';
    }

    function truncate(str, len) {
        if (!str) return '';
        return str.length > len ? str.substring(0, len) + '…' : str;
    }

    function showError(el, msg) {
        if (!el) return;
        el.textContent = msg;
        el.hidden = false;
        el.style.display = 'block';
    }

    function hideError(el) {
        if (!el) return;
        el.textContent = '';
        el.hidden = true;
        el.style.display = 'none';
    }

    function copyToClipboard(text, btn) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => showCopiedFeedback(btn));
        } else {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            try {
                document.execCommand('copy');
                showCopiedFeedback(btn);
            } catch (err) {}
            document.body.removeChild(ta);
        }
    }

    function showCopiedFeedback(btn) {
        const orig = btn.innerHTML;
        btn.innerHTML = '<span>✓ Copied!</span>';
        setTimeout(() => { btn.innerHTML = orig; }, 1800);
    }

    function escapeHtml(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
});
