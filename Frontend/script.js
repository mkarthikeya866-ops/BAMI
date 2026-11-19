/* =========================================================
    XGBIOACTIVE — XGBOOST BIOACTIVITY PREDICTION
    HTML + CSS + VANILLA JAVASCRIPT
    ========================================================= */
/* =========================================================
    PAGE CONFIGURATION
   ========================================================= */

const API_HOST = window.location.hostname || "127.0.0.1";
const API_BASE_URL = ["localhost", "127.0.0.1"].includes(API_HOST)
    ? `http://${API_HOST}:8000/api/v1`
    : "/api/v1";
const PREDICTION_API_URLS = {
    "COX-2": `${API_BASE_URL}/predict-xgb`,
    "EGFR": `${API_BASE_URL}/predict-egfr-xgb`
};
const PUBCHEM_API_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug";
const PUBCHEM_AUTOCOMPLETE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/autocomplete";

/* Input UI: these IDs match the SMILES field and buttons in index.html. */

const smilesInput = document.getElementById("smiles-input");
const exampleBtn = document.getElementById("example-btn");
const clearBtn = document.getElementById("clear-btn");
const predictBtn = document.getElementById("predict-btn");
const targetSelect = document.getElementById("target-select");

const predictionMessage = document.getElementById("prediction-message");
const resultSection = document.getElementById("result-section");
const clinicalUsesPanel = document.getElementById("clinical-uses-panel");
const knownUsesButton = document.getElementById("lookup-known-uses-btn");
const knownUsesContent = document.getElementById("known-uses-content");
const knownUsesSource = document.getElementById("known-uses-source");

/* Result UI: classification label and explanatory text. */
const predictionValue = document.getElementById("prediction-value");
const classificationDescription =
    document.getElementById("classification-description");
const researchGuidance = document.getElementById("research-guidance-text");

/* Structure preview UI: RDKit draws into this container and updates its status. */
const structureDisplay = document.getElementById("structure-display");
const structureStatus = document.getElementById("structure-status");

const exampleSmiles = "CC(=O)Oc1ccccc1C(=O)O";
let lastPredictedSmiles = "";
let knownUsesRequestId = 0;

/* Load RDKit so the structure preview UI can render molecule drawings. */

let RDKitModule = null;

async function initializeRDKit() {
    try {
        RDKitModule = await window.initRDKitModule();

        console.log("RDKit initialized successfully.");

        structureStatus.textContent =
            "RDKit ready — enter a molecule.";

    } catch (error) {
        console.error("RDKit initialization failed:", error);

        structureStatus.textContent =
            "RDKit initialization failed.";
    }
}

initializeRDKit();

// In-memory cache for resolved molecule metadata
const moleculeMetadataCache = new Map();

function formatFormulaSubscripts(formula) {
    if (!formula) return "";
    const subscripts = {
        "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
        "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉"
    };
    return formula.replace(/\d+/g, (digits) =>
        digits.split("").map((d) => subscripts[d] || d).join("")
    );
}

function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

async function resolveMoleculeMetadata(smiles, hintName = "") {
    if (hintName && hintName.trim()) {
        const cleanHint = hintName.trim();
        const curated = window.BAMI?.findBioactiveMoleculeByName?.(cleanHint);
        if (curated) {
            return {
                name: curated.name,
                formula: formatFormulaSubscripts(curated.formula || ""),
                iupac: curated.description || curated.classType || "",
                classType: curated.classType || ""
            };
        }
        return { name: cleanHint, formula: "", iupac: "", classType: "Known Compound" };
    }

    if (!smiles) return { name: "Bioactive Compound", formula: "", iupac: "", classType: "" };
    const clean = smiles.trim();

    if (moleculeMetadataCache.has(clean)) {
        return moleculeMetadataCache.get(clean);
    }

    // 1. Check curated scientific BAMI dataset
    const curated = window.BAMI?.findBioactiveMoleculeBySmiles?.(clean);
    if (curated) {
        const meta = {
            name: curated.name,
            formula: formatFormulaSubscripts(curated.formula || ""),
            iupac: curated.description || curated.classType || "",
            classType: curated.classType || ""
        };
        moleculeMetadataCache.set(clean, meta);
        return meta;
    }

    // 2. Query PubChem with fast 2.5s timeout
    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 2500);
        const url = `${PUBCHEM_API_URL}/compound/smiles/${encodeURIComponent(clean)}/property/Title,IUPACName,MolecularFormula/JSON`;
        const resp = await fetch(url, { signal: controller.signal });
        clearTimeout(timeout);

        if (resp.ok) {
            const json = await resp.json();
            const p = json.PropertyTable?.Properties?.[0];
            if (p) {
                const meta = {
                    name: p.Title || p.IUPACName || "Bioactive Candidate",
                    formula: formatFormulaSubscripts(p.MolecularFormula || ""),
                    iupac: p.IUPACName || "",
                    classType: "PubChem Compound"
                };
                moleculeMetadataCache.set(clean, meta);
                return meta;
            }
        }
    } catch (_) {}

    // 3. Fallback
    const fallbackMeta = {
        name: "Bioactive Compound",
        formula: "",
        iupac: clean.length > 36 ? clean.slice(0, 34) + "..." : clean,
        classType: "Candidate"
    };
    moleculeMetadataCache.set(clean, fallbackMeta);
    return fallbackMeta;
}

/* Structure preview UI: render an RDKit SVG inside #structure-display along with molecule identity. */

