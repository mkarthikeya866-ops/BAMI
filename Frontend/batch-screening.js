/* =========================================================
   BATCH MOLECULE SCREENING
   ========================================================= */

const batchHost = window.location.hostname || "127.0.0.1";
const batchApiBaseUrl = ["localhost", "127.0.0.1"].includes(batchHost)
    ? `http://${batchHost}:8000/api/v1`
    : "/api/v1";
const batchApiUrl = `${batchApiBaseUrl}/batch-predict`;
const batchSmilesInput = document.getElementById("batch-smiles-input");
const batchTargetSelect = document.getElementById("batch-target-select");
const batchCsvFile = document.getElementById("batch-csv-file");
const batchScreenButton = document.getElementById("batch-screen-btn");
const batchClearButton = document.getElementById("batch-clear-btn");
const batchDownloadButton = document.getElementById("batch-download-btn");
const batchMessage = document.getElementById("batch-message");
const batchLoading = document.getElementById("batch-loading");
const batchResultsSection = document.getElementById("batch-results");
const batchResultsBody = document.getElementById("batch-results-body");
const batchCountElements = {
    total: document.getElementById("batch-total-count"),
    valid: document.getElementById("batch-valid-count"),
    invalid: document.getElementById("batch-invalid-count"),
    active: document.getElementById("batch-active-count"),
    inactive: document.getElementById("batch-inactive-count")
};

let batchResults = [];
let batchResultTarget = "";
let csvLoadedSmiles = null;
let csvLoadedText = "";

/* CSV parsing supports quoted cells, escaped quotes, and embedded newlines. */

function parseCsvRows(csvText) {
    const text = csvText.replace(/^\uFEFF/, "");
    const rows = [];
    let row = [];
    let field = "";
    let insideQuotes = false;

    for (let index = 0; index < text.length; index += 1) {
        const character = text[index];

        if (insideQuotes) {
            if (character === '"') {
                if (text[index + 1] === '"') {
                    field += '"';
                    index += 1;
                } else {
                    insideQuotes = false;
                }
            } else {
                field += character;
            }
            continue;
        }

        if (character === '"' && field.length === 0) {
            insideQuotes = true;
        } else if (character === ",") {
            row.push(field);
            field = "";
        } else if (character === "\n" || character === "\r") {
            if (character === "\r" && text[index + 1] === "\n") {
                index += 1;
            }
            row.push(field);
            rows.push(row);
            row = [];
            field = "";
        } else {
            field += character;
        }
    }

    if (insideQuotes) {
        throw new Error("The CSV contains an unterminated quoted field.");
    }
    if (field.length > 0 || row.length > 0) {
        row.push(field);
        rows.push(row);
    }

    return rows;
}

function readSmilesFromCsv(csvText) {
    const rows = parseCsvRows(csvText);
    if (rows.length === 0) {
        throw new Error("The CSV file is empty.");
    }

    const smilesColumn = rows[0].findIndex(function (heading) {
        return heading.trim().toLocaleLowerCase() === "smiles";
    });
    if (smilesColumn < 0) {
        throw new Error('The CSV must contain a column named "SMILES".');
    }

    return rows.slice(1)
        .filter(function (row) {
            return row.some(function (cell) { return cell.trim() !== ""; });
        })
        .map(function (row) {
            return (row[smilesColumn] || "").trim();
        });
}

function setBatchMessage(message, kind = "") {
    batchMessage.textContent = message;
    batchMessage.className = `batch-message${kind ? ` ${kind}` : ""}`;
}

function clearBatchResults(clearInput = false) {
    batchResults = [];
    batchResultTarget = "";
    csvLoadedSmiles = null;
    csvLoadedText = "";
    batchResultsBody.replaceChildren();
    batchResultsSection.hidden = true;
    batchDownloadButton.disabled = true;
    if (clearInput) {
        batchSmilesInput.value = "";
        batchCsvFile.value = "";
    }
    setBatchMessage("");
}

function predictionTargets(target) {
    return target === "Both" ? ["COX-2", "EGFR"] : [target];
}

function formatProbability(probability) {
    if (typeof probability !== "number" || !Number.isFinite(probability)) {
        return "Unavailable";
    }
    return `${(probability * 100).toFixed(2)}%`;
}

