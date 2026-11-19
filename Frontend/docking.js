/**
 * BAMI Molecular Docking Simulation Client
 * ========================================
 * Connects to FastAPI backend and AutoDock Vina v1.2.7
 * Renders 3D protein-ligand complex with 3Dmol.js
 */

(function () {
    "use strict";

    // Dynamic API Base Configuration (connects to FastAPI backend across Localhost, LAN, and Cloud)
    const localHosts = new Set(["localhost", "127.0.0.1"]);
    const currentHost = window.location.hostname || "127.0.0.1";
    const isLocal = localHosts.has(currentHost);

    // Support custom backend URL via query param ?api=..., window.BAMI_API_URL, or localStorage
    const urlParams = (typeof window !== "undefined" && window.location.search)
        ? new URLSearchParams(window.location.search)
        : null;
    const customApi = urlParams?.get("api") || 
        (typeof window !== "undefined" ? (window.BAMI_API_URL || localStorage.getItem("bami_api_url")) : null);

    let API_BASE;
    if (customApi) {
        API_BASE = customApi.replace(/\/$/, "") + (customApi.endsWith("/api/v1") ? "" : "/api/v1");
    } else if (isLocal) {
        API_BASE = window.location.port === "8000" ? "/api/v1" : `http://${currentHost}:8000/api/v1`;
    } else if (window.location.protocol.startsWith("http")) {
        const port = window.location.port;
        // If loaded over local network IP with a dev port (e.g. http://192.168.1.5:5501), target port 8000
        if (port && port !== "80" && port !== "443" && port !== "8000") {
            API_BASE = `${window.location.protocol}//${currentHost}:8000/api/v1`;
        } else {
            // Hosted cloud deployment (Render, AWS, etc.) -> use same-origin relative /api/v1 to avoid Mixed Content
            API_BASE = `${window.location.origin}/api/v1`;
        }
    } else {
        // file:/// protocol fallback
        API_BASE = "http://127.0.0.1:8000/api/v1";
    }

    /**
     * Resilient fetch helper that handles cross-origin localhost/127.0.0.1 fallbacks
     * and cloud / relative fallbacks
     */
    async function apiFetch(endpoint, options = {}) {
        try {
            const resp = await fetch(`${API_BASE}${endpoint}`, options);
            return resp;
        } catch (err) {
            // Fallback 1: If primary host failed on localhost/127.0.0.1, try loopback alternate
            if (isLocal) {
                const altHost = currentHost === "localhost" ? "127.0.0.1" : "localhost";
                const altBase = `http://${altHost}:8000/api/v1`;
                if (altBase !== API_BASE) {
                    try {
                        const altResp = await fetch(`${altBase}${endpoint}`, options);
                        return altResp;
                    } catch (_) {}
                }
            }
            // Fallback 2: If absolute URL failed on a hosted domain, try relative /api/v1
            if (API_BASE !== "/api/v1" && window.location.protocol.startsWith("http")) {
                try {
                    const fallbackResp = await fetch(`/api/v1${endpoint}`, options);
                    return fallbackResp;
                } catch (_) {}
            }
            // Fallback 3: If on LAN or localhost, try direct port 8000
            if (window.location.protocol.startsWith("http")) {
                const port8000Base = `${window.location.protocol}//${currentHost}:8000/api/v1`;
                if (port8000Base !== API_BASE) {
                    try {
                        const altPortResp = await fetch(`${port8000Base}${endpoint}`, options);
                        return altPortResp;
                    } catch (_) {}
                }
            }
            throw err;
        }
    }

    // Application state
    let currentTarget = "COX-2";
    let activeJobId = null;
    let pollInterval = null;
    let cachedReceptors = {};
    let currentDockingResult = null;
    let viewer3D = null;
    let surfaceObj = null;
    let isSurfaceVisible = false;
    let currentStyleMode = 0; // 0: Cartoon, 1: Sticks, 2: Sphere/Spacefill

    // Target metadata configurations
    const TARGET_DATA = {
        "COX-2": {
            target: "COX-2",
            targetName: "Cyclooxygenase-2",
            pdbId: "6COX",
            resolution: "2.80 Å",
            organism: "Mus musculus / Homo sapiens homologous active site",
            desc: "Murine Cyclooxygenase-2 complexed with selective inhibitor SC-558. Active site pocket is 100% homologous to human COX-2 catalytic channel.",
            center: "X: 23.67, Y: 23.31, Z: 47.83",
            box: "18.0 × 18.0 × 18.0 Å",
            inhibitor: "SC-558 / Celecoxib",
            rcsbUrl: "https://www.rcsb.org/structure/6COX"
        },
        "EGFR": {
            target: "EGFR",
            targetName: "Epidermal Growth Factor Receptor",
            pdbId: "1M17",
            resolution: "2.60 Å",
            organism: "Homo sapiens",
            desc: "Human EGFR kinase domain complexed with 4-anilinoquinazoline inhibitor Erlotinib (Tarceva), capturing the active ATP-binding conformation.",
            center: "X: 22.01, Y: 0.25, Z: 52.79",
            box: "18.0 × 18.0 × 18.0 Å",
            inhibitor: "Erlotinib (Tarceva)",
            rcsbUrl: "https://www.rcsb.org/structure/1M17"
        }
    };

    // Dictionary of well-known reference drugs for instant name-to-SMILES resolution
    const KNOWN_DRUG_SMILES = {
        "aspirin": "CC(=O)Oc1ccccc1C(=O)O",
        "celecoxib": "CC1=CC=C(C=C1)C2=CC(=NN2C3=CC=C(C=C3)S(=O)(=O)N)C(F)(F)F",
        "erlotinib": "COCCOC1=C(C=C2C(=C1)C(=NC=N2)NC3=CC=CC(=C3)C#C)OCCOC",
        "gefitinib": "COC1=C(C=C2C(=C1)N=CN=C2NC3=CC(=C(C=C3)F)Cl)OCCCN4CCOCC4",
        "ibuprofen": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
        "indomethacin": "CC1=C(C2=C(N1C(=O)C3=CC=C(C=C3)Cl)C=CC(=C2)OC)CC(=O)O",
        "naproxen": "CC(C1=CC2=C(C=C1)C=C(C=C2)OC)C(=O)O",
        "diclofenac": "O=C(O)Cc1ccccc1Nc1c(Cl)cccc1Cl",
        "osimertinib": "CN(C)CC=CC(=O)Nc1cc(Nc2ncccn2)c(Nc2ccccc2)cc1OC",
        "lapatinib": "CS(=O)(=O)CCNCc1ccc(o1)c2ccc3c(c2)c(ncn3)Nc4ccc(c(c4)Cl)OCc5cccc(c5)F",
        "afatinib": "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(c(c3)Cl)F)ncnc2cc1O[C@H]3CCOC3",
        "meloxicam": "Cc1nc(ns1)NC(=O)C2=C(O)c3ccccc3S(=O)(=O)N2C",
        "rofecoxib": "O=S(=O)(c1ccc(cc1)C2=C(CO2)c3ccccc3)C",
        "sc-558": "CC1=CC=C(C=C1)C2=CC(=NN2C3=CC=C(C=C3)S(=O)(=O)N)C(Br)(F)F",
        "paracetamol": "CC(=O)NC1=CC=C(C=C1)O",
        "acetaminophen": "CC(=O)NC1=CC=C(C=C1)O"
    };

    /**
     * Resolve compound name to canonical SMILES if needed
     */
    async function resolveInputToSmiles(input) {
        input = (input || "").trim();
        if (!input) return "";

        // Check if already valid SMILES (heuristic check: contains typical SMILES bond or ring notation)
        const key = input.toLowerCase().replace(/[^a-z0-9]/g, "");

        // 1. Direct dictionary match
        for (const [k, smiles] of Object.entries(KNOWN_DRUG_SMILES)) {
            if (k.replace(/[^a-z0-9]/g, "") === key) {
                return smiles;
            }
        }

        // 2. Local curated dataset lookup via BAMI suggestions engine
        if (window.BAMI && typeof window.BAMI.findBioactiveMoleculeByName === "function") {
            try {
                const match = window.BAMI.findBioactiveMoleculeByName(input);
                if (match && match.smiles) {
                    return match.smiles;
                }
            } catch (_) {}
        }

        // 3. If looks like a plain chemical or drug name (no brackets or ring digits), query PubChem
        if (/^[A-Za-z0-9\s\-]+$/.test(input) && !input.includes("=") && !input.includes("@") && !input.includes("#")) {
            try {
                const resp = await fetch(`https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${encodeURIComponent(input)}/property/CanonicalSMILES/JSON`);
                if (resp.ok) {
                    const data = await resp.json();
                    const canonical = data?.PropertyTable?.Properties?.[0]?.CanonicalSMILES;
                    if (canonical) return canonical;
                }
            } catch (_) {}
        }

        return input;
    }

    // DOM Elements
    const cox2Btn = document.getElementById("target-cox2-btn");
    const egfrBtn = document.getElementById("target-egfr-btn");
    const receptorPdbId = document.getElementById("receptor-pdb-id");
    const rcsbLink = document.getElementById("rcsb-external-link");
    const receptorDesc = document.getElementById("receptor-desc");
    const pocketCenterText = document.getElementById("pocket-center-text");
    const pocketBoxText = document.getElementById("pocket-box-text");
    const refInhibitorText = document.getElementById("reference-inhibitor-text");

    const smilesInput = document.getElementById("docking-smiles-input");
    const exhaustivenessSelect = document.getElementById("exhaustiveness-select");
    const runDockingBtn = document.getElementById("run-docking-btn");

    const statusBadge = document.getElementById("docking-status-badge");
    const statusLabel = document.getElementById("docking-status-label");
    const progressBar = document.getElementById("docking-progress-bar");
    const progressPercent = document.getElementById("docking-progress-percent");
    const stageTitle = document.getElementById("docking-stage-title");
    const stageMsg = document.getElementById("docking-stage-msg");
    const errorBox = document.getElementById("docking-error-box");
    const errorMsg = document.getElementById("docking-error-message");
    const retryBtn = document.getElementById("retry-docking-btn");

    const affinityCard = document.getElementById("affinity-results-card");
    const bestAffinityVal = document.getElementById("best-affinity-val");
    const affinityBadge = document.getElementById("affinity-strength-badge");
    const resultsTargetPdb = document.getElementById("results-target-pdb");
    const dockingTimeVal = document.getElementById("docking-time-val");
    const contactCountVal = document.getElementById("contact-residues-count");
    const modesTbody = document.getElementById("vina-modes-tbody");
    const contactPillsList = document.getElementById("contact-pills-list");

    const viewportContainer = document.getElementById("docking-3dmol-viewport");
    const viewportPlaceholder = document.getElementById("viewport-placeholder");
    const placeholderTitle = document.getElementById("placeholder-title");
    const placeholderMsg = document.getElementById("placeholder-msg");
    const focusLigandBtn = document.getElementById("view-focus-ligand-btn");
    const toggleSurfaceBtn = document.getElementById("view-toggle-surface-btn");
    const styleCycleBtn = document.getElementById("view-style-btn");
    const resetCameraBtn = document.getElementById("view-reset-camera-btn");
    const fullscreenBtn = document.getElementById("view-fullscreen-btn");

    /**
     * Set active target (COX-2 or EGFR) and update metadata display
     */
    function setTarget(target) {
        currentTarget = target === "EGFR" ? "EGFR" : "COX-2";
        const meta = TARGET_DATA[currentTarget];

        if (cox2Btn && egfrBtn) {
            cox2Btn.classList.toggle("active", currentTarget === "COX-2");
            egfrBtn.classList.toggle("active", currentTarget === "EGFR");
        }

        if (receptorPdbId) receptorPdbId.textContent = `PDB: ${meta.pdbId}`;
        if (rcsbLink) rcsbLink.href = meta.rcsbUrl;
        if (receptorDesc) receptorDesc.textContent = meta.desc;
        if (pocketCenterText) pocketCenterText.textContent = meta.center;
        if (pocketBoxText) pocketBoxText.textContent = meta.box;
        if (refInhibitorText) refInhibitorText.textContent = meta.inhibitor;

        // If results are already showing for previous target, reset them
        if (currentDockingResult && currentDockingResult.target !== currentTarget) {
            resetStatusUI();
        }
    }

    // Expose setTarget globally for autocomplete & external integrations
    window.BAMI = window.BAMI || {};
    window.BAMI.setDockingTarget = setTarget;

    /**
     * Update Live Status Panel
     */
    function updateStatusUI(status, percent, message) {
        if (!statusBadge || !statusLabel) return;

        // Remove all status classes
        statusBadge.className = "status-indicator-badge";
        const statusClass = status.toLowerCase().replace(/\s+/g, "-");
        statusBadge.classList.add(statusClass);
        statusLabel.textContent = status;

        if (progressBar) {
            progressBar.style.width = `${percent}%`;
            progressBar.classList.toggle("running-shimmer", status === "Running" || status.startsWith("Preparing"));
        }

        if (progressPercent) progressPercent.textContent = `${percent}%`;
        if (stageTitle) stageTitle.textContent = status;
        if (stageMsg) stageMsg.textContent = message || "Processing molecular docking pipeline…";

        if (errorBox) {
            errorBox.hidden = (status !== "Failed");
        }
    }

    /**
     * Reset Status UI to Not Started
     */
    function resetStatusUI() {
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
        activeJobId = null;
        currentDockingResult = null;
        updateStatusUI("Not Started", 0, "Select a protein target and provide a ligand SMILES, then click 'Run AutoDock Vina Simulation'.");
        if (affinityCard) affinityCard.hidden = true;
        if (errorBox) errorBox.hidden = true;
        if (viewportPlaceholder) {
            viewportPlaceholder.classList.remove("hidden");
            if (placeholderTitle) placeholderTitle.textContent = "3D Molecular Viewport Ready";
            if (placeholderMsg) placeholderMsg.textContent = "Run docking to visualize the crystallographic protein receptor and the lowest-energy ligand binding pose in 3D.";
        }
        if (runDockingBtn) {
            runDockingBtn.disabled = false;
            runDockingBtn.querySelector(".btn-text").textContent = "Run AutoDock Vina Simulation";
        }
    }

    /**
     * Fetch receptor PDB file from backend (cached in memory)
     */
    async function fetchReceptorPdb(target) {
        if (cachedReceptors[target]) {
            return cachedReceptors[target];
        }
        const resp = await apiFetch(`/docking/receptor/${encodeURIComponent(target)}`);
        if (!resp.ok) {
            throw new Error(`Failed to load receptor structure for ${target}`);
        }
        const text = await resp.text();
        cachedReceptors[target] = text;
        return text;
    }

    /**
     * Initialize 3Dmol.js WebGL Viewer
     */
    function init3DmolViewer() {
        if (!viewportContainer || typeof $3Dmol === "undefined") return null;
        if (!viewer3D) {
            viewer3D = $3Dmol.createViewer(viewportContainer, {
                backgroundColor: "#0B061A",
                id: "docking-canvas-viewer"
            });
        }
        return viewer3D;
    }

    /**
     * Render the docked protein-ligand complex in 3D
     */
    async function render3DComplex(dockingResult) {
        const viewer = init3DmolViewer();
        if (!viewer) return;

        try {
            if (viewportPlaceholder) {
                viewportPlaceholder.classList.add("hidden");
            }

            viewer.clear();
            surfaceObj = null;
            isSurfaceVisible = false;

            // 1. Load Receptor Protein PDB
            const receptorPdb = await fetchReceptorPdb(dockingResult.target);
            const receptorModel = viewer.addModel(receptorPdb, "pdb");

            // Style receptor as secondary structure ribbon cartoon
            viewer.setStyle({ model: receptorModel }, {
                cartoon: {
                    color: "spectrum",
                    opacity: 0.88,
                    style: "trace"
                }
            });

            // 2. Load Docked Ligand (top pose PDBQT)
            const ligandPdbqt = dockingResult.docked_pdbqt || dockingResult.top_pose_pdb;
            let ligandModel = null;
            if (ligandPdbqt) {
                ligandModel = viewer.addModel(ligandPdbqt, "pdbqt");
                // Style ligand as prominent green-carbon sticks with CPK element spheres
                viewer.setStyle({ model: ligandModel }, {
                    stick: {
                        colorscheme: "greenCarbon",
                        radius: 0.28
                    },
                    sphere: {
                        scale: 0.32
                    }
                });
            }

            // 3. Highlight Contact Residues within 4.5 Å
            if (dockingResult.contact_residues && dockingResult.contact_residues.length > 0) {
                const resSeqList = dockingResult.contact_residues.map(r => r.seq);
                viewer.addStyle(
                    { model: receptorModel, resi: resSeqList },
                    {
                        stick: {
                            colorscheme: "yellowCarbon",
                            radius: 0.18
                        }
                    }
                );

                // Add small floating 3D labels for key contact residues
                try {
                    dockingResult.contact_residues.slice(0, 5).forEach(res => {
                        viewer.addResLabels(
                            { model: receptorModel, resi: res.seq },
                            {
                                font: "sans-serif",
                                fontSize: 11,
                                fontColor: "#FDE047",
                                backgroundOpacity: 0.6,
                                backgroundColor: "#1E1530",
                                showBackground: true
                            }
                        );
                    });
                } catch (_) {}
            }

            // 4. Focus Camera on Ligand & Render
            if (ligandModel) {
                viewer.zoomTo({ model: ligandModel }, 1200);
            } else {
                viewer.zoomTo();
            }
            viewer.render();

        } catch (err) {
            console.error("3Dmol rendering error:", err);
            if (viewportPlaceholder) {
                viewportPlaceholder.classList.remove("hidden");
                if (placeholderTitle) placeholderTitle.textContent = "3D Rendering Notice";
                if (placeholderMsg) placeholderMsg.textContent = "Receptor visualization completed. Interactive WebGL preview active.";
            }
        }
    }

    /**
     * Populate Results UI with real AutoDock Vina scores
     */
    function displayDockingResults(result) {
        currentDockingResult = result;

        if (affinityCard) affinityCard.hidden = false;

        const bestScore = result.top_affinity_kcal_mol != null ? Number(result.top_affinity_kcal_mol).toFixed(2) : "--";
        if (bestAffinityVal) bestAffinityVal.textContent = bestScore;

        if (affinityBadge) {
            affinityBadge.textContent = `${result.affinity_level || "Active Pose"}`;
            if (result.top_affinity_kcal_mol <= -9.0) {
                affinityBadge.style.background = "#059669";
            } else if (result.top_affinity_kcal_mol <= -7.0) {
                affinityBadge.style.background = "#10B981";
            } else if (result.top_affinity_kcal_mol <= -5.0) {
                affinityBadge.style.background = "#D97706";
            } else {
                affinityBadge.style.background = "#6B7280";
            }
        }

        if (resultsTargetPdb) {
            resultsTargetPdb.textContent = `${result.target} (${result.pdb_id})`;
        }
        if (dockingTimeVal) {
            dockingTimeVal.textContent = `${result.docking_duration_seconds}s (${result.completed_at || "Just now"})`;
        }
        if (contactCountVal) {
            contactCountVal.textContent = `${result.contact_residues ? result.contact_residues.length : 0} residues`;
        }

        // Render Modes Table
        if (modesTbody) {
            modesTbody.innerHTML = "";
            (result.modes || []).forEach((m, idx) => {
                const tr = document.createElement("tr");
                if (idx === 0) tr.className = "active-mode";
                tr.innerHTML = `
                    <td><strong>Mode ${m.mode}</strong> ${idx === 0 ? '<span class="dock-tag success-tag">BEST</span>' : ''}</td>
                    <td><strong style="color: #15803D;">${Number(m.affinity_kcal_mol).toFixed(2)} kcal/mol</strong></td>
                    <td>${Number(m.rmsd_lb).toFixed(2)} Å</td>
                    <td>${Number(m.rmsd_ub).toFixed(2)} Å</td>
                    <td><button type="button" class="pose-select-btn" data-mode="${m.mode}">Inspect Pose</button></td>
                `;
                modesTbody.appendChild(tr);
            });

            // Bind pose inspection
            modesTbody.querySelectorAll(".pose-select-btn").forEach(btn => {
                btn.addEventListener("click", () => {
                    const row = btn.closest("tr");
                    modesTbody.querySelectorAll("tr").forEach(r => r.classList.remove("active-mode"));
                    row.classList.add("active-mode");
                    if (viewer3D) {
                        viewer3D.zoomTo({ model: 1 }, 800);
                    }
                });
            });
        }

        // Render Contact Residue Pills
        if (contactPillsList) {
            contactPillsList.innerHTML = "";
            (result.contact_residues || []).forEach(res => {
                const pill = document.createElement("button");
                pill.type = "button";
                pill.className = "contact-pill";
                pill.textContent = `${res.label} (${res.min_dist_angstrom} Å)`;
                pill.title = `Focus on active pocket residue ${res.label}`;
                pill.addEventListener("click", () => {
                    if (viewer3D) {
                        viewer3D.zoomTo({ model: 0, resi: res.seq }, 900);
                    }
                });
                contactPillsList.appendChild(pill);
            });
        }

        // Render 3D Protein-Ligand Complex
        render3DComplex(result);
    }

    /**
     * Start live status polling for a docking job
     */
    function startStatusPolling(jobId) {
        if (pollInterval) clearInterval(pollInterval);
        activeJobId = jobId;

        pollInterval = setInterval(async () => {
            try {
                const resp = await apiFetch(`/docking/status/${encodeURIComponent(jobId)}`);
                if (!resp.ok) {
                    throw new Error(`Status check failed (${resp.status})`);
                }
                const data = await resp.json();

                updateStatusUI(data.status, data.progress_percent, data.stage_message);

                if (data.status === "Completed") {
                    clearInterval(pollInterval);
                    pollInterval = null;
                    if (runDockingBtn) {
                        runDockingBtn.disabled = false;
                        runDockingBtn.querySelector(".btn-text").textContent = "Run AutoDock Vina Simulation";
                    }
                    if (data.result) {
                        displayDockingResults(data.result);
                    }
                } else if (data.status === "Failed") {
                    clearInterval(pollInterval);
                    pollInterval = null;
                    if (runDockingBtn) {
                        runDockingBtn.disabled = false;
                        runDockingBtn.querySelector(".btn-text").textContent = "Run AutoDock Vina Simulation";
                    }
                    if (errorBox && errorMsg) {
                        errorBox.hidden = false;
                        errorMsg.textContent = data.error || "AutoDock Vina physics simulation encountered an error.";
                    }
                }
            } catch (err) {
                console.warn("Polling error:", err);
            }
        }, 350);
    }

    /**
     * Trigger Docking Simulation
     */
    async function runDockingSimulation() {
        const rawInput = smilesInput ? smilesInput.value.trim() : "";
        if (!rawInput) {
            alert("Please enter a valid SMILES string or select a reference compound lead.");
            if (smilesInput) smilesInput.focus();
            return;
        }

        const exhaustiveness = exhaustivenessSelect ? parseInt(exhaustivenessSelect.value, 10) : 4;

        if (runDockingBtn) {
            runDockingBtn.disabled = true;
            runDockingBtn.querySelector(".btn-text").textContent = "Simulating with AutoDock Vina…";
        }
        if (errorBox) errorBox.hidden = true;
        if (affinityCard) affinityCard.hidden = true;

        updateStatusUI("Preparing Ligand", 10, "Resolving molecular structure and generating 3D conformer…");

        try {
            // Resolve compound name (e.g. "Aspirin") to SMILES if necessary
            const smiles = await resolveInputToSmiles(rawInput);
            if (smiles !== rawInput && smilesInput) {
                smilesInput.value = smiles;
            }

            const resp = await apiFetch("/docking/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    smiles: smiles,
                    target: currentTarget,
                    exhaustiveness: exhaustiveness
                })
            });

            if (!resp.ok) {
                const errData = await resp.json().catch(() => ({}));
                const errMsg = errData.detail || (resp.status === 404
                    ? "Cannot connect to Docking API on port 8000. Please ensure the FastAPI backend is running."
                    : "Failed to start docking simulation.");
                throw new Error(errMsg);
            }

            const data = await resp.json();
            startStatusPolling(data.job_id);

        } catch (err) {
            console.error("Docking launch failed:", err);
            const targetDisplay = API_BASE.startsWith("/") ? `${window.location.origin}${API_BASE}` : API_BASE;
            const isNetErr = !err.status && (
                !err.message || 
                err.message.includes("Failed to fetch") || 
                err.message.includes("NetworkError") ||
                err.message.includes("Cannot connect")
            );
            const userFriendlyMsg = isNetErr
                ? `Cannot connect to FastAPI backend at ${targetDisplay}. Please verify the backend server is running (e.g. run 'npm run dev' or 'uvicorn app.main:app --app-dir Backend --host 0.0.0.0 --port 8000').`
                : (err.message || "Failed to start docking simulation.");
            updateStatusUI("Failed", 0, `Unable to launch docking: ${userFriendlyMsg}`);
            if (runDockingBtn) {
                runDockingBtn.disabled = false;
                runDockingBtn.querySelector(".btn-text").textContent = "Run AutoDock Vina Simulation";
            }
            if (errorBox && errorMsg) {
                errorBox.hidden = false;
                errorMsg.textContent = userFriendlyMsg;
            }
        }
    }

    // =========================================================
    // EVENT LISTENERS & INITIALIZATION
    // =========================================================

    function bindEvents() {
        // Target toggle buttons
        if (cox2Btn) {
            cox2Btn.addEventListener("click", () => setTarget("COX-2"));
        }
        if (egfrBtn) {
            egfrBtn.addEventListener("click", () => setTarget("EGFR"));
        }

        // Run button
        if (runDockingBtn) {
            runDockingBtn.addEventListener("click", runDockingSimulation);
        }

        // Retry button
        if (retryBtn) {
            retryBtn.addEventListener("click", runDockingSimulation);
        }

        // Autocomplete & Inline Suggestions for Docking Input
        const dockingContainer = document.getElementById("docking-search-container") || (smilesInput ? smilesInput.parentElement : null);
        const dockingDropdown = document.getElementById("docking-suggestions-dropdown");

        if (typeof initMoleculeAutocomplete === "function" && smilesInput) {
            window.dockingAutocomplete = initMoleculeAutocomplete({
                input: smilesInput,
                container: dockingContainer,
                dropdown: dockingDropdown,
                onSelect: (molecule) => {
                    smilesInput.value = molecule.name;
                    if (molecule.target) {
                        if (molecule.target.toUpperCase().includes("EGFR")) {
                            setTarget("EGFR");
                        } else if (molecule.target.toUpperCase().includes("COX-2")) {
                            setTarget("COX-2");
                        }
                    }
                    // Update active pill state
                    document.querySelectorAll(".preset-pill, .lead-pill").forEach(p => {
                        const isMatch = (p.dataset.name && p.dataset.name.toLowerCase() === molecule.name.toLowerCase()) ||
                                        (p.dataset.smiles && molecule.smiles && p.dataset.smiles === molecule.smiles);
                        p.classList.toggle("active", !!isMatch);
                    });
                }
            });
        }

        // Preset Quick Pills Click Handlers
        document.querySelectorAll(".preset-pill, .lead-pill").forEach(pill => {
            pill.addEventListener("click", () => {
                const molName = pill.dataset.name || "";
                const molTarget = pill.dataset.target || "";
                const molSmiles = pill.dataset.smiles || "";

                // 1. Fill molecule name automatically in the input
                if (smilesInput) {
                    smilesInput.value = molName || molSmiles;
                }

                // 2. Automatically select corresponding target
                if (molTarget) {
                    setTarget(molTarget);
                }

                // 3. Highlight this pill as active
                document.querySelectorAll(".preset-pill, .lead-pill").forEach(p => p.classList.remove("active"));
                pill.classList.add("active");

                // 4. Render the inline suggestion banner (just like in single prediction!)
                const curated = (window.BAMI && typeof window.BAMI.findBioactiveMoleculeByName === "function")
                    ? window.BAMI.findBioactiveMoleculeByName(molName)
                    : null;

                const moleculeData = curated || {
                    name: molName,
                    target: molTarget,
                    smiles: molSmiles,
                    formula: molName.toLowerCase() === "aspirin" ? "C9H8O4"
                        : molName.toLowerCase() === "celecoxib" ? "C17H14F3N3O2S"
                        : molName.toLowerCase() === "erlotinib" ? "C22H23N3O4"
                        : molName.toLowerCase() === "gefitinib" ? "C22H24ClFN4O3" : ""
                };

                const ac = window.dockingAutocomplete || window._bamiDockingAutocompleteInstance;
                if (ac && typeof ac.renderInlineBar === "function") {
                    ac.renderInlineBar(moleculeData);
                }
            });
        });

        // Sync active state when user manually types in the input
        if (smilesInput) {
            smilesInput.addEventListener("input", () => {
                const val = smilesInput.value.trim().toLowerCase();
                document.querySelectorAll(".preset-pill, .lead-pill").forEach(p => {
                    const nameMatch = p.dataset.name && p.dataset.name.toLowerCase() === val;
                    const smilesMatch = p.dataset.smiles && p.dataset.smiles.toLowerCase() === val;
                    p.classList.toggle("active", !!(nameMatch || smilesMatch));
                });
                if (!val) {
                    const ac = window.dockingAutocomplete || window._bamiDockingAutocompleteInstance;
                    if (ac && typeof ac.clearInlineBar === "function") {
                        ac.clearInlineBar();
                    }
                }
            });
        }

        // 3D Viewport Controls
        if (focusLigandBtn) {
            focusLigandBtn.addEventListener("click", () => {
                if (viewer3D) {
                    viewer3D.zoomTo({ model: 1 }, 800);
                }
            });
        }

        if (toggleSurfaceBtn) {
            toggleSurfaceBtn.addEventListener("click", () => {
                if (!viewer3D) return;
                if (!isSurfaceVisible) {
                    surfaceObj = viewer3D.addSurface($3Dmol.SurfaceType.VDW, {
                        opacity: 0.55,
                        color: "#8B5CF6"
                    }, { model: 0 });
                    isSurfaceVisible = true;
                    toggleSurfaceBtn.style.background = "#651FFF";
                } else {
                    if (surfaceObj) {
                        viewer3D.removeSurface(surfaceObj);
                        surfaceObj = null;
                    }
                    isSurfaceVisible = false;
                    toggleSurfaceBtn.style.background = "";
                }
                viewer3D.render();
            });
        }

        if (styleCycleBtn) {
            styleCycleBtn.addEventListener("click", () => {
                if (!viewer3D) return;
                currentStyleMode = (currentStyleMode + 1) % 3;
                if (currentStyleMode === 0) {
                    // Cartoon
                    viewer3D.setStyle({ model: 0 }, { cartoon: { color: "spectrum", opacity: 0.88 } });
                } else if (currentStyleMode === 1) {
                    // Sticks
                    viewer3D.setStyle({ model: 0 }, { stick: { colorscheme: "amino", radius: 0.15 } });
                } else {
                    // Spacefill
                    viewer3D.setStyle({ model: 0 }, { sphere: { scale: 0.8, colorscheme: "amino" } });
                }
                viewer3D.render();
            });
        }

        if (resetCameraBtn) {
            resetCameraBtn.addEventListener("click", () => {
                if (viewer3D) {
                    viewer3D.zoomTo();
                    viewer3D.render();
                }
            });
        }

        if (fullscreenBtn) {
            fullscreenBtn.addEventListener("click", () => {
                const wrapper = document.querySelector(".viewer-3d-wrapper");
                if (wrapper) {
                    wrapper.classList.toggle("fullscreen-mode");
                    const isFull = wrapper.classList.contains("fullscreen-mode");
                    fullscreenBtn.textContent = isFull ? "✕ Exit" : "⛶ Fullscreen";
                    setTimeout(() => {
                        if (viewer3D) viewer3D.resize();
                    }, 100);
                }
            });
        }

        // Download PDF Report with docking data
        const dockingDownloadBtn = document.getElementById("docking-download-pdf-btn");
        if (dockingDownloadBtn) {
            dockingDownloadBtn.addEventListener("click", async () => {
                const smiles = smilesInput ? smilesInput.value.trim() : "";
                if (!smiles) {
                    alert("Please provide a valid molecule SMILES string.");
                    return;
                }
                const originalHtml = dockingDownloadBtn.innerHTML;
                dockingDownloadBtn.disabled = true;
                dockingDownloadBtn.innerHTML = `<span>⏳ Compiling Scientific PDF with Docking Data…</span>`;

                try {
                    let authHeaders = {};
                    if (typeof window.getFirebaseAuthHeaders === "function") {
                        try {
                            authHeaders = await window.getFirebaseAuthHeaders();
                        } catch (_) {}
                    }

                    const resp = await apiFetch("/download-report", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            ...authHeaders
                        },
                        body: JSON.stringify({
                            smiles: smiles,
                            target: currentTarget,
                            include_admet: true,
                            include_docking: true,
                            docking_data: currentDockingResult
                        })
                    });

                    if (!resp.ok) {
                        const err = await resp.json().catch(() => ({}));
                        throw new Error(err.detail || `Server returned ${resp.status}`);
                    }

                    const blob = await resp.blob();
                    let filename = `BAMI_Docking_Report_${currentTarget}.pdf`;
                    const cd = resp.headers.get("Content-Disposition");
                    if (cd) {
                        const match = cd.match(/filename="?([^";]+)"?/);
                        if (match && match[1]) filename = match[1].trim();
                    }

                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = filename;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    window.URL.revokeObjectURL(url);

                } catch (err) {
                    console.error("PDF download failed:", err);
                    alert(`Failed to download report: ${err.message}`);
                } finally {
                    dockingDownloadBtn.disabled = false;
                    dockingDownloadBtn.innerHTML = originalHtml;
                }
            });
        }

        // Check URL Parameters on load (e.g. redirected from active prediction or deep-link)
        const params = new URLSearchParams(window.location.search);
        const urlSmiles = params.get("smiles") || params.get("q");
        const urlTarget = params.get("target");
        const autoRun = params.get("auto") === "1" || params.get("auto") === "true";

        if (urlTarget) {
            setTarget(urlTarget);
        } else {
            setTarget("COX-2");
        }

        if (urlSmiles && smilesInput) {
            smilesInput.value = urlSmiles;
            if (autoRun) {
                setTimeout(runDockingSimulation, 400);
            }
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bindEvents);
    } else {
        bindEvents();
    }

})();