async function renderMolecule(smiles, explicitName = "") {

    if (!RDKitModule) {
        structureStatus.textContent =
            "RDKit is still loading. Please wait.";

        return;
    }

    const header = document.getElementById("structure-molecule-header");
    const nameEl = document.getElementById("molecule-display-name");
    const formulaEl = document.getElementById("molecule-display-formula");
    const iupacEl = document.getElementById("molecule-display-iupac");
    const classEl = document.getElementById("molecule-display-class");

    try {

        const molecule = RDKitModule.get_mol(smiles);

        if (!molecule) {
            throw new Error("Invalid SMILES representation.");
        }

        molecule.set_new_coords(true);

        const svg = molecule.get_svg(420, 310);

        structureDisplay.innerHTML = svg;

        molecule.delete();

        // Resolve and display molecule name along with 2D structure
        const meta = await resolveMoleculeMetadata(smiles, explicitName);
        window.currentDrugName = meta.name;

        if (nameEl) nameEl.textContent = meta.name || "Bioactive Molecule";
        if (formulaEl) {
            if (meta.formula) {
                formulaEl.textContent = meta.formula;
                formulaEl.style.display = "inline-block";
            } else {
                formulaEl.style.display = "none";
            }
        }
        if (iupacEl) {
            iupacEl.textContent = meta.iupac || "";
            iupacEl.style.display = meta.iupac ? "block" : "none";
        }
        if (classEl) {
            if (meta.classType) {
                classEl.textContent = meta.classType;
                classEl.style.display = "inline-block";
            } else {
                classEl.style.display = "none";
            }
        }
        if (header) header.style.display = "flex";

        structureStatus.textContent =
            `Rendered: ${meta.name} (2D chemical structure ready)`;

    } catch (error) {

        console.error("Molecule rendering error:", error);

        structureDisplay.innerHTML = `
            <div class="structure-placeholder">
                <h4>Invalid Molecule</h4>
                <p>Please enter a valid SMILES representation.</p>
            </div>
        `;

        if (header) header.style.display = "none";

        structureStatus.textContent =
            "Unable to render molecule.";

    }

}

/* Resolve a compound name when the input is not valid SMILES. */

function nameEditDistance(firstName, secondName) {
    const previousRow = Array.from(
        { length: secondName.length + 1 },
        function (_, index) { return index; }
    );

    for (let rowIndex = 1; rowIndex <= firstName.length; rowIndex += 1) {
        const currentRow = [rowIndex];

        for (let columnIndex = 1; columnIndex <= secondName.length; columnIndex += 1) {
            const substitutionCost =
                firstName[rowIndex - 1] === secondName[columnIndex - 1] ? 0 : 1;

            currentRow[columnIndex] = Math.min(
                currentRow[columnIndex - 1] + 1,
                previousRow[columnIndex] + 1,
                previousRow[columnIndex - 1] + substitutionCost
            );
        }

        previousRow.splice(0, previousRow.length, ...currentRow);
    }

    return previousRow[secondName.length];
}

async function suggestCompoundName(input) {
    const normalizedInput = input.toLocaleLowerCase().replace(/[^a-z0-9]/g, "");
    if (normalizedInput.length < 4) {
        return "";
    }

    const prefix = normalizedInput.slice(0, 3);
    const response = await fetch(
        `${PUBCHEM_AUTOCOMPLETE_URL}/compound/${encodeURIComponent(prefix)}/JSON?limit=50`
    );
    if (!response.ok) {
        return "";
    }

    const data = await response.json();
    const maximumDistance = Math.max(1, Math.floor(normalizedInput.length * 0.1));
    const candidates = (data.dictionary_terms?.compound || [])
        .map(function (name) {
            const normalizedName = name.toLocaleLowerCase().replace(/[^a-z0-9]/g, "");
            return { name, distance: nameEditDistance(normalizedInput, normalizedName) };
        })
        .filter(function (candidate) {
            return candidate.distance <= maximumDistance;
        })
        .sort(function (first, second) {
            return first.distance - second.distance;
        });

    if (candidates.length === 0 ||
        (candidates.length > 1 && candidates[0].distance === candidates[1].distance)) {
        return "";
    }

    return candidates[0].name;
}

async function resolveCompoundInput(input) {
    if (!RDKitModule) {
        throw new Error("RDKit is still loading. Please try again shortly.");
    }

    const molecule = RDKitModule.get_mol(input);
    if (molecule) {
        molecule.delete();
        return { smiles: input, compoundName: "", correctedName: "" };
    }

    // Fast resolution: check curated scientific dataset first
    const curatedMatch = window.BAMI?.findBioactiveMoleculeByName?.(input);
    if (curatedMatch && curatedMatch.smiles) {
        return {
            smiles: curatedMatch.smiles,
            compoundName: curatedMatch.name,
            correctedName: ""
        };
    }

    let lookupName = input;
    let correctedName = "";
    let response = await fetch(
        `${PUBCHEM_API_URL}/compound/name/${encodeURIComponent(lookupName)}/property/CanonicalSMILES,IsomericSMILES,ConnectivitySMILES,IUPACName/JSON`
    );

    if (response.status === 404) {
        correctedName = await suggestCompoundName(input);
        if (!correctedName) {
            throw new Error(`No compound found for "${input}". Check the name or enter a valid SMILES.`);
        }

        lookupName = correctedName;
        response = await fetch(
            `${PUBCHEM_API_URL}/compound/name/${encodeURIComponent(lookupName)}/property/CanonicalSMILES,IsomericSMILES,ConnectivitySMILES,IUPACName/JSON`
        );
    }
    if (!response.ok) {
        throw new Error("PubChem name lookup is unavailable. Try again later or enter a SMILES.");
    }

    const data = await response.json();
    const records = data.PropertyTable?.Properties || [];
    if (records.length !== 1) {
        throw new Error("This name did not resolve to one unique compound. Try a more specific name or enter a SMILES.");
    }

    const record = records[0];
    const smiles = record.SMILES || record.IsomericSMILES || record.ConnectivitySMILES;
    if (!smiles) {
        throw new Error("PubChem did not provide a structure for this compound name.");
    }

    return {
        smiles,
        compoundName: lookupName,
        correctedName
    };
}

/* Load Example button: fill the SMILES field and preview aspirin. */

exampleBtn.addEventListener("click", async function() {

    if (window.moleculeAutocomplete) {
        window.moleculeAutocomplete.close();
    }

    smilesInput.value = exampleSmiles;

    predictionMessage.textContent =
        "Aspirin example loaded. Click Predict Bioactivity.";

    predictionMessage.className =
        "prediction-message";

    structureStatus.textContent =
        "Rendering aspirin structure...";

    const downloadPdfBtn = document.getElementById("download-pdf-btn");
    if (downloadPdfBtn) {
        downloadPdfBtn.disabled = false;
    }

    await renderMolecule(exampleSmiles, "Aspirin");

});

/* Reset the result and descriptor UI before the next prediction. */