function appendTargetValues(cell, result, targets, valueForTarget) {
    targets.forEach(function (target) {
        const line = document.createElement("span");
        line.className = "batch-target-result";
        const targetResult = result.predictions?.[target];
        const value = valueForTarget(targetResult);
        line.textContent = targets.length > 1 ? `${target}: ${value}` : value;
        cell.append(line);
    });
}

function renderBatchResults(data) {
    const targets = predictionTargets(data.target);
    const fragment = document.createDocumentFragment();
    let activeCount = 0;
    let inactiveCount = 0;

    data.results.forEach(function (result) {
        const row = document.createElement("tr");
        const indexCell = document.createElement("td");
        indexCell.textContent = String(result.index);
        row.append(indexCell);

        const smilesCell = document.createElement("td");
        smilesCell.textContent = result.smiles;
        row.append(smilesCell);

        const predictionCell = document.createElement("td");
        appendTargetValues(predictionCell, result, targets, function (targetResult) {
            return targetResult?.prediction || "Unavailable";
        });
        row.append(predictionCell);

        const probabilityCell = document.createElement("td");
        appendTargetValues(probabilityCell, result, targets, function (targetResult) {
            const probability = formatProbability(targetResult?.probability);
            const probabilityType = targetResult?.probability_type;
            return probabilityType && probability !== "Unavailable"
                ? `${probability} (${probabilityType.replaceAll("_", " ")})`
                : probability;
        });
        row.append(probabilityCell);

        const validationCell = document.createElement("td");
        validationCell.textContent = result.validation_status;
        validationCell.className = result.validation_status === "valid"
            ? "batch-validation-valid"
            : "batch-validation-invalid";
        row.append(validationCell);

        const errorCell = document.createElement("td");
        errorCell.textContent = result.error_message || "";
        row.append(errorCell);

        fragment.append(row);

        if (result.validation_status !== "valid") {
            return;
        }
        const predictions = targets.map(function (target) {
            return result.predictions?.[target]?.prediction;
        });
        if (predictions.some(function (prediction) { return prediction === "Active"; })) {
            activeCount += 1;
        } else if (predictions.length > 0 &&
            predictions.every(function (prediction) { return prediction === "Inactive"; })) {
            inactiveCount += 1;
        }
    });

    batchResultsBody.replaceChildren(fragment);
    batchCountElements.total.textContent = String(data.total);
    batchCountElements.valid.textContent = String(data.valid);
    batchCountElements.invalid.textContent = String(data.invalid);
    batchCountElements.active.textContent = String(activeCount);
    batchCountElements.inactive.textContent = String(inactiveCount);
    batchResultsSection.hidden = false;
}

function getCsvValue(value) {
    let text = value === null || value === undefined ? "" : String(value);
    if (/^[\t\r ]*[=+\-@]/.test(text)) {
        text = `'${text}`;
    }
    return `"${text.replaceAll('"', '""')}"`;
}

function buildResultsCsv() {
    const headings = [
        "Molecule Index",
        "SMILES",
        "Validation Status",
        "Error Message",
        "COX-2 Prediction",
        "COX-2 Probability",
        "EGFR Prediction",
        "EGFR Probability"
    ];
    const rows = batchResults.map(function (result) {
        const cox2 = result.predictions?.["COX-2"] || {};
        const egfr = result.predictions?.EGFR || {};
        return [
            result.index,
            result.smiles,
            result.validation_status,
            result.error_message,
            cox2.prediction,
            cox2.probability,
            egfr.prediction,
            egfr.probability
        ];
    });
    return `\uFEFF${[headings, ...rows]
        .map(function (row) { return row.map(getCsvValue).join(","); })
        .join("\r\n")}\r\n`;
}

/* Read an uploaded CSV, validate its header, and populate the SMILES input. */

batchCsvFile.addEventListener("change", async function () {
    const file = batchCsvFile.files?.[0];
    if (!file) {
        return;
    }

    clearBatchResults();
    batchSmilesInput.value = "";
    if (!file.name.toLocaleLowerCase().endsWith(".csv")) {
        setBatchMessage("Choose a .csv file.", "error");
        batchCsvFile.value = "";
        return;
    }

    try {
        const smiles = readSmilesFromCsv(await file.text());
        if (smiles.length === 0) {
            throw new Error("The CSV contains no molecule rows.");
        }
        if (smiles.length > 500) {
            throw new Error("The CSV contains more than the 500-molecule limit.");
        }
        csvLoadedSmiles = smiles;
        batchSmilesInput.value = smiles.join("\n");
        csvLoadedText = batchSmilesInput.value;
        setBatchMessage(`Loaded ${smiles.length} molecule row(s) from ${file.name}.`);
    } catch (error) {
        setBatchMessage(error.message || "Could not read the CSV file.", "error");
        batchCsvFile.value = "";
    }
});

