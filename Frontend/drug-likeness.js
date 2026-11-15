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

const ruleLabels = {
    molecular_weight: "Molecular Weight ≤ 500 g/mol",
    logp: "LogP ≤ 5",
    hydrogen_bond_donors: "Hydrogen-bond donors ≤ 5",
    hydrogen_bond_acceptors: "Hydrogen-bond acceptors ≤ 10"
};

/* =========================================================
    ERROR AND RESULT RENDERING
   ========================================================= */

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.hidden = false;
    statusMessage.textContent = "";
    resultsSection.hidden = true;
}

function displayResults(data) {
    const descriptors = data.descriptors;

    document.getElementById("drug-mw").textContent =
        Number(descriptors.Molecular_Weight).toFixed(2);
    document.getElementById("drug-logp").textContent =
        Number(descriptors.LogP).toFixed(2);
    document.getElementById("drug-hbd").textContent = descriptors.HBD;
    document.getElementById("drug-hba").textContent = descriptors.HBA;
    document.getElementById("drug-tpsa").textContent =
        Number(descriptors.TPSA).toFixed(2);
    document.getElementById("drug-rotatable").textContent =
        descriptors.Rotatable_Bonds;

    const lipinski = data.lipinski;
    const overall = document.getElementById("lipinski-overall");
    overall.textContent = lipinski.passed
        ? `PASS · ${lipinski.violations} rule violations`
        : `FAIL · ${lipinski.violations} rule violation${lipinski.violations === 1 ? "" : "s"}`;
    overall.className = `lipinski-overall ${lipinski.passed ? "status-pass" : "status-fail"}`;

    const rulesList = document.getElementById("lipinski-rules");
    rulesList.replaceChildren();
    Object.entries(lipinski.rules).forEach(([ruleName, rule]) => {
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

    errorMessage.hidden = true;
    resultsSection.hidden = false;
}

/* =========================================================
    BACKEND AND PUBCHEM REQUESTS
   ========================================================= */

async function requestAnalysis(smiles) {
    const response = await fetch(DRUG_LIKENESS_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ smiles })
    });
    const data = await response.json().catch(() => null);
    return { response, data };
}

async function resolveMoleculeName(name) {
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
        let resolvedName = "";

        if (response.status === 422) {
            statusMessage.textContent = "Looking up molecule name through PubChem…";
            const resolvedSmiles = await resolveMoleculeName(input);
            resolvedName = input;
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

        displayResults(data);
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