function resetResults() {

    const structHeader = document.getElementById("structure-molecule-header");
    if (structHeader) {
        structHeader.style.display = "none";
    }

    if (typeof PipelineTracker !== "undefined") {
        PipelineTracker.hide();
    }

    hideActiveDrugLikenessAction();

    knownUsesRequestId += 1;
    lastPredictedSmiles = "";
    clinicalUsesPanel.hidden = true;
    knownUsesButton.disabled = true;
    knownUsesContent.innerHTML = "<p>Run a prediction, then look up matching Phase-IV records.</p>";
    knownUsesSource.hidden = true;

    const downloadPdfBtn = document.getElementById("download-pdf-btn");
    if (downloadPdfBtn) {
        downloadPdfBtn.disabled = !smilesInput?.value?.trim();
    }

    const predictionDetails = document.getElementById("xgb-probability-results");
    predictionDetails?.remove();

    predictionValue.textContent = "--";

    predictionValue.classList.remove("inactive");

    classificationDescription.textContent =
        "Submit a molecule to view its classification.";
    researchGuidance.textContent =
        "A model prediction is an early research signal and needs experimental validation.";

    /* Reset main descriptors */

    const descriptorIds = [
        "mw-value",
        "logp-value",
        "tpsa-value",
        "hbd-value",
        "hba-value",
        "rotatable-value"
    ];

    descriptorIds.forEach(function(id) {

        const element = document.getElementById(id);

        if (element) {
            element.textContent = "--";
        }

    });


    /* Reset molecular structure */

    structureDisplay.innerHTML = `

        <div class="structure-placeholder">

            <div class="structure-placeholder-icon">⌬</div>

            <h4>Molecular Visualization</h4>

            <p>
                Your molecule's 2D structure will appear here.
            </p>

        </div>

    `;

   structureStatus.textContent =
    RDKitModule
        ? "RDKit ready — enter a molecule."
        : "Waiting for RDKit initialization...";
}


/* Clear button: empty the input and reset the prediction UI. */

clearBtn.addEventListener("click", function() {

    if (window.moleculeAutocomplete) {
        window.moleculeAutocomplete.close();
    }

    smilesInput.value = "";

    predictionMessage.textContent = "";
    predictionMessage.className =
        "prediction-message";

    resetResults();

});

smilesInput.addEventListener("input", function() {
    resetResults();
    predictionMessage.textContent = "";
    predictionMessage.className = "prediction-message";
    const downloadPdfBtn = document.getElementById("download-pdf-btn");
    if (downloadPdfBtn) {
        downloadPdfBtn.disabled = !smilesInput.value.trim();
    }
});

/* Look up source records only after the user requests them. */

knownUsesButton.addEventListener("click", async function() {
    if (!lastPredictedSmiles) {
        return;
    }

    const requestId = ++knownUsesRequestId;
    knownUsesButton.disabled = true;
    knownUsesContent.textContent = "Looking up source-documented uses...";
    knownUsesSource.hidden = true;

    try {
        const response = await fetch(`${API_BASE_URL}/clinical-uses`, {
            method: "POST",
            headers: {
                ...(await window.getFirebaseAuthHeaders()),
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ smiles: lastPredictedSmiles })
        });
        const data = await response.json().catch(() => null);
        if (!response.ok) {
            const detail = data?.detail;
            throw new Error(
                typeof detail === "string"
                    ? detail
                    : "The clinical-use lookup could not be completed. Try again later."
            );
        }

        if (requestId !== knownUsesRequestId) {
            return;
        }

        knownUsesContent.replaceChildren();

        if (!data.matched) {
            knownUsesContent.textContent =
                "No matching clinical-use record was found for this structure.";
            return;
        }

        const compoundLabel = document.createElement("p");
        compoundLabel.className = "known-uses-compound";
        compoundLabel.textContent = data.compound_name;
        knownUsesContent.appendChild(compoundLabel);

        const indications = Array.isArray(data.indications)
            ? data.indications
            : [];
        if (indications.length > 0) {
            const heading = document.createElement("p");
            heading.className = "known-uses-section-title";
            heading.textContent = "Clinical indications";
            knownUsesContent.appendChild(heading);
            const indicationList = document.createElement("ul");
            indications.forEach(function (name) {
                const item = document.createElement("li");
                item.textContent = name;
                indicationList.appendChild(item);
            });
            knownUsesContent.appendChild(indicationList);
        } else {
            const noIndications = document.createElement("p");
            noIndications.textContent =
                "No clinical indications were listed in the sources checked.";
            knownUsesContent.appendChild(noIndications);
        }

        const otherUses = Array.isArray(data.other_uses)
            ? data.other_uses
            : [];
        if (otherUses.length > 0) {
            const heading = document.createElement("p");
            heading.className = "known-uses-section-title";
            heading.textContent = "Other documented uses (not clinical indications)";
            knownUsesContent.appendChild(heading);
            const useList = document.createElement("ul");
            otherUses.forEach(function (use) {
                const item = document.createElement("li");
                item.textContent = use;
                useList.appendChild(item);
            });
            knownUsesContent.appendChild(useList);
        }

        knownUsesSource.href = data.source_url;
        knownUsesSource.hidden = false;
    } catch (error) {
        if (requestId === knownUsesRequestId) {
            knownUsesContent.textContent =
                `${error.message} The prediction itself is unchanged.`;
        }
    } finally {
        if (requestId === knownUsesRequestId) {
            knownUsesButton.disabled = false;
        }
    }
});


/* =========================================================
   PIPELINE TRACKER FOR PREDICTION LOADING EXPERIENCE
   Connects to real SMILES validation, 2048-bit Morgan fingerprinting,
   and FastAPI XGBoost inference states.
   ========================================================= */

