/* =========================================================
   BAMI PREDICTION HISTORY CONTROLLER
   Renders and manages the 50 most recent predictions from local storage.
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    const historySearch = document.getElementById('history-search');
    const targetFilter = document.getElementById('history-target-filter');
    const outcomeFilter = document.getElementById('history-outcome-filter');
    const historyCount = document.getElementById('history-count');
    const historyLoading = document.getElementById('history-loading');
    const historyEmpty = document.getElementById('history-empty');
    const historyNoMatches = document.getElementById('history-no-matches');
    const historyList = document.getElementById('history-list');
    const resetFiltersBtn = document.getElementById('reset-filters-btn');
    const loadSampleBtn = document.getElementById('load-sample-btn');
    const loadSampleToolbarBtn = document.getElementById('history-load-samples-toolbar');
    const clearAllBtn = document.getElementById('history-clear-all-btn');

    let allEntries = [];

    // Helper to reliably toggle visibility with both HTML5 hidden attribute and inline display
    function setElementVisibility(el, visible, displayStyle = 'flex') {
        if (!el) return;
        el.hidden = !visible;
        el.style.display = visible ? displayStyle : 'none';
    }

    // Initialize history loader
    function init() {
        try {
            allEntries = window.BAMIHistory ? window.BAMIHistory.getHistory() : [];
        } catch (e) {
            console.warn('Could not read history:', e);
            allEntries = [];
        }

        setElementVisibility(historyLoading, false);

        render();
        setupEventListeners();
    }

    // Set up filter and action listeners
    function setupEventListeners() {
        if (historySearch) {
            historySearch.addEventListener('input', debounce(render, 150));
        }
        if (targetFilter) {
            targetFilter.addEventListener('change', render);
        }
        if (outcomeFilter) {
            outcomeFilter.addEventListener('change', render);
        }
        if (resetFiltersBtn) {
            resetFiltersBtn.addEventListener('click', function () {
                if (historySearch) historySearch.value = '';
                if (targetFilter) targetFilter.value = 'all';
                if (outcomeFilter) outcomeFilter.value = 'all';
                render();
            });
        }
        if (loadSampleBtn) {
            loadSampleBtn.addEventListener('click', function () {
                loadSamplePredictions();
            });
        }
        if (loadSampleToolbarBtn) {
            loadSampleToolbarBtn.addEventListener('click', function () {
                loadSamplePredictions();
            });
        }
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', function () {
                if (window.confirm('Are you sure you want to clear all saved prediction history on this device?')) {
                    if (window.BAMIHistory && typeof window.BAMIHistory.clearHistory === 'function') {
                        window.BAMIHistory.clearHistory();
                    }
                    allEntries = [];
                    render();
                }
            });
        }

        // Delegate clicks on history list for copy, expand/collapse, and remove
        if (historyList) {
            historyList.addEventListener('click', handleListClick);
        }
    }

    // Filter entries according to active controls
    function getFilteredEntries() {
        const query = (historySearch ? historySearch.value.trim().toLowerCase() : '');
        const selectedTarget = (targetFilter ? targetFilter.value : 'all');
        const selectedOutcome = (outcomeFilter ? outcomeFilter.value : 'all');

        return allEntries.filter(function (entry) {
            // Target filter
            if (selectedTarget !== 'all' && entry.target !== selectedTarget) {
                return false;
            }

            // Outcome filter
            if (selectedOutcome !== 'all' && entry.prediction !== selectedOutcome) {
                return false;
            }

            // Text search query
            if (query) {
                const name = (entry.compound_name || '').toLowerCase();
                const smiles = (entry.smiles || '').toLowerCase();
                const input = (entry.input || '').toLowerCase();
                const target = (entry.target || '').toLowerCase();
                const model = (entry.model || '').toLowerCase();
                const pred = (entry.prediction || '').toLowerCase();

                const matches = name.includes(query) ||
                    smiles.includes(query) ||
                    input.includes(query) ||
                    target.includes(query) ||
                    model.includes(query) ||
                    pred.includes(query);

                if (!matches) return false;
            }

            return true;
        });
    }

    // Main render pipeline
    function render() {
        if (!historyList) return;

        // Ensure loading state is completely hidden
        setElementVisibility(historyLoading, false);

        // If storage has no entries at all
        if (!allEntries || allEntries.length === 0) {
            setElementVisibility(historyEmpty, true, 'flex');
            setElementVisibility(historyNoMatches, false);
            setElementVisibility(clearAllBtn, false);
            historyList.innerHTML = '';
            if (historyCount) historyCount.textContent = '0 saved predictions';
            return;
        }

        setElementVisibility(historyEmpty, false);
        setElementVisibility(clearAllBtn, true, 'inline-block');

        const filtered = getFilteredEntries();

        // If search/filter returns 0 matches
        if (filtered.length === 0) {
            setElementVisibility(historyNoMatches, true, 'flex');
            historyList.innerHTML = '';
            if (historyCount) historyCount.textContent = `0 of ${allEntries.length} predictions match your filters`;
            return;
        }

        setElementVisibility(historyNoMatches, false);
        if (historyCount) {
            historyCount.textContent = `Showing ${filtered.length} of ${allEntries.length} saved prediction${allEntries.length === 1 ? '' : 's'}`;
        }

        // Render card fragment
        const fragment = document.createDocumentFragment();

        filtered.forEach(function (entry) {
            const card = createHistoryCard(entry);
            fragment.appendChild(card);
        });

        historyList.innerHTML = '';
        historyList.appendChild(fragment);
    }

    // Construct DOM element for a single prediction card
    function createHistoryCard(entry) {
        const card = document.createElement('article');
        card.className = 'history-card';
        card.setAttribute('data-id', entry.id);

        const isEgfr = entry.target === 'EGFR';
        const targetClass = isEgfr ? 'badge-egfr' : 'badge-cox2';
        const isActive = entry.prediction === 'Active';
        const outcomeClass = isActive ? 'outcome-active' : 'outcome-inactive';

        // Score display handling
        let scoreLabel = 'Model Score';
        let scorePercentage = null;
        if (Number.isFinite(entry.score)) {
            scorePercentage = (entry.score * 100).toFixed(1);
            if (entry.score_type === 'calibrated_probability') {
                scoreLabel = 'Calibrated Probability';
            } else if (entry.score_type === 'model_probability') {
                scoreLabel = 'Model Probability';
            }
        }

        const thresholdPercentage = Number.isFinite(entry.threshold)
            ? (entry.threshold * 100).toFixed(1)
            : '50.0';

        const formattedDate = window.BAMIHistory
            ? window.BAMIHistory.formatDate(entry.timestamp)
            : (entry.timestamp || '--');

        const compoundTitle = entry.compound_name || (entry.input !== entry.smiles ? entry.input : '') || 'Molecule Lead';
        const smilesDisplay = entry.smiles || entry.input || '--';

        // Build HTML
        card.innerHTML = `
            <div class="history-card-header">
                <div class="history-card-meta">
                    <span class="history-date">${escapeHtml(formattedDate)}</span>
                    <span class="history-target-badge ${targetClass}">${escapeHtml(entry.target || 'Target')}</span>
                </div>
                <div class="history-outcome-badge ${outcomeClass}">
                    <span class="status-dot"></span>
                    <span>${escapeHtml(entry.prediction || 'Unknown')}</span>
                </div>
            </div>

            <div class="history-card-body">
                <h3 class="history-molecule-title">${escapeHtml(compoundTitle)}</h3>
                
                <div class="history-smiles-box">
                    <span class="smiles-label">SMILES</span>
                    <code class="smiles-code" title="${escapeHtml(smilesDisplay)}">${escapeHtml(smilesDisplay)}</code>
                    <button type="button" class="history-copy-btn" data-copy="${escapeHtml(smilesDisplay)}" aria-label="Copy SMILES string">
                        <span class="copy-icon">📋</span> Copy
                    </button>
                </div>

                <div class="history-metrics-row">
                    ${scorePercentage !== null ? `
                        <div class="metric-pill">
                            <span class="metric-label">${escapeHtml(scoreLabel)}:</span>
                            <strong class="metric-val ${isActive ? 'val-active' : ''}">${scorePercentage}%</strong>
                        </div>
                    ` : ''}
                    <div class="metric-pill">
                        <span class="metric-label">Decision Threshold:</span>
                        <strong class="metric-val">${thresholdPercentage}%</strong>
                    </div>
                    <div class="metric-pill model-name-pill" title="${escapeHtml(entry.model || 'XGBoost')}">
                        <span class="metric-label">Model:</span>
                        <span class="metric-val">${escapeHtml(entry.model || 'XGBoost')}</span>
                    </div>
                </div>

                <!-- Expandable Saved Results Drawer -->
                <div class="history-expandable-section" id="details-${escapeHtml(entry.id)}" hidden style="display: none;">
                    <div class="saved-descriptors-box">
                        <h4>Saved Molecular Descriptors (Lipinski Rule of 5)</h4>
                        ${renderDescriptorsGrid(entry.descriptors)}
                        
                        <div class="saved-pipeline-meta">
                            <span><strong>Target UniProt:</strong> ${escapeHtml(entry.target_uniprot || (isEgfr ? 'P00533' : 'P35354'))}</span>
                            <span><strong>Representation:</strong> Morgan Fingerprint (Radius 2, 2,048 bits)</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="history-card-footer">
                <button type="button" class="history-toggle-btn" aria-expanded="false" data-toggle="details-${escapeHtml(entry.id)}">
                    <span>View Saved Results</span>
                    <span class="arrow-icon" aria-hidden="true">▾</span>
                </button>

                <div class="history-card-actions">
                    <a href="index.html?smiles=${encodeURIComponent(entry.smiles)}&target=${encodeURIComponent(entry.target)}&name=${encodeURIComponent(entry.compound_name || '')}" class="history-open-btn" title="Open this molecule in the Predictor without retyping">
                        Open in Predictor &rarr;
                    </a>
                    <button type="button" class="history-delete-btn" data-delete-id="${escapeHtml(entry.id)}" title="Delete this entry from local history" aria-label="Delete entry">
                        ✕
                    </button>
                </div>
            </div>
        `;

        return card;
    }

    // Helper to format saved Lipinski descriptors
    function renderDescriptorsGrid(desc) {
        if (!desc || typeof desc !== 'object') {
            return '<p class="no-descriptors-note">No molecular descriptors recorded for this entry.</p>';
        }

        const formatNum = function (v) {
            return Number.isFinite(Number(v)) ? Number(v).toFixed(2) : '--';
        };

        return `
            <div class="descriptors-compact-grid">
                <div class="compact-desc-item">
                    <span class="desc-k">MW</span>
                    <strong class="desc-v">${formatNum(desc.mw)}</strong>
                    <span class="desc-sub">g/mol (&le;500)</span>
                </div>
                <div class="compact-desc-item">
                    <span class="desc-k">LogP</span>
                    <strong class="desc-v">${formatNum(desc.logp)}</strong>
                    <span class="desc-sub">Lipophilicity (&le;5)</span>
                </div>
                <div class="compact-desc-item">
                    <span class="desc-k">TPSA</span>
                    <strong class="desc-v">${formatNum(desc.tpsa)}</strong>
                    <span class="desc-sub">&Aring;&sup2; (&le;140)</span>
                </div>
                <div class="compact-desc-item">
                    <span class="desc-k">HBD</span>
                    <strong class="desc-v">${desc.hbd !== null && desc.hbd !== undefined ? desc.hbd : '--'}</strong>
                    <span class="desc-sub">Donors (&le;5)</span>
                </div>
                <div class="compact-desc-item">
                    <span class="desc-k">HBA</span>
                    <strong class="desc-v">${desc.hba !== null && desc.hba !== undefined ? desc.hba : '--'}</strong>
                    <span class="desc-sub">Acceptors (&le;10)</span>
                </div>
                <div class="compact-desc-item">
                    <span class="desc-k">Rotatable</span>
                    <strong class="desc-v">${desc.rotatable_bonds !== null && desc.rotatable_bonds !== undefined ? desc.rotatable_bonds : '--'}</strong>
                    <span class="desc-sub">Bonds (&le;10)</span>
                </div>
            </div>
        `;
    }

    // Handle delegated click interactions
    function handleListClick(e) {
        const copyBtn = e.target.closest('.history-copy-btn');
        if (copyBtn) {
            const textToCopy = copyBtn.getAttribute('data-copy');
            if (textToCopy) {
                copyToClipboard(textToCopy, copyBtn);
            }
            return;
        }

        const toggleBtn = e.target.closest('.history-toggle-btn');
        if (toggleBtn) {
            const targetId = toggleBtn.getAttribute('data-toggle');
            const drawer = document.getElementById(targetId);
            if (drawer) {
                const willShow = drawer.hidden || drawer.style.display === 'none';
                drawer.hidden = !willShow;
                drawer.style.display = willShow ? 'block' : 'none';
                toggleBtn.setAttribute('aria-expanded', String(willShow));
                const textSpan = toggleBtn.querySelector('span:first-child');
                const arrow = toggleBtn.querySelector('.arrow-icon');
                if (textSpan) {
                    textSpan.textContent = willShow ? 'Hide Saved Results' : 'View Saved Results';
                }
                if (arrow) {
                    arrow.textContent = willShow ? '▴' : '▾';
                }
            }
            return;
        }

        const deleteBtn = e.target.closest('.history-delete-btn');
        if (deleteBtn) {
            const idToDelete = deleteBtn.getAttribute('data-delete-id');
            if (idToDelete) {
                removeEntry(idToDelete);
            }
            return;
        }
    }

    // Clipboard copy with feedback tooltip
    function copyToClipboard(text, btnElement) {
        if (!navigator.clipboard) {
            // Fallback
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                showCopiedFeedback(btnElement);
            } catch (err) {
                console.warn('Copy failed', err);
            }
            document.body.removeChild(textarea);
            return;
        }

        navigator.clipboard.writeText(text).then(function () {
            showCopiedFeedback(btnElement);
        }).catch(function (err) {
            console.warn('Clipboard write error:', err);
        });
    }

    function showCopiedFeedback(btnElement) {
        const originalText = btnElement.innerHTML;
        btnElement.classList.add('copied');
        btnElement.innerHTML = '<span>✓ Copied!</span>';
        setTimeout(function () {
            btnElement.classList.remove('copied');
            btnElement.innerHTML = originalText;
        }, 1800);
    }

    // Delete single entry from history
    function removeEntry(id) {
        if (window.BAMIHistory && typeof window.BAMIHistory.removeEntry === 'function') {
            window.BAMIHistory.removeEntry(id);
        }
        allEntries = allEntries.filter(function (e) {
            return e.id !== id;
        });
        render();
    }

    // Load sample predictions for user testing if empty
    function loadSamplePredictions() {
        if (!window.BAMIHistory) return;

        const samples = [
            {
                prediction: 'Active',
                target: 'COX-2',
                target_uniprot: 'P35354',
                canonical_smiles: 'CC(=O)Oc1ccccc1C(=O)O',
                probability_active: 0.865,
                probability_type: 'model_probability',
                classification_threshold: 0.5,
                model: 'Final XGBoost - Morgan Fingerprint',
                molecular_descriptors: {
                    molecular_weight: 180.16,
                    logp: 1.19,
                    tpsa: 63.60,
                    h_bond_donors: 1,
                    h_bond_acceptors: 3,
                    rotatable_bonds: 3
                }
            },
            {
                prediction: 'Active',
                target: 'EGFR',
                target_uniprot: 'P00533',
                canonical_smiles: 'COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1',
                probability_active: 0.942,
                probability_type: 'calibrated_probability',
                classification_threshold: 0.44,
                model: 'Tuned EGFR XGBoost - Morgan Fingerprint',
                molecular_descriptors: {
                    molecular_weight: 446.90,
                    logp: 3.75,
                    tpsa: 68.74,
                    h_bond_donors: 1,
                    h_bond_acceptors: 7,
                    rotatable_bonds: 6
                }
            },
            {
                prediction: 'Inactive',
                target: 'EGFR',
                target_uniprot: 'P00533',
                canonical_smiles: 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O',
                probability_active: 0.128,
                probability_type: 'calibrated_probability',
                classification_threshold: 0.44,
                model: 'Tuned EGFR XGBoost - Morgan Fingerprint',
                molecular_descriptors: {
                    molecular_weight: 206.28,
                    logp: 3.50,
                    tpsa: 37.30,
                    h_bond_donors: 1,
                    h_bond_acceptors: 1,
                    rotatable_bonds: 4
                }
            }
        ];

        // Add samples in reverse order so Aspirin (first) appears at the very top (newest first)
        samples.slice().reverse().forEach(function (sample) {
            const name = sample.target === 'COX-2' ? 'Aspirin' : (sample.prediction === 'Active' ? 'Gefitinib' : 'Ibuprofen');
            window.BAMIHistory.addPrediction(sample, {
                compoundName: name,
                rawInput: sample.canonical_smiles,
                target: sample.target
            });
        });

        // Reset search/filter inputs so user immediately sees all loaded samples
        if (historySearch) historySearch.value = '';
        if (targetFilter) targetFilter.value = 'all';
        if (outcomeFilter) outcomeFilter.value = 'all';

        allEntries = window.BAMIHistory.getHistory();
        render();
    }

    // Debounce utility
    function debounce(func, wait) {
        let timeout;
        return function () {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(function () {
                func.apply(context, args);
            }, wait);
        };
    }

    // HTML escape utility
    function escapeHtml(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // Run initialization
    init();
});
