/* =========================================================
    PAGE CONFIGURATION
   ========================================================= */

const API_HOST = window.location.hostname || "127.0.0.1";
const DRUG_LIKENESS_API_URL =
    `${["localhost", "127.0.0.1"].includes(API_HOST)
        ? `http://${API_HOST}:8000`
        : ""}/api/v1/drug-likeness`;
const PUBCHEM_NAME_URL =
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name";

/* =========================================================
    PAGE ELEMENTS AND LIPINSKI LABELS
   ========================================================= */

const form = document.getElementById("drug-likeness-form");
const smilesInput = document.getElementById("drug-smiles-input");
const analyzeButton = document.getElementById("drug-analyze-button");
const analyzeLabel = document.getElementById("drug-analyze-label");
const statusMessage = document.getElementById("drug-status");
const errorMessage = document.getElementById("drug-error");
const resultsSection = document.getElementById("drug-results");

let currentCompoundName = "";

const ruleLabels = {
    molecular_weight: "Molecular Weight ≤ 500 Da",
    logp: "LogP ≤ 5.0",
    hydrogen_bond_donors: "Hydrogen-bond donors ≤ 5",
    hydrogen_bond_acceptors: "Hydrogen-bond acceptors ≤ 10"
};

/* =========================================================
    SAMPLE BENCHMARK PILLS HANDLER
   ========================================================= */

document.querySelectorAll(".sample-pill-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
        const smiles = this.dataset.smiles;
        const name = this.dataset.name;
        if (smiles) {
            smilesInput.value = smiles;
            currentCompoundName = name || "";
            form.dispatchEvent(new Event("submit", { cancelable: true }));
        }
    });
});

/* =========================================================
    ERROR AND RESULT RENDERING
   ========================================================= */

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.hidden = false;
    statusMessage.textContent = "";
    resultsSection.hidden = true;
}

function displayResults(data, compoundName) {
    const descriptors = data.descriptors || {};
    const lip = data.lipinski || {};
    const isPass = Boolean(lip.passed);
    const violations = lip.violations !== undefined ? lip.violations : 0;
    const smiles = data.smiles || smilesInput.value.trim();
    const resolvedName = compoundName || currentCompoundName || (window.BAMI?.findBioactiveMoleculeBySmiles?.(smiles)?.name) || "Candidate Molecule";

    // 1. Analyzed chemical entity header
    const nameEl = document.getElementById("drug-analyzed-name");
    const smilesEl = document.getElementById("drug-analyzed-smiles");
    const tagEl = document.getElementById("drug-lead-tag");
    if (nameEl) nameEl.textContent = resolvedName;
    if (smilesEl) smilesEl.textContent = smiles;
    if (tagEl) {
        tagEl.textContent = isPass ? "Oral Drug-Like Candidate" : "Physicochemical Review Required";
        tagEl.className = isPass ? "lead-badge-entity badge-pass-pill" : "lead-badge-entity badge-review-pill";
    }

    // 2. Summary Status Banner
    const banner = document.getElementById("lipinski-status-banner");
    const statusBadge = document.getElementById("lipinski-status-badge");
    const statusTitle = document.getElementById("lipinski-status-title");
    const statusSubtitle = document.getElementById("lipinski-status-subtitle");

    if (banner && statusBadge && statusTitle && statusSubtitle) {
        if (isPass) {
            banner.className = "lipinski-status-banner status-banner-pass";
            statusBadge.textContent = "PASS";
            statusBadge.className = "status-banner-badge badge-pass";
            statusTitle.textContent = "5/5 criteria satisfied";
            statusSubtitle.textContent = "Favorable drug-like physicochemical properties for potential oral drug development.";
        } else {
            banner.className = "lipinski-status-banner status-banner-review";
            statusBadge.textContent = "REVIEW REQUIRED";
            statusBadge.className = "status-banner-badge badge-review";
            statusTitle.textContent = `${violations} Lipinski Rule Violation${violations === 1 ? "" : "s"} (${Math.max(0, 5 - violations)}/5 Criteria Satisfied)`;
            statusSubtitle.textContent = "Parameter review required. Note: Lipinski violations do not automatically disqualify oral candidacy.";
        }
    }

    // KPI Grid
    const kpiStatus = document.getElementById("kpi-status");
    const kpiScore = document.getElementById("kpi-score");
    const kpiViolations = document.getElementById("kpi-violations");
    const kpiOutlook = document.getElementById("kpi-outlook");

    if (kpiStatus) {
        kpiStatus.textContent = isPass ? "PASS" : "REVIEW REQUIRED";
        kpiStatus.className = `kpi-value ${isPass ? "status-val-pass" : "status-val-review"}`;
    }
    if (kpiScore) {
        kpiScore.textContent = isPass ? "5/5" : `${Math.max(0, 5 - violations)}/5`;
    }
    if (kpiViolations) {
        kpiViolations.textContent = String(violations);
        kpiViolations.className = `kpi-value ${violations === 0 ? "status-val-pass" : "status-val-review"}`;
    }
    if (kpiOutlook) {
        kpiOutlook.textContent = isPass ? "Favorable" : "Review Needed";
        kpiOutlook.className = `kpi-value ${isPass ? "status-val-pass" : "status-val-review"}`;
    }

    // 3. Exact Scientific Interpretation Box
    const interpText = document.getElementById("lipinski-interpretation-text");
    if (interpText) {
        if (lip.interpretation) {
            interpText.textContent = lip.interpretation;
        } else if (isPass) {
            interpText.textContent = "The molecule satisfies all five Lipinski thresholds, indicating favorable physicochemical properties for potential oral drug development. However, passing Lipinski's Rule of Five does not guarantee absorption, safety or therapeutic effectiveness. Further ADMET profiling and molecular docking analysis are required.";
        } else {
            interpText.textContent = "The molecule violates one or more Lipinski thresholds. This indicates potential challenges in oral drug development. However, Lipinski violations do not automatically disqualify a molecule. Further ADMET profiling and molecular docking analysis can provide additional information.";
        }
    }

    // 4. All Five Lipinski Thresholds Table
    const tableBody = document.getElementById("lipinski-table-body");
    if (tableBody) {
        tableBody.replaceChildren();

        const paramDefinitions = [
            {
                key: "molecular_weight",
                name: "Molecular Weight",
                subdesc: "Total relative molecular mass",
                val: `${Number(descriptors.Molecular_Weight).toFixed(2)} Da`,
                threshold: "≤ 500.0 Da",
                rule: lip.rules?.molecular_weight
            },
            {
                key: "logp",
                name: "LogP (Octanol/Water Partition)",
                subdesc: "Estimated lipophilicity (MolLogP)",
                val: `${Number(descriptors.LogP).toFixed(2)}`,
                threshold: "≤ 5.00",
                rule: lip.rules?.logp
            },
            {
                key: "hydrogen_bond_donors",
                name: "Hydrogen Bond Donors (HBD)",
                subdesc: "Sum of OH and NH donor groups",
                val: String(descriptors.HBD),
                threshold: "≤ 5",
                rule: lip.rules?.hydrogen_bond_donors
            },
            {
                key: "hydrogen_bond_acceptors",
                name: "Hydrogen Bond Acceptors (HBA)",
                subdesc: "Sum of oxygen and nitrogen heteroatoms",
                val: String(descriptors.HBA),
                threshold: "≤ 10",
                rule: lip.rules?.hydrogen_bond_acceptors
            }
        ];

        paramDefinitions.forEach((p) => {
            const tr = document.createElement("tr");
            const passed = p.rule ? Boolean(p.rule.passed) : true;

            tr.innerHTML = `
                <td>
                    <strong class="param-title">${p.name}</strong>
                    <span class="param-subdesc">${p.subdesc}</span>
                </td>
                <td>
                    <code class="val-code">${p.val}</code>
                </td>
                <td>
                    <span class="threshold-pill">${p.threshold}</span>
                </td>
                <td>
                    <span class="rule-status-badge ${passed ? "badge-pass" : "badge-fail"}">
                        ${passed ? "✓ PASS" : "✕ FAIL"}
                    </span>
                </td>
            `;
            tableBody.appendChild(tr);
        });
    }

    // 5. Violations & Mechanistic Rationale Box
    const violationsCard = document.getElementById("lipinski-violations-card");
    const violationsList = document.getElementById("lipinski-violations-list");

    if (violationsCard && violationsList) {
        if (!isPass && violations > 0) {
            violationsCard.hidden = false;
            violationsList.replaceChildren();

            const failedList = lip.failed_parameters && lip.failed_parameters.length > 0
                ? lip.failed_parameters
                : Object.entries(lip.rules || {})
                    .filter(([_, r]) => !r.passed)
                    .map(([k, r]) => ({
                        parameter: r.name || k,
                        value: r.value,
                        unit: r.unit || "",
                        threshold: r.display_threshold || r.threshold,
                        reason: r.failure_reason || "Value exceeds the recommended Lipinski threshold."
                    }));

            failedList.forEach((f) => {
                const item = document.createElement("div");
                item.className = "violation-item";
                item.innerHTML = `
                    <div class="violation-item-header">
                        <span class="violation-bullet-badge">✕</span>
                        <strong class="violation-item-title">${f.parameter} Exceeded:</strong>
                        <span class="violation-measured-tag">${f.value} ${f.unit || ""} (Threshold: ${f.threshold})</span>
                    </div>
                    <p class="violation-mechanistic-reason">${f.reason}</p>
                `;
                violationsList.appendChild(item);
            });
        } else {
            violationsCard.hidden = true;
            violationsList.replaceChildren();
        }
    }

    // 6. General Molecular Descriptors (6 features)
    const mwEl = document.getElementById("drug-mw");
    const logpEl = document.getElementById("drug-logp");
    const hbdEl = document.getElementById("drug-hbd");
    const hbaEl = document.getElementById("drug-hba");
    const tpsaEl = document.getElementById("drug-tpsa");
    const rotEl = document.getElementById("drug-rotatable");

    if (mwEl) mwEl.textContent = Number(descriptors.Molecular_Weight).toFixed(2);
    if (logpEl) logpEl.textContent = Number(descriptors.LogP).toFixed(2);
    if (hbdEl) hbdEl.textContent = descriptors.HBD;
    if (hbaEl) hbaEl.textContent = descriptors.HBA;
    if (tpsaEl) tpsaEl.textContent = Number(descriptors.TPSA).toFixed(2);
    if (rotEl) rotEl.textContent = descriptors.Rotatable_Bonds;

    // 7. Workflow Integration Links (Connecting Lipinski with other BAMI enhancements)
    const encodedSmiles = encodeURIComponent(smiles);
    const encodedName = encodeURIComponent(resolvedName);
    const queryStr = `smiles=${encodedSmiles}&name=${encodedName}&auto=1`;

    const admetBtn = document.getElementById("action-btn-admet");
    const dockingBtn = document.getElementById("action-btn-docking");
    const scaffoldBtn = document.getElementById("action-btn-scaffold");
    const predBtn = document.getElementById("action-btn-prediction");

    if (admetBtn) admetBtn.href = `admet.html?${queryStr}`;
    if (dockingBtn) dockingBtn.href = `docking.html?${queryStr}`;
    if (scaffoldBtn) scaffoldBtn.href = `scaffold-analysis.html?${queryStr}`;
    if (predBtn) predBtn.href = `single-prediction.html?${queryStr}`;

    // 8. Legacy element fallback
    const overall = document.getElementById("lipinski-overall");
    if (overall) {
        overall.textContent = isPass
            ? `PASS · ${violations} rule violations`
            : `REVIEW REQUIRED · ${violations} rule violation${violations === 1 ? "" : "s"}`;
        overall.className = `lipinski-overall ${isPass ? "status-pass" : "status-fail"}`;
    }
    const rulesList = document.getElementById("lipinski-rules");
    if (rulesList && lip.rules) {
        rulesList.replaceChildren();
        Object.entries(lip.rules).forEach(([ruleName, rule]) => {
            const item = document.createElement("li");
            const label = document.createElement("span");
            const result = document.createElement("strong");
            const passed = Boolean(rule.passed);
            label.textContent = ruleLabels[ruleName] || ruleName;
            result.textContent = passed ? "PASS" : "FAIL";
            result.className = passed ? "status-pass" : "status-fail";
            item.append(label, result);
            rulesList.append(item);
        });
    }

    errorMessage.hidden = true;
    resultsSection.hidden = false;
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* =========================================================
    BACKEND AND PUBCHEM REQUESTS
   ========================================================= */

async function getAuthHeaders() {
    if (typeof window.getFirebaseAuthHeaders === "function") {
        try {
            return await window.getFirebaseAuthHeaders();
        } catch (e) {
            console.warn("Auth header lookup:", e);
        }
    }
    for (let i = 0; i < 25; i++) {
        await new Promise((resolve) => setTimeout(resolve, 80));
        if (typeof window.getFirebaseAuthHeaders === "function") {
            try {
                return await window.getFirebaseAuthHeaders();
            } catch (e) {
                console.warn("Auth header lookup:", e);
            }
        }
    }
    return {};
}

async function requestAnalysis(smiles) {
    const authHeaders = await getAuthHeaders();
    const response = await fetch(DRUG_LIKENESS_API_URL, {
        method: "POST",
        headers: {
            ...authHeaders,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ smiles })
    });
    const data = await response.json().catch(() => null);
    return { response, data };
}

async function resolveMoleculeName(name) {
    const localMatch = window.BAMI?.findBioactiveMoleculeByName?.(name);
    if (localMatch && localMatch.smiles) {
        return localMatch.smiles;
    }

    let response;
    try {
        const url = `${PUBCHEM_NAME_URL}/${encodeURIComponent(name)}/property/CanonicalSMILES,IsomericSMILES,ConnectivitySMILES/JSON`;
        response = await fetch(url);
    } catch (error) {
        throw new Error("Could not reach PubChem to look up that molecule name. Check your internet connection or enter a SMILES string.");
    }

    if (response.status === 404) {
        throw new Error(`No molecule was found for "${name}". Check the name or enter a valid SMILES.`);
    }
    if (!response.ok) {
        throw new Error("PubChem name lookup is unavailable. Try again later or enter a SMILES string.");
    }

    const data = await response.json();
    const properties = data.PropertyTable?.Properties || [];
    if (properties.length !== 1) {
        throw new Error("That name did not resolve to one unique molecule. Try a more specific name or enter a SMILES string.");
    }

    const molecule = properties[0];
    const smiles = molecule.SMILES ||
        molecule.IsomericSMILES ||
        molecule.ConnectivitySMILES;
    if (!smiles) {
        throw new Error("PubChem did not provide a structure for that molecule name.");
    }

    return smiles;
}

/* =========================================================
    DRUG-LIKENESS FORM WORKFLOW
   ========================================================= */

form.addEventListener("submit", async function (event) {
    event.preventDefault();
    const input = smilesInput.value.trim();

    errorMessage.hidden = true;
    resultsSection.hidden = true;

    if (!input) {
        showError("Enter a molecule name or SMILES string before analyzing.");
        smilesInput.focus();
        return;
    }

    analyzeButton.disabled = true;
    analyzeLabel.textContent = "Analyzing...";
    statusMessage.textContent = "Calculating molecular descriptors and Lipinski rules…";

    try {
        let { response, data } = await requestAnalysis(input);
        let resolvedName = currentCompoundName || "";

        if (response.status === 422) {
            statusMessage.textContent = "Looking up molecule name through PubChem…";
            const resolvedSmiles = await resolveMoleculeName(input);
            resolvedName = input;
            currentCompoundName = input;
            statusMessage.textContent = "Name found. Calculating molecular descriptors and Lipinski rules…";
            ({ response, data } = await requestAnalysis(resolvedSmiles));
        }

        if (!response.ok) {
            const detail = data?.detail;
            throw new Error(
                typeof detail === "string"
                    ? detail
                    : detail?.message || "The analysis request could not be completed."
            );
        }

        displayResults(data, resolvedName);
        statusMessage.textContent = resolvedName
            ? `Analysis complete for ${resolvedName}.`
            : "Analysis complete.";
    } catch (error) {
        const message = error instanceof TypeError
            ? "Could not reach the analysis service. Check that the backend is running and try again."
            : error.message;
        showError(message);
    } finally {
        analyzeButton.disabled = false;
        analyzeLabel.textContent = "Analyze Drug-Likeness";
    }
});

/* Initialize live molecule autocomplete for drug likeness search */
if (typeof initMoleculeAutocomplete === "function") {
    initMoleculeAutocomplete({
        input: smilesInput,
        container: document.getElementById("drug-search-container"),
        dropdown: document.getElementById("drug-suggestions-dropdown"),
        onSelect: (molecule) => {
            smilesInput.value = molecule.smiles || molecule.name;
            currentCompoundName = molecule.name || "";
        }
    });
}

/* =========================================================
   AUTO-ANALYZE WHEN REDIRECTED FROM AN ACTIVE PREDICTION
   ========================================================= */

async function checkAndHandleAutoAnalysis() {
    const params = new URLSearchParams(window.location.search);
    let smilesParam = params.get("smiles") || params.get("compound") || params.get("q");
    let nameParam = params.get("name");
    const autoAnalyze = params.get("auto") === "1" || params.get("auto") === "true";
    const fromActive = params.get("from") === "active_prediction";
    const targetParam = params.get("target");

    if (!smilesParam) {
        try {
            const raw = sessionStorage.getItem("bami_auto_drug_likeness");
            if (raw) {
                const stored = JSON.parse(raw);
                if (stored && stored.smiles && (Date.now() - (stored.timestamp || 0) < 120000)) {
                    smilesParam = stored.smiles;
                    nameParam = stored.name || nameParam;
                }
            }
        } catch (e) {}
    }

    if (smilesParam) {
        smilesInput.value = smilesParam;

        if (autoAnalyze || fromActive) {
            try {
                sessionStorage.removeItem("bami_auto_drug_likeness");
            } catch (e) {}

            const displayLabel = nameParam && nameParam !== smilesParam ? `${nameParam} (${smilesParam})` : smilesParam;
            const targetNote = targetParam ? ` against ${targetParam}` : "";
            statusMessage.textContent = `Active lead detected${targetNote}! Automatically analyzing Lipinski's Rule of Five…`;

            // Give a brief moment for autocomplete and auth initialization, then trigger form submission
            setTimeout(() => {
                form.dispatchEvent(new Event("submit", { cancelable: true }));
            }, 180);
        }
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", checkAndHandleAutoAnalysis);
} else {
    checkAndHandleAutoAnalysis();
}