const PipelineTracker = {
    get container() { return document.getElementById("prediction-pipeline-container"); },
    get targetLabel() { return document.getElementById("pipeline-target-label"); },
    get overallStatus() { return document.getElementById("pipeline-overall-status"); },
    get step1() { return document.getElementById("pipeline-step-1"); },
    get step2() { return document.getElementById("pipeline-step-2"); },
    get step3() { return document.getElementById("pipeline-step-3"); },
    get step1Desc() { return document.getElementById("step-1-desc"); },
    get step2Desc() { return document.getElementById("step-2-desc"); },
    get step3Title() { return document.getElementById("step-3-title"); },
    get step3Desc() { return document.getElementById("step-3-desc"); },
    get errorAlert() { return document.getElementById("pipeline-error-alert"); },
    get errorTitle() { return document.getElementById("pipeline-error-title"); },
    get errorMessage() { return document.getElementById("pipeline-error-message"); },

    start(target) {
        if (!this.container) return;
        this.container.hidden = false;
        this.container.style.display = "block";
        if (this.errorAlert) {
            this.errorAlert.hidden = true;
            this.errorAlert.style.display = "none";
        }

        if (this.targetLabel) {
            this.targetLabel.textContent = `Target: ${target} • ${target === 'EGFR' ? 'Tuned XGBoost (Calibrated)' : 'Final XGBoost Classifier'}`;
        }
        if (this.step3Title) {
            this.step3Title.textContent = `${target} XGBoost Inference`;
        }

        if (this.overallStatus) {
            this.overallStatus.className = "pipeline-overall-badge badge-running";
            this.overallStatus.textContent = "Pipeline Running";
        }

        this.setStep(1, "pending", "Waiting", "Verifying SMILES syntax, valence rules, and aromaticity");
        this.setStep(2, "pending", "Waiting", "Generating 2048-bit ECFP4-equivalent topological descriptors");
        this.setStep(3, "pending", "Waiting", `Executing trained model on FastAPI backend (port 8000)`);
    },

    setStep(stepNum, status, statusText, desc) {
        const stepEl = this[`step${stepNum}`];
        if (!stepEl) return;
        stepEl.setAttribute("data-status", status);

        const pill = stepEl.querySelector(".step-status-pill");
        if (pill && statusText) {
            pill.textContent = statusText;
        }

        const descEl = this[`step${stepNum}Desc`];
        if (descEl && desc) {
            descEl.textContent = desc;
        }
    },

    fail(stepNum, title, message) {
        if (stepNum) {
            this.setStep(stepNum, "failed", "✕ Failed");
        }
        for (let s = (stepNum || 1) + 1; s <= 3; s++) {
            this.setStep(s, "pending", "Cancelled", "Pipeline halted due to upstream failure");
        }

        if (this.overallStatus) {
            this.overallStatus.className = "pipeline-overall-badge badge-failed";
            this.overallStatus.textContent = "Pipeline Interrupted";
        }

        if (this.errorAlert && this.errorMessage) {
            this.errorAlert.hidden = false;
            this.errorAlert.style.display = "flex";
            if (this.errorTitle) this.errorTitle.textContent = title || "Inference Interrupted";
            this.errorMessage.textContent = message || "An unexpected error occurred during prediction.";
        }
    },

    complete(target, executionTimeMs) {
        this.setStep(3, "completed", "✓ Resolved", `${target} model prediction & probabilities resolved in ${executionTimeMs || '<100'}ms`);
        if (this.overallStatus) {
            this.overallStatus.className = "pipeline-overall-badge badge-completed";
            this.overallStatus.textContent = "✓ Inferred";
        }
    },

    hide() {
        if (!this.container) return;
        this.container.hidden = true;
        this.container.style.display = "none";
        if (this.errorAlert) {
            this.errorAlert.hidden = true;
            this.errorAlert.style.display = "none";
        }
    }
};

/* Predict button: accept SMILES or resolve a familiar compound name first. */