batchSmilesInput.addEventListener("input", function () {
    if (csvLoadedSmiles !== null && batchSmilesInput.value !== csvLoadedText) {
        csvLoadedSmiles = null;
        csvLoadedText = "";
        batchCsvFile.value = "";
    }
    batchResults = [];
    batchResultTarget = "";
    batchResultsBody.replaceChildren();
    batchResultsSection.hidden = true;
    batchDownloadButton.disabled = true;
    setBatchMessage("");
});

batchTargetSelect.addEventListener("change", function () {
    batchResults = [];
    batchResultTarget = "";
    batchResultsBody.replaceChildren();
    batchResultsSection.hidden = true;
    batchDownloadButton.disabled = true;
    setBatchMessage("");
});

/* Submit the batch and display each molecule's independent result. */

batchScreenButton.addEventListener("click", async function () {
    const smiles = csvLoadedSmiles !== null &&
        batchSmilesInput.value === csvLoadedText
        ? csvLoadedSmiles
        : batchSmilesInput.value.split(/\r?\n/)
            .map(function (value) { return value.trim(); })
            .filter(function (value) { return value !== ""; });

    if (smiles.length === 0) {
        setBatchMessage("Paste at least one SMILES or upload a CSV file.", "error");
        return;
    }
    if (smiles.length > 500) {
        setBatchMessage("A batch can contain at most 500 molecules.", "error");
        return;
    }

    batchScreenButton.disabled = true;
    batchClearButton.disabled = true;
    batchDownloadButton.disabled = true;
    batchSmilesInput.disabled = true;
    batchTargetSelect.disabled = true;
    batchCsvFile.disabled = true;
    batchLoading.hidden = false;
    batchResultsSection.hidden = true;
    batchResults = [];
    batchResultTarget = "";
    setBatchMessage("");

    try {
        const response = await fetch(batchApiUrl, {
            method: "POST",
            headers: {
                ...(await window.getFirebaseAuthHeaders()),
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({
                target: batchTargetSelect.value,
                smiles: smiles
            })
        });
        const data = await response.json().catch(function () { return {}; });
        if (!response.ok) {
            const detail = typeof data.detail === "string"
                ? data.detail
                : JSON.stringify(data.detail || "Batch prediction request failed.");
            throw new Error(detail);
        }
        if (!Array.isArray(data.results) || data.total !== data.results.length) {
            throw new Error("The batch API returned an incomplete result.");
        }

        batchResults = data.results;
        batchResultTarget = data.target;
        renderBatchResults(data);
        batchDownloadButton.disabled = batchResults.length === 0;
        setBatchMessage(
            `Screening complete: ${data.total} molecule(s) processed.`,
            "success"
        );
    } catch (error) {
        setBatchMessage(
            error.message.includes("Failed to fetch")
                ? "Cannot reach the prediction API. Ensure FastAPI is running at http://127.0.0.1:8000."
                : error.message,
            "error"
        );
    } finally {
        batchScreenButton.disabled = false;
        batchClearButton.disabled = false;
        batchSmilesInput.disabled = false;
        batchTargetSelect.disabled = false;
        batchCsvFile.disabled = false;
        batchLoading.hidden = true;
    }
});

/* Download the displayed API results as an Excel-friendly CSV file. */

batchDownloadButton.addEventListener("click", function () {
    if (batchResults.length === 0) {
        setBatchMessage("Run a batch before downloading results.", "error");
        return;
    }

    const blob = new Blob([buildResultsCsv()], {
        type: "text/csv;charset=utf-8"
    });
    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = `bioactive-batch-${batchResultTarget.toLocaleLowerCase().replaceAll(/[^a-z0-9]+/g, "-")}.csv`;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(function () {
        URL.revokeObjectURL(downloadUrl);
    }, 1000);
});

batchClearButton.addEventListener("click", function () {
    clearBatchResults(true);
});