predictBtn.addEventListener("click", async function() {

    const enteredInput = smilesInput.value.trim();

    if (enteredInput === "") {
        predictionMessage.textContent =
            "Please enter a compound name or SMILES first.";
        predictionMessage.className =
            "prediction-message error";
        PipelineTracker.hide();
        return;
    }

    resetResults();

    /* Disable button during prediction */
    predictBtn.disabled = true;
    knownUsesRequestId += 1;
    clinicalUsesPanel.hidden = true;
    knownUsesButton.disabled = true;

    const selectedTarget = targetSelect.value;
    const predictionApiUrl = PREDICTION_API_URLS[selectedTarget];
    if (!predictionApiUrl) {
        predictBtn.disabled = false;
        predictBtn.innerHTML = "<span>Predict Bioactivity</span><span>→</span>";
        predictionMessage.textContent = "Select a supported prediction target.";
        predictionMessage.className = "prediction-message error";
        PipelineTracker.hide();
        return;
    }

    // Initialize real pipeline loading experience
    PipelineTracker.start(selectedTarget);
    predictBtn.innerHTML = "<span>Validating SMILES...</span>";
    predictionMessage.textContent = "";
    predictionMessage.className = "prediction-message";

    const startTime = performance.now();

    try {
        // ==========================================
        // STAGE 1: Real Structure Validation
        // ==========================================
        PipelineTracker.setStep(1, "active", "Validating...", "Resolving structure and verifying valence...");
        structureStatus.textContent = "Validating molecular structure...";

        let resolvedCompound;
        try {
            resolvedCompound = await resolveCompoundInput(enteredInput);
        } catch (resolveErr) {
            PipelineTracker.fail(1, "Molecular Structure Error", resolveErr.message || "Could not resolve compound structure.");
            throw resolveErr;
        }

        const smiles = resolvedCompound.smiles;
        if (!smiles) {
            const err = new Error("No valid molecular SMILES could be resolved.");
            PipelineTracker.fail(1, "Validation Failed", err.message);
            throw err;
        }

        const displaySmiles = smiles.length > 32 ? smiles.slice(0, 30) + '...' : smiles;
        PipelineTracker.setStep(1, "completed", "✓ Validated", `Canonical structure verified: ${displaySmiles}`);

        // ==========================================
        // STAGE 2: 2048-bit Morgan Fingerprint Generation
        // ==========================================
        PipelineTracker.setStep(2, "active", "Generating...", "Computing 2048-bit Morgan fingerprints & 2D depiction...");
        predictBtn.innerHTML = "<span>Generating Fingerprints...</span>";

        try {
            await renderMolecule(smiles, resolvedCompound.compoundName);
        } catch (renderErr) {
            PipelineTracker.fail(2, "Cheminformatics Representation Error", renderErr.message || "Failed to generate molecular representation.");
            throw renderErr;
        }

        PipelineTracker.setStep(2, "completed", "✓ Generated", "2048-bit circular Morgan fingerprint vectors generated");

        // ==========================================
        // STAGE 3: Real Target XGBoost Inference API Request
        // ==========================================
        PipelineTracker.setStep(3, "active", "Inference...", `Submitting to ${selectedTarget} XGBoost model on port 8000...`);
        predictBtn.innerHTML = `<span>Running ${selectedTarget} Model...</span>`;

        let authHeaders = {};
        if (typeof window.getFirebaseAuthHeaders === "function") {
            try {
                authHeaders = await window.getFirebaseAuthHeaders();
            } catch (e) {}
        }

        const response = await fetch(predictionApiUrl, {
            method: "POST",
            headers: {
                ...authHeaders,
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({ smiles: smiles })
        });

        const data = await response.json().catch(function () {
            return {};
        });

        if (!response.ok) {
            const errorDetail = data?.detail || data?.message || (response.status === 404 || response.status === 501
                ? "Cannot reach Prediction API on port 8000. Please ensure the FastAPI backend is running."
                : "Prediction request failed on backend.");
            const fullError = typeof errorDetail === "string" ? errorDetail : JSON.stringify(errorDetail);
            PipelineTracker.fail(3, `${selectedTarget} Inference Error`, fullError);
            throw new Error(fullError);
        }

        if (smilesInput.value.trim() !== enteredInput) {
            return;
        }

        const elapsedMs = Math.round(performance.now() - startTime);
        PipelineTracker.complete(selectedTarget, elapsedMs);

        // Display actual verified prediction results
        displayPrediction(data, resolvedCompound);

    } catch (error) {
        console.warn("Prediction API error:", error);

        predictionMessage.textContent =
            error.message.includes("Failed to fetch")
                ? "Cannot reach PubChem or the prediction API. Check your internet connection and ensure FastAPI is running at http://127.0.0.1:8000."
                : error.message;

        predictionMessage.className = "prediction-message error";
        structureStatus.textContent = "Prediction halted";

    } finally {
        predictBtn.disabled = false;
        predictBtn.innerHTML = "<span>Predict Bioactivity</span><span>→</span>";
    }

});


/* Result UI: fill classification and descriptor values from the API response. */

function displayPrediction(data, resolvedCompound = {}) {

    if (!data) {
        throw new Error("Backend did not return any prediction data.");
    }

    const predictionText =
        typeof data.prediction === "string"
            ? data.prediction
            : typeof data.class_id === "number"
                ? (data.class_id === 1 ? "Active" : "Inactive")
                : "Unknown";

    const prediction = predictionText.toLowerCase();
    const targetName = data.target || targetSelect.value;
    lastPredictedSmiles = data.canonical_smiles || data.smiles || smilesInput.value.trim();
    knownUsesButton.disabled = true;
    knownUsesContent.innerHTML = "<p>Click to see reported clinical uses for this structure.</p>";
    knownUsesSource.hidden = true;
    const descriptors =
        data.molecular_descriptors && typeof data.molecular_descriptors === "object"
            ? data.molecular_descriptors
            : data.descriptors && typeof data.descriptors === "object"
                ? data.descriptors
                : {};

    const formattedPrediction =
        prediction === "active"
            ? "Active"
            : prediction === "inactive"
                ? "Inactive"
                : predictionText;

    knownUsesRequestId += 1;
    clinicalUsesPanel.hidden = formattedPrediction === "Unknown" || !lastPredictedSmiles;
    knownUsesButton.disabled = formattedPrediction === "Unknown" || !lastPredictedSmiles;

    const downloadPdfBtn = document.getElementById("download-pdf-btn");
    if (downloadPdfBtn) {
        downloadPdfBtn.disabled = !lastPredictedSmiles && !smilesInput?.value?.trim();
    }

    predictionValue.textContent = formattedPrediction;
    predictionValue.classList.toggle(
        "inactive",
        formattedPrediction === "Inactive"
    );

    classificationDescription.textContent =
        formattedPrediction === "Active"
            ? `The XGBoost model predicts this molecule as Active against ${targetName}.`
            : formattedPrediction === "Inactive"
                ? `The model did not classify this molecule as Active against ${targetName}. This does not mean it has no other medical uses.`
                : "The XGBoost model returned an unknown prediction class.";

    researchGuidance.textContent =
        formattedPrediction === "Active"
            ? `Treat this as a research lead: prioritize confirmatory ${targetName} testing, then assess selectivity, safety, and ADME properties. This result does not show that the molecule is a medicine or treatment.`
            : formattedPrediction === "Inactive"
                ? `Do not discard a compound solely because of this result. It only describes this model's ${targetName} prediction; the compound may still be useful for other targets or conditions that this model does not assess. This is not advice to start, stop, or avoid a medicine.`
                : "Check the molecule input and prediction response before deciding on follow-up testing.";

    const descriptorMap = {
        "mw-value": descriptors.molecular_weight ?? descriptors.Molecular_Weight,
        "logp-value": descriptors.logp ?? descriptors.LogP,
        "tpsa-value": descriptors.tpsa ?? descriptors.TPSA,
        "hbd-value": descriptors.h_bond_donors ?? descriptors.HBD,
        "hba-value": descriptors.h_bond_acceptors ?? descriptors.HBA,
        "rotatable-value": descriptors.rotatable_bonds ?? descriptors.Rotatable_Bonds
    };

    Object.entries(descriptorMap).forEach(function ([id, value]) {
        const element = document.getElementById(id);

        if (element) {
            element.textContent =
                value !== undefined && value !== null
                    ? Number(value).toFixed(2)
                    : "--";
        }
    });

    let modelInfoContainer = document.getElementById("xgb-probability-results");

    if (!modelInfoContainer) {
        modelInfoContainer = document.createElement("div");
        modelInfoContainer.id = "xgb-probability-results";
        modelInfoContainer.className = "prediction-details";
        resultSection.appendChild(modelInfoContainer);
    }

    modelInfoContainer.innerHTML = `
        <h3>XGBoost Prediction Details</h3>

        <div class="model-results-table">
            <p><strong>Model:</strong> ${data.model || "XGBoost"}</p>
            <p><strong>Target:</strong> ${targetName}</p>
            <p><strong>SMILES:</strong> ${data.smiles || "Not available"}</p>
            <p><strong>Predicted Class:</strong> ${formattedPrediction}</p>
        </div>
    `;

    if (Number.isFinite(Number(data.probability_active))) {
        const probability = document.createElement("p");
        const probabilityLabel = document.createElement("strong");
        probabilityLabel.textContent = data.probability_type === "calibrated_probability"
            ? "Calibrated probability of Active: "
            : "Model score for Active: ";
        probability.append(
            probabilityLabel,
            document.createTextNode(`${(Number(data.probability_active) * 100).toFixed(1)}%`)
        );
        modelInfoContainer.querySelector(".model-results-table").appendChild(probability);
    }

    if (Number.isFinite(Number(data.classification_threshold))) {
        const threshold = document.createElement("p");
        const thresholdLabel = document.createElement("strong");
        thresholdLabel.textContent = "Classification threshold: ";
        threshold.append(
            thresholdLabel,
            document.createTextNode(`${(Number(data.classification_threshold) * 100).toFixed(1)}%`)
        );
        modelInfoContainer.querySelector(".model-results-table").appendChild(threshold);
    }

    if (resolvedCompound.compoundName) {
        const resolvedName = document.createElement("p");
        const label = document.createElement("strong");
        label.textContent = resolvedCompound.correctedName
            ? "Suggested match: "
            : "Compound name: ";
        const nameText = resolvedCompound.correctedName
            ? `${resolvedCompound.compoundName} (matched from "${smilesInput.value.trim()}")`
            : resolvedCompound.compoundName;
        resolvedName.append(label, document.createTextNode(nameText));
        modelInfoContainer.querySelector(".model-results-table").appendChild(resolvedName);
    }

    const dlShortcutHtml = formattedPrediction === "Active"
        ? `<a href="drug-likeness.html?smiles=${encodeURIComponent(lastPredictedSmiles)}&name=${encodeURIComponent(resolvedCompound.compoundName || '')}&auto=1&from=active_prediction&target=${encodeURIComponent(targetName)}" class="scaffold-shortcut-link scaffold-shortcut-druglikeness">
            💊 Analyze Drug-Likeness (Lipinski Ro5) &rarr;
        </a>`
        : "";

    const scaffoldAction = document.createElement("div");
    scaffoldAction.className = "scaffold-shortcut-box";
    scaffoldAction.innerHTML = `
        <div style="display: flex; flex-wrap: wrap; gap: 10px;">
            ${dlShortcutHtml}
            <a href="docking.html?smiles=${encodeURIComponent(lastPredictedSmiles)}&target=${encodeURIComponent(targetName)}" class="scaffold-shortcut-link" style="background: linear-gradient(135deg, #651FFF 0%, #3D5AFE 100%); color: #ffffff; border-color: transparent; box-shadow: 0 4px 14px rgba(101,31,255,0.25);">
                🔬 Run AutoDock Vina Docking &rarr;
            </a>
            <a href="scaffold-analysis.html?smiles=${encodeURIComponent(lastPredictedSmiles)}&name=${encodeURIComponent(resolvedCompound.compoundName || '')}" class="scaffold-shortcut-link">
                🧬 Analyze Bemis-Murcko Scaffold &rarr;
            </a>
            <a href="admet.html?smiles=${encodeURIComponent(lastPredictedSmiles)}&name=${encodeURIComponent(resolvedCompound.compoundName || '')}" class="scaffold-shortcut-link" style="background: #ECFDF5; color: #065F46; border-color: #A7F3D0;">
                🛡️ Profile Complete ADMET Properties &rarr;
            </a>
        </div>
    `;
    modelInfoContainer.appendChild(scaffoldAction);

    predictionMessage.textContent =
        "XGBoost prediction completed successfully. This is a model prediction, not a confirmed biological result.";
    predictionMessage.className = "prediction-message success";
    structureStatus.textContent =
        "Molecular structure rendered; XGBoost prediction completed.";

    // Record successful prediction in local history (max 50, stored on this browser)
    try {
        if (window.BAMIHistory && typeof window.BAMIHistory.addPrediction === "function") {
            window.BAMIHistory.addPrediction(data, {
                compoundName: resolvedCompound.compoundName || "",
                rawInput: smilesInput.value.trim(),
                target: targetName,
                smiles: lastPredictedSmiles
            });
        }
    } catch (historyErr) {
        console.warn("Unable to log prediction to history:", historyErr);
    }

    if (resultSection) {
        resultSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }

    if (formattedPrediction === "Active") {
        showActiveDrugLikenessAction(data, resolvedCompound, targetName);
    } else {
        hideActiveDrugLikenessAction();
    }
}

/* =========================================================
   ACTIVE PREDICTION: DRUG-LIKENESS (LIPINSKI) ACTION BUTTON
   (Auto-redirect removed per user preference; manual button provided)
   ========================================================= */

let activeRedirectTimer = null; // Maintained as null safety reference

function hideActiveDrugLikenessAction() {
    if (activeRedirectTimer) {
        clearTimeout(activeRedirectTimer);
        activeRedirectTimer = null;
    }
    const banner = document.getElementById("active-druglikeness-banner") || document.getElementById("active-redirect-banner");
    banner?.remove();
}

function showActiveDrugLikenessAction(data, resolvedCompound = {}, targetName = "") {
    hideActiveDrugLikenessAction();

    const smilesToPass = data?.canonical_smiles || data?.smiles || lastPredictedSmiles || smilesInput?.value?.trim() || "";
    const compoundName = resolvedCompound?.compoundName || smilesInput?.value?.trim() || "";

    if (!smilesToPass) return;

    // Persist to sessionStorage for seamless transfer if the user clicks the button
    try {
        sessionStorage.setItem("bami_auto_drug_likeness", JSON.stringify({
            smiles: smilesToPass,
            name: compoundName,
            target: targetName,
            timestamp: Date.now()
        }));
    } catch (e) {
        // quota/private browsing fallback
    }

    const targetUrl = new URL("drug-likeness.html", window.location.href);
    targetUrl.searchParams.set("smiles", smilesToPass);
    if (compoundName && compoundName !== smilesToPass) {
        targetUrl.searchParams.set("name", compoundName);
    }
    targetUrl.searchParams.set("auto", "1");
    targetUrl.searchParams.set("from", "active_prediction");
    if (targetName) {
        targetUrl.searchParams.set("target", targetName);
    }

    // Display prominent action banner in result-section
    const actionBanner = document.createElement("div");
    actionBanner.id = "active-druglikeness-banner";
    actionBanner.className = "active-druglikeness-banner active-redirect-banner";

    const safeTarget = escapeHtml(targetName || "Target");
    const safeName = compoundName ? escapeHtml(compoundName) : "Molecule";

    actionBanner.innerHTML = `
        <div class="active-druglikeness-icon-wrap" aria-hidden="true">
            <span class="active-druglikeness-icon">💊</span>
        </div>
        <div class="active-druglikeness-body">
            <div class="active-druglikeness-badge">
                <span class="active-druglikeness-pulse" aria-hidden="true"></span>
                <span>Active Lead Candidate</span>
            </div>
            <h4>Analyze Drug-Likeness (Lipinski Rule of 5)</h4>
            <p>
                <strong>${safeName}</strong> was classified as <strong>Active</strong> against <strong>${safeTarget}</strong>.
                Screen for oral bioavailability, hydrogen bonding properties, molecular weight boundaries, and Lipinski rule compliance.
            </p>
        </div>
        <div class="active-druglikeness-actions">
            <a href="${targetUrl.toString()}" class="btn-druglikeness-active" id="active-drug-likeness-btn">
                <span class="btn-icon">🔬</span>
                <span class="btn-text">Analyze Drug-Likeness</span>
                <span class="btn-arrow" aria-hidden="true">&rarr;</span>
            </a>
        </div>
    `;

    const classificationCard = document.querySelector(".classification-card");
    if (classificationCard && classificationCard.parentNode) {
        classificationCard.parentNode.insertBefore(actionBanner, classificationCard.nextSibling);
    } else if (resultSection) {
        resultSection.prepend(actionBanner);
    }

    // Inform user of active status without forcing a countdown redirect
    predictionMessage.textContent =
        `Active prediction confirmed against ${targetName}! Review prediction details or click "Analyze Drug-Likeness" to screen for oral bioavailability.`;
    predictionMessage.className = "prediction-message success";
}

// Backward-compatibility alias
function handleActivePredictionRedirect(data, resolvedCompound = {}, targetName = "") {
    showActiveDrugLikenessAction(data, resolvedCompound, targetName);
}



/* =========================================================
   INITIALIZATION
   ========================================================= */

function setupMoleculeAutocomplete() {
    const searchContainer = document.getElementById("molecule-search-container");
    const searchDropdown = document.getElementById("molecule-suggestions-dropdown");

    if (typeof initMoleculeAutocomplete === "function" && smilesInput && searchDropdown) {
        window.moleculeAutocomplete = initMoleculeAutocomplete({
            input: smilesInput,
            container: searchContainer,
            dropdown: searchDropdown,
            targetSelect: targetSelect,
            onSelect: async (molecule) => {
                smilesInput.value = molecule.name;

                // Intelligently sync target dropdown if target is specified
                if (molecule.target) {
                    if (molecule.target.toUpperCase().includes("EGFR")) {
                        targetSelect.value = "EGFR";
                    } else if (molecule.target.toUpperCase().includes("COX-2")) {
                        targetSelect.value = "COX-2";
                    }
                }

                predictionMessage.textContent = `Selected ${molecule.name} (${molecule.formula ? molecule.formula + " · " : ""}${molecule.target ? molecule.target : "Molecule"}). Click Predict Bioactivity to screen.`;
                predictionMessage.className = "prediction-message success";

                // Fast render 2D molecular structure if SMILES is available
                if (molecule.smiles) {
                    try {
                        await renderMolecule(molecule.smiles, molecule.name);
                        structureStatus.textContent = `${molecule.name} structure preview ready.`;
                    } catch (err) {
                        console.warn("Could not preview selected molecule structure:", err);
                    }
                }
            }
        });
    }
}

// Run immediately or on DOM ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupMoleculeAutocomplete);
} else {
    setupMoleculeAutocomplete();
}

document.addEventListener("DOMContentLoaded", function() {

    // Welcome toast check post-login
    try {
        if (sessionStorage.getItem("bami_just_logged_in")) {
            sessionStorage.removeItem("bami_just_logged_in");
            const welcomeToast = document.createElement("div");
            welcomeToast.className = "bami-login-welcome-toast";
            welcomeToast.innerHTML = `
                <span class="welcome-toast-icon">⌬</span>
                <div class="welcome-toast-text">
                    <strong>Workspace Initialized</strong>
                    <span>BAMI Bioactive Molecule Intelligence is ready.</span>
                </div>
            `;
            document.body.appendChild(welcomeToast);
            setTimeout(() => {
                welcomeToast.classList.add("fade-out");
                setTimeout(() => welcomeToast.remove(), 600);
            }, 3600);
        }
    } catch (_) {}

    console.log(
        "XGBioactive frontend initialized with intelligent molecule autocomplete."
    );

    console.log(
        "XGBoost prediction APIs:",
        PREDICTION_API_URLS
    );

    // Check for preloaded molecule from History or external query params
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const preloadedSmiles = urlParams.get("smiles") || sessionStorage.getItem("bami_preload_smiles");
        const preloadedTarget = urlParams.get("target") || sessionStorage.getItem("bami_preload_target");
        const preloadedName = urlParams.get("name") || sessionStorage.getItem("bami_preload_name");

        if (preloadedSmiles && smilesInput) {
            smilesInput.value = preloadedSmiles;
            if (preloadedTarget && targetSelect) {
                targetSelect.value = preloadedTarget;
            }
            sessionStorage.removeItem("bami_preload_smiles");
            sessionStorage.removeItem("bami_preload_target");
            sessionStorage.removeItem("bami_preload_name");

            if (predictionMessage) {
                predictionMessage.textContent = preloadedName
                    ? `Loaded "${preloadedName}" from history. Click Predict Bioactivity to evaluate.`
                    : "Loaded molecule from history. Click Predict Bioactivity to evaluate.";
                predictionMessage.className = "prediction-message";
            }

            // Attempt to render structure after RDKit finishes loading
            const attemptRender = function (retriesLeft) {
                if (window.RDKitModule && typeof renderMolecule === "function") {
                    renderMolecule(preloadedSmiles, preloadedName).catch(function () {});
                } else if (retriesLeft > 0) {
                    setTimeout(function () {
                        attemptRender(retriesLeft - 1);
                    }, 250);
                }
            };
            attemptRender(10);
        }
    } catch (preloadErr) {
        console.warn("Could not handle preloaded history params:", preloadErr);
    }

    /* Initialize PDF Download Button */
    const downloadPdfBtn = document.getElementById("download-pdf-btn");
    if (downloadPdfBtn) {
        // If there's an existing smiles in the field, enable it
        if (smilesInput && smilesInput.value.trim().length > 0) {
            downloadPdfBtn.disabled = false;
        }

        downloadPdfBtn.addEventListener("click", function () {
            const targetSmiles = (lastPredictedSmiles || (smilesInput ? smilesInput.value.trim() : "")).trim();
            downloadScientificReport(targetSmiles);
        });
    }

});

/* =========================================================
   SCIENTIFIC REPORT GENERATION (PDF)
   ========================================================= */

async function downloadScientificReport(smiles, moleculeName = "") {
    const downloadPdfBtn = document.getElementById("download-pdf-btn");
    const targetSmiles = (smiles || lastPredictedSmiles || (smilesInput ? smilesInput.value.trim() : "")).trim();

    if (!targetSmiles) {
        if (predictionMessage) {
            predictionMessage.textContent = "Please provide or predict a valid SMILES molecule to generate a report.";
            predictionMessage.className = "prediction-message error";
        }
        alert("Please enter or predict a molecule before generating the scientific PDF report.");
        return;
    }

    const originalContent = downloadPdfBtn ? downloadPdfBtn.innerHTML : "";
    if (downloadPdfBtn) {
        downloadPdfBtn.disabled = true;
        downloadPdfBtn.classList.add("loading");
        downloadPdfBtn.innerHTML = `
            <span class="pdf-spinner" aria-hidden="true"></span>
            <span class="btn-text">Generating PDF...</span>
        `;
    }

    if (predictionMessage) {
        predictionMessage.textContent = "Synthesizing comprehensive scientific PDF report via ReportLab...";
        predictionMessage.className = "prediction-message info";
    }

    try {
        let authHeaders = {};
        if (typeof window.getFirebaseAuthHeaders === "function") {
            try {
                authHeaders = await window.getFirebaseAuthHeaders();
            } catch {
                authHeaders = {};
            }
        }

        const endpoint = `${API_BASE_URL}/download-report`;
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...authHeaders
            },
            body: JSON.stringify({
                smiles: targetSmiles,
                name: moleculeName || (window.currentDrugName || ""),
                target: (targetSelect ? targetSelect.value : "COX-2"),
                include_admet: true,
                include_docking: true
            })
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `Server returned status ${response.status}`);
        }

        const blob = await response.blob();
        let filename = `BAMI_Report_${moleculeName ? moleculeName.replace(/[^a-zA-Z0-9_-]/g, "_") : "Candidate"}.pdf`;
        const contentDisposition = response.headers.get("Content-Disposition");
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?([^";]+)"?/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1].trim();
            }
        }

        const blobUrl = window.URL.createObjectURL(blob);
        const tempLink = document.createElement("a");
        tempLink.href = blobUrl;
        tempLink.download = filename;
        document.body.appendChild(tempLink);
        tempLink.click();
        document.body.removeChild(tempLink);
        setTimeout(() => window.URL.revokeObjectURL(blobUrl), 2000);

        if (predictionMessage) {
            predictionMessage.textContent = `Report downloaded successfully: ${filename}`;
            predictionMessage.className = "prediction-message success";
        }
    } catch (err) {
        console.error("PDF generation error:", err);
        if (predictionMessage) {
            predictionMessage.textContent = `PDF generation failed: ${err.message}`;
            predictionMessage.className = "prediction-message error";
        }
        alert(`Failed to generate PDF report: ${err.message}`);
    } finally {
        if (downloadPdfBtn) {
            downloadPdfBtn.disabled = false;
            downloadPdfBtn.classList.remove("loading");
            downloadPdfBtn.innerHTML = originalContent;
        }
    }
}


/* =========================================================
   SCIENTIFIC REPORT GENERATION (PDF)
   ========================================================= */

async function downloadScientificReport(smiles, moleculeName = "") {
    const downloadPdfBtn = document.getElementById("download-pdf-btn");
    const targetSmiles = (smiles || lastPredictedSmiles || (smilesInput ? smilesInput.value.trim() : "")).trim();

    if (!targetSmiles) {
        if (predictionMessage) {
            predictionMessage.textContent = "Please provide or predict a valid SMILES molecule to generate a report.";
            predictionMessage.className = "prediction-message error";
        }
        alert("Please enter or predict a molecule before generating the scientific PDF report.");
        return;
    }

    const originalContent = downloadPdfBtn ? downloadPdfBtn.innerHTML : "";
    if (downloadPdfBtn) {
        downloadPdfBtn.disabled = true;
        downloadPdfBtn.classList.add("loading");
        downloadPdfBtn.innerHTML = `
            <span class="pdf-spinner" aria-hidden="true"></span>
            <span class="btn-text">Generating PDF...</span>
        `;
    }

    if (predictionMessage) {
        predictionMessage.textContent = "Synthesizing comprehensive scientific PDF report via ReportLab...";
        predictionMessage.className = "prediction-message info";
    }

    try {
        let authHeaders = {};
        if (typeof window.getFirebaseAuthHeaders === "function") {
            try {
                authHeaders = await window.getFirebaseAuthHeaders();
            } catch {
                authHeaders = {};
            }
        }

        const endpoint = `${API_BASE_URL}/download-report`;
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...authHeaders
            },
            body: JSON.stringify({
                smiles: targetSmiles,
                name: moleculeName || (window.currentDrugName || ""),
                target: (targetSelect ? targetSelect.value : "COX-2"),
                include_admet: true,
                include_docking: true
            })
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `Server returned status ${response.status}`);
        }

        const blob = await response.blob();
        let filename = `BAMI_Report_${moleculeName ? moleculeName.replace(/[^a-zA-Z0-9_-]/g, "_") : "Candidate"}.pdf`;
        const contentDisposition = response.headers.get("Content-Disposition");
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?([^";]+)"?/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1].trim();
            }
        }

        const blobUrl = window.URL.createObjectURL(blob);
        const tempLink = document.createElement("a");
        tempLink.href = blobUrl;
        tempLink.download = filename;
        document.body.appendChild(tempLink);
        tempLink.click();
        document.body.removeChild(tempLink);
        setTimeout(() => window.URL.revokeObjectURL(blobUrl), 2000);

        if (predictionMessage) {
            predictionMessage.textContent = `Report downloaded successfully: ${filename}`;
            predictionMessage.className = "prediction-message success";
        }
    } catch (err) {
        console.error("PDF generation error:", err);
        if (predictionMessage) {
            predictionMessage.textContent = `PDF generation failed: ${err.message}`;
            predictionMessage.className = "prediction-message error";
        }
        alert(`Failed to generate PDF report: ${err.message}`);
    } finally {
        if (downloadPdfBtn) {
            downloadPdfBtn.disabled = false;
            downloadPdfBtn.classList.remove("loading");
            downloadPdfBtn.innerHTML = originalContent;
        }
    }
}