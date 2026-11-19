/* =========================================================
   BIOACTIVE MOLECULE INTELLIGENCE (BAMI)
   Intelligent Molecule Autocomplete & Inline Suggestion Engine
   ========================================================= */

(function (global) {
    "use strict";

    /* =========================================================
       1. RELIABLE CURATED BIOACTIVE MOLECULE DATASET
       Scientifically verified molecules for EGFR, COX-2, NSAIDs,
       and common bioactive drug compounds.
       ========================================================= */
    const BIOACTIVE_MOLECULES = [
        /* ---------------- EGFR INHIBITORS ---------------- */
        {
            name: "Erlotinib",
            synonyms: ["Tarceva", "CP-358774", "OSI-774"],
            formula: "C22H23N3O4",
            target: "EGFR",
            targetType: "EGFR",
            classType: "1st-Gen EGFR TKI",
            smiles: "COCCOC1=C(C=C2C(=C1)C(=NC=N2)NC3=CC=CC(=C3)C#C)OCCOC",
            description: "Potent EGFR tyrosine kinase inhibitor approved for non-small cell lung cancer."
        },
        {
            name: "Gefitinib",
            synonyms: ["Iressa", "ZD1839"],
            formula: "C22H24ClFN4O3",
            target: "EGFR",
            targetType: "EGFR",
            classType: "1st-Gen EGFR TKI",
            smiles: "COC1=C(C=C2C(=C1)N=CN=C2NC3=CC(=C(C=C3)F)Cl)OCCCN4CCOCC4",
            description: "Selective EGFR kinase inhibitor for EGFR-mutated advanced adenocarcinoma."
        },
        {
            name: "Osimertinib",
            synonyms: ["Tagrisso", "AZD9291"],
            formula: "C28H33N7O2",
            target: "EGFR",
            targetType: "EGFR",
            classType: "3rd-Gen EGFR TKI",
            smiles: "CN1C=C(C2=CC=CC=C21)C3=NC(=NC=C3)NC4=C(C=C(C(=C4)NC(=O)C=C)N(C)CCN(C)C)OC",
            description: "3rd-generation mutant-selective EGFR inhibitor targeting T790M resistance mutations."
        },
        {
            name: "Afatinib",
            synonyms: ["Gilotrif", "BIBW 2992"],
            formula: "C24H25ClFN5O3",
            target: "EGFR",
            targetType: "EGFR",
            classType: "2nd-Gen Pan-HER TKI",
            smiles: "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(Cl)c(F)c3)ncnc2cc1O[C@H]1CCOC1",
            description: "Irreversible covalent ErbB family blocker inhibiting EGFR (HER1) and HER2."
        },
        {
            name: "Lapatinib",
            synonyms: ["Tykerb", "GW572016"],
            formula: "C29H26ClFN4O4S",
            target: "EGFR",
            targetType: "EGFR",
            classType: "Dual EGFR/HER2 TKI",
            smiles: "CS(=O)(=O)CCNCc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)c(Cl)c4)c3c2)o1",
            description: "Dual reversible inhibitor of EGFR and HER2 receptor tyrosine kinase domains."
        },
        {
            name: "Dacomitinib",
            synonyms: ["Vizimpro", "PF-00299804"],
            formula: "C24H25ClFN5O2",
            target: "EGFR",
            targetType: "EGFR",
            classType: "2nd-Gen Irreversible TKI",
            smiles: "COc1cc2ncnc(Nc3ccc(Cl)c(F)c3)c2cc1NC(=O)/C=C/CN1CCCCC1",
            description: "Irreversible pan-HER inhibitor with selective activity against EGFR mutations."
        },
        {
            name: "Brigatinib",
            synonyms: ["Alunbrig", "AP26113"],
            formula: "C29H32ClN7O2",
            target: "EGFR",
            targetType: "EGFR",
            classType: "Multi-kinase Inhibitor",
            smiles: "COc1cc(Nc2ncc(Cl)c(Nc3ccccc3P(=O)(C)C)n2)ccc1N1CCN(C)CC1",
            description: "Kinase inhibitor targeting ALK and multiple EGFR mutant variants."
        },
        {
            name: "Mobocertinib",
            synonyms: ["Exkivity", "TAK-788"],
            formula: "C32H39N7O4",
            target: "EGFR",
            targetType: "EGFR",
            classType: "EGFR Exon 20 TKI",
            smiles: "CC(C)OC(=O)c1c(Nc2nc(Nc3ccc(N4CCN(C)CC4)cc3)ncc2Cl)c(C)n(C)c1=O",
            description: "Oral kinase inhibitor designed to selectively target EGFR exon 20 insertions."
        },
        {
            name: "Vandetanib",
            synonyms: ["Caprelsa", "ZD6474"],
            formula: "C22H24BrFN4O2",
            target: "EGFR",
            targetType: "EGFR",
            classType: "EGFR/VEGFR Inhibitor",
            smiles: "COc1cc2ncnc(Nc3ccc(Br)cc3F)c2cc1OCC1CCN(C)CC1",
            description: "Tyrosine kinase inhibitor targeting EGFR, VEGFR-2, and RET pathways."
        },
        {
            name: "Neratinib",
            synonyms: ["Nerlynx", "HKI-272"],
            formula: "C30H29ClN6O3",
            target: "EGFR",
            targetType: "EGFR",
            classType: "Pan-HER Inhibitor",
            smiles: "COc1cc2c(Nc3ccc(OCc4cccc(Cl)c4)c(Cl)c3)ncnc2cc1NC(=O)/C=C/CN(C)C",
            description: "Irreversible inhibitor of EGFR, HER2, and HER4 receptor kinases."
        },
        {
            name: "Icotinib",
            synonyms: ["Conmana", "BPI-2009H"],
            formula: "C22H21N3O4",
            target: "EGFR",
            targetType: "EGFR",
            classType: "1st-Gen EGFR TKI",
            smiles: "C#Cc1cccc(Nc2ncnc3cc4c(cc23)OCCO4)c1",
            description: "Potent and selective EGFR tyrosine kinase inhibitor with a crown-ether backbone."
        },

        /* ---------------- COX-2 SELECTIVE INHIBITORS ---------------- */
        {
            name: "Celecoxib",
            synonyms: ["Celebrex", "SC-58635"],
            formula: "C17H14F3N3O2S",
            target: "COX-2",
            targetType: "COX-2",
            classType: "Selective COX-2 Inhibitor",
            smiles: "Cc1ccc(-c2cc(C(F)(F)F)nn2-c2ccc(S(N)(=O)=O)cc2)cc1",
            description: "Benchmark diaryl-substituted pyrazole selective cyclooxygenase-2 inhibitor."
        },
        {
            name: "Rofecoxib",
            synonyms: ["Vioxx", "MK-0966"],
            formula: "C17H14O4S",
            target: "COX-2",
            targetType: "COX-2",
            classType: "Selective COX-2 Inhibitor",
            smiles: "O=C1OC(C)(C)C(=C1c2ccc(S(=O)(=O)C)cc2)c3ccccc3",
            description: "Furanone-based selective COX-2 inhibitor with high target binding affinity."
        },
        {
            name: "Valdecoxib",
            synonyms: ["Bextra", "SC-65872"],
            formula: "C16H14N2O3S",
            target: "COX-2",
            targetType: "COX-2",
            classType: "Selective COX-2 Inhibitor",
            smiles: "Cc1onc(-c2ccccc2)c1-c1ccc(S(N)(=O)=O)cc1",
            description: "Diaryl isoxazole selective COX-2 inhibitor for inflammatory osteoarthritis."
        },
        {
            name: "Etoricoxib",
            synonyms: ["Arcoxia", "MK-0663"],
            formula: "C18H15ClN2O2S",
            target: "COX-2",
            targetType: "COX-2",
            classType: "Selective COX-2 Inhibitor",
            smiles: "Cc1ccc(-c2ncc(Cl)cc2-c2ccc(S(C)(=O)=O)cc2)cn1",
            description: "Bipyridine selective inhibitor of COX-2 with high selectivity over COX-1."
        },
        {
            name: "Parecoxib",
            synonyms: ["Dynastat", "SC-69124A"],
            formula: "C19H18N2O4S",
            target: "COX-2",
            targetType: "COX-2",
            classType: "COX-2 Inhibitor Prodrug",
            smiles: "CCC(=O)N(c1ccc(-c2onc(C)c2-c2ccccc2)cc1)S(C)(=O)=O",
            description: "Injectable water-soluble amide prodrug rapidly hydrolyzed in vivo to valdecoxib."
        },
        {
            name: "Lumiracoxib",
            synonyms: ["Prexige", "COX189"],
            formula: "C15H13ClFNO2",
            target: "COX-2",
            targetType: "COX-2",
            classType: "Selective COX-2 Inhibitor",
            smiles: "Cc1ccccc1Nc1c(Cl)cccc1CC(=O)O",
            description: "Arylacetic acid-derivative NSAID exhibiting high COX-2 selectivity."
        },
        {
            name: "Meloxicam",
            synonyms: ["Mobic", "Metacam"],
            formula: "C14H13N3O4S2",
            target: "COX-2",
            targetType: "COX-2",
            classType: "COX-2 Preferential Oxicam",
            smiles: "Cc1ncc(NC(=O)C2=C(O)c3ccccc3S(=O)(=O)N2C)s1",
            description: "Enolic acid (oxicam) class NSAID with preferential inhibition of COX-2."
        },
        {
            name: "Nimesulide",
            synonyms: ["Aulin", "Mesulid"],
            formula: "C13H12N2O5S",
            target: "COX-2",
            targetType: "COX-2",
            classType: "Selective COX-2 Inhibitor",
            smiles: "CS(=O)(=O)Nc1ccc([N+](=O)[O-])cc1Oc1ccccc1",
            description: "Sulfonanilide NSAID exhibiting preferential cyclooxygenase-2 inhibition."
        },

        /* ---------------- CLASSICAL NSAIDS & ANALGESICS ---------------- */
        {
            name: "Aspirin",
            synonyms: ["Acetylsalicylic Acid", "ASA", "Ecotrin", "Empirin"],
            formula: "C9H8O4",
            target: "COX-1 / COX-2",
            targetType: "COX-2",
            classType: "Irreversible COX Inhibitor",
            smiles: "CC(=O)Oc1ccccc1C(=O)O",
            description: "Prototypical non-steroidal anti-inflammatory drug; irreversibly acetylates COX active site."
        },
        {
            name: "Paracetamol",
            synonyms: ["Acetaminophen", "Tylenol", "Panadol", "APAP"],
            formula: "C8H9NO2",
            target: "COX-1 / COX-2",
            targetType: "COX-2",
            classType: "Anilide Analgesic",
            smiles: "CC(=O)Nc1ccc(O)cc1",
            description: "Widely used central analgesic and antipyretic agent that modulates peroxidase/COX activity."
        },
        {
            name: "Ibuprofen",
            synonyms: ["Advil", "Motrin", "Nurofen", "Brufen"],
            formula: "C13H18O2",
            target: "COX-1 / COX-2",
            targetType: "COX-2",
            classType: "Propionic Acid NSAID",
            smiles: "CC(C)Cc1ccc(C(C)C(=O)O)cc1",
            description: "Non-selective reversible competitive inhibitor of both COX-1 and COX-2 enzymes."
        },
        {
            name: "Naproxen",
            synonyms: ["Aleve", "Naprosyn", "Anaprox"],
            formula: "C14H14O3",
            target: "COX-1 / COX-2",
            targetType: "COX-2",
            classType: "Propionic Acid NSAID",
            smiles: "COc1ccc2cc(C(C)C(=O)O)ccc2c1",
            description: "Non-selective COX inhibitor with balanced COX-1/COX-2 suppression profile."
        },
        {
            name: "Diclofenac",
            synonyms: ["Voltaren", "Cataflam", "Zipsor"],
            formula: "C14H11Cl2NO2",
            target: "COX-1 / COX-2",
            targetType: "COX-2",
            classType: "Phenylacetic Acid NSAID",
            smiles: "O=C(O)Cc1ccccc1Nc1c(Cl)cccc1Cl",
            description: "Potent NSAID displaying higher relative affinity for COX-2 than classic propionates."
        },
        {
            name: "Indomethacin",
            synonyms: ["Indocin", "Indocid"],
            formula: "C19H16ClNO4",
            target: "COX-1 / COX-2",
            targetType: "COX-2",
            classType: "Indole-acetic Acid NSAID",
            smiles: "COc1ccc2c(c1)c(CC(=O)O)c(C)n2C(=O)c1ccc(Cl)cc1",
            description: "Potent non-selective COX inhibitor with time-dependent inactivation kinetics."
        },
        {
            name: "Ketoprofen",
            synonyms: ["Orudis", "Oruvail", "Actron"],
            formula: "C16H14O3",
            target: "COX-1 / COX-2",
            targetType: "COX-2",
            classType: "Propionic Acid NSAID",
            smiles: "CC(C(=O)O)c1cccc(C(=O)c2ccccc2)c1",
            description: "Reversible inhibitor of cyclooxygenase-1 and cyclooxygenase-2."
        },
        {
            name: "Piroxicam",
            synonyms: ["Feldene"],
            formula: "C15H13N3O4S",
            target: "COX-1 / COX-2",
            targetType: "COX-2",
            classType: "Oxicam NSAID",
            smiles: "CN1C(=C(c2ccccc2S1(=O)=O)O)C(=O)Nc3ccccn3",
            description: "Long-acting oxicam derivative non-selective COX-1 and COX-2 inhibitor."
        },
        {
            name: "Mefenamic Acid",
            synonyms: ["Ponstel", "Ponstan"],
            formula: "C15H15NO2",
            target: "COX-1 / COX-2",
            targetType: "COX-2",
            classType: "Fenamate NSAID",
            smiles: "Cc1cccc(C)c1Nc1ccccc1C(=O)O",
            description: "Anthranilic acid derivative binding both COX isoforms to diminish prostaglandin synthesis."
        },
        {
            name: "Sulindac",
            synonyms: ["Clinoril"],
            formula: "C20H17FO3S",
            target: "COX-1 / COX-2",
            targetType: "COX-2",
            classType: "Sulfinyl Indene Prodrug",
            smiles: "Cc1c(CC(=O)O)c2cc(F)ccc2c1/C=C/c1ccc(S(C)=O)cc1",
            description: "Prodrug metabolized to an active sulfide metabolite that potently inhibits COX."
        },
        {
            name: "Ketorolac",
            synonyms: ["Toradol", "Acular"],
            formula: "C15H13NO3",
            target: "COX-1 / COX-2",
            targetType: "COX-2",
            classType: "Pyrrolizine Carboxylic Acid",
            smiles: "O=C(O)C1CCc2c1n(C(=O)c1ccccc1)c1ccccc21",
            description: "Potent analgesic NSAID with high affinity for cyclooxygenase enzymes."
        },
        {
            name: "Flurbiprofen",
            synonyms: ["Ansaid", "Froben"],
            formula: "C15H13FO2",
            target: "COX-1 / COX-2",
            targetType: "COX-2",
            classType: "Phenylalkanoic Acid NSAID",
            smiles: "CC(C(=O)O)c1ccc(-c2ccccc2)c(F)c1",
            description: "Fluorinated propionic acid NSAID inhibiting cyclooxygenase pathways."
        },
        {
            name: "Etodolac",
            synonyms: ["Lodine"],
            formula: "C17H21NO3",
            target: "COX-2",
            targetType: "COX-2",
            classType: "Pyranocarboxylic Acid NSAID",
            smiles: "CCc1ccc2c(c1)c(CC)c(CC(=O)O)o2",
            description: "NSAID displaying preferential inhibition of COX-2 over COX-1."
        },
        {
            name: "Nabumetone",
            synonyms: ["Relafen"],
            formula: "C15H16O2",
            target: "COX-2",
            targetType: "COX-2",
            classType: "Non-acidic Prodrug NSAID",
            smiles: "COc1ccc2cc(CCC(C)=O)ccc2c1",
            description: "Non-acidic prodrug converted by hepatic metabolism to 6-MNA, a preferential COX-2 inhibitor."
        },
        {
            name: "Oxaprozin",
            synonyms: ["Daypro", "Duraprox"],
            formula: "C18H15NO3",
            target: "COX-1 / COX-2",
            targetType: "COX-2",
            classType: "Propionic Acid NSAID",
            smiles: "O=C(O)CCc1nc(-c2ccccc2)c(-c2ccccc2)o1",
            description: "Once-daily propionic acid NSAID with dual COX-1 and COX-2 activity."
        },
        {
            name: "Diflunisal",
            synonyms: ["Dolobid"],
            formula: "C13H8F2O3",
            target: "COX-1 / COX-2",
            targetType: "COX-2",
            classType: "Salicylic Acid Derivative",
            smiles: "O=C(O)c1cc(-c2ccc(F)cc2F)ccc1O",
            description: "Difluorophenyl derivative of salicylic acid with prolonged competitive COX inhibition."
        }
    ];

    /* Popular quick suggestions shown when user focuses on an empty input */
    const POPULAR_SUGGESTIONS = [
        "Erlotinib",
        "Gefitinib",
        "Aspirin",
        "Celecoxib",
        "Paracetamol",
        "Osimertinib",
        "Ibuprofen"
    ];

    /* =========================================================
       2. TEXT & CHEMICAL FORMULA FORMATTING HELPERS
       ========================================================= */

    function formatMolecularFormula(formula) {
        if (!formula) return "";
        return formula.replace(/(\d+)/g, "<sub>$1</sub>");
    }

    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
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

    function highlightMatchingText(text, query) {
        if (!query || !text) return escapeHtml(text);
        const cleanQuery = query.trim();
        if (!cleanQuery) return escapeHtml(text);

        const regex = new RegExp(`(${escapeRegExp(cleanQuery)})`, "gi");
        const parts = text.split(regex);
        return parts.map(part => {
            if (part.toLowerCase() === cleanQuery.toLowerCase()) {
                return `<mark class="suggestion-highlight">${escapeHtml(part)}</mark>`;
            }
            return escapeHtml(part);
        }).join("");
    }

    /* =========================================================
       3. SEARCH & MATCHING ALGORITHM
       ========================================================= */

    function searchCuratedDataset(query, currentTarget) {
        if (!query || query.length < 2) return [];

        const cleanQuery = query.trim().toLowerCase();
        const results = [];

        for (const mol of BIOACTIVE_MOLECULES) {
            const nameLower = mol.name.toLowerCase();
            let matched = false;
            let score = 0;
            let matchedSynonym = "";

            if (nameLower.startsWith(cleanQuery)) {
                matched = true;
                score += 100 - nameLower.length;
            } else if (nameLower.includes(cleanQuery)) {
                matched = true;
                score += 50 - nameLower.indexOf(cleanQuery);
            } else {
                for (const syn of mol.synonyms) {
                    const synLower = syn.toLowerCase();
                    if (synLower.startsWith(cleanQuery)) {
                        matched = true;
                        matchedSynonym = syn;
                        score += 80 - synLower.length;
                        break;
                    } else if (synLower.includes(cleanQuery)) {
                        matched = true;
                        matchedSynonym = syn;
                        score += 40 - synLower.indexOf(cleanQuery);
                        break;
                    }
                }
            }

            if (matched) {
                // Boost score if molecule matches selected target
                if (currentTarget && mol.targetType && mol.targetType.toUpperCase() === currentTarget.toUpperCase()) {
                    score += 35;
                }
                results.push({
                    name: mol.name,
                    formula: mol.formula,
                    target: mol.target,
                    targetType: mol.targetType,
                    classType: mol.classType,
                    description: mol.description,
                    smiles: mol.smiles,
                    matchedSynonym: matchedSynonym,
                    source: "curated",
                    score: score
                });
            }
        }

        results.sort((a, b) => b.score - a.score);
        return results;
    }

    async function fetchPubChemAutocomplete(query, signal) {
        if (!query || query.length < 2) return [];

        const url = `https://pubchem.ncbi.nlm.nih.gov/rest/autocomplete/compound/${encodeURIComponent(query)}/JSON?limit=8`;
        try {
            const response = await fetch(url, { signal });
            if (!response.ok) return [];

            const data = await response.json();
            const names = data.dictionary_terms?.compound || [];
            return names.map(name => ({
                name: name.charAt(0).toUpperCase() + name.slice(1),
                formula: "",
                target: "",
                targetType: "",
                classType: "Chemical Compound (PubChem)",
                description: "Verified chemical compound record from NCBI PubChem.",
                smiles: "",
                source: "pubchem"
            }));
        } catch (error) {
            return [];
        }
    }

    function deduplicateSuggestions(localResults, pubChemResults) {
        const seen = new Set();
        const merged = [];

        for (const item of localResults) {
            const key = item.name.toLowerCase().trim();
            if (!seen.has(key)) {
                seen.add(key);
                merged.push(item);
            }
        }

        for (const item of pubChemResults) {
            const key = item.name.toLowerCase().trim();
            if (!seen.has(key)) {
                seen.add(key);
                merged.push(item);
            }
        }

        return merged;
    }

    function findBioactiveMoleculeByName(name) {
        if (!name) return null;
        const clean = name.trim().toLowerCase();
        for (const mol of BIOACTIVE_MOLECULES) {
            if (mol.name.toLowerCase() === clean) return mol;
            for (const syn of mol.synonyms) {
                if (syn.toLowerCase() === clean) return mol;
            }
        }
        return null;
    }

    function findBioactiveMoleculeBySmiles(smiles) {
        if (!smiles) return null;
        const clean = smiles.trim();
        for (const mol of BIOACTIVE_MOLECULES) {
            if (mol.smiles === clean) return mol;
        }
        if (window.RDKitModule) {
            try {
                const m1 = window.RDKitModule.get_mol(clean);
                if (m1) {
                    const canon1 = m1.get_smiles();
                    m1.delete();
                    for (const mol of BIOACTIVE_MOLECULES) {
                        const m2 = window.RDKitModule.get_mol(mol.smiles);
                        if (m2) {
                            const canon2 = m2.get_smiles();
                            m2.delete();
                            if (canon1 === canon2) return mol;
                        }
                    }
                }
            } catch (_) {}
        }
        return null;
    }

    /* =========================================================
       4. MOLECULE AUTOCOMPLETE CONTROLLER CLASS
       Features:
       - Top inline suggestion banner right above the search box
       - Complete suggestions dropdown with hover animations
       - Arrow key navigation & Enter / Tab autocompletion
       - Quick suggestions on focus
       ========================================================= */

    class MoleculeAutocomplete {
        constructor(options) {
            this.input = options.input;
            this.container = options.container;
            this.dropdown = options.dropdown;
            this.targetSelect = options.targetSelect || null;
            this.onSelect = options.onSelect || (() => {});

            this.items = [];
            this.activeIndex = -1;
            this.isOpen = false;
            this.debounceTimer = null;
            this.abortController = null;
            this.currentQuery = "";

            this.inlineBar = null;

            this.init();
        }

        init() {
            if (!this.input) return;

            // Ensure container exists
            if (!this.container) {
                this.container = this.input.parentElement;
                this.container.classList.add("molecule-search-container");
            }

            // Ensure dropdown element exists
            if (!this.dropdown) {
                this.dropdown = document.createElement("div");
                this.dropdown.className = "molecule-suggestions-dropdown";
                this.dropdown.id = (this.input.id || "molecule") + "-suggestions-dropdown";
                this.container.appendChild(this.dropdown);
            }

            // Create or bind Inline Suggestion Banner
            let existingBar = this.container.querySelector(".inline-suggestion-bar");
            if (!existingBar) {
                this.inlineBar = document.createElement("div");
                this.inlineBar.className = "inline-suggestion-bar";
                this.inlineBar.style.display = "none";
                this.container.insertBefore(this.inlineBar, this.dropdown);
            } else {
                this.inlineBar = existingBar;
            }

            // Initial hide state with robust style overrides
            this.dropdown.style.display = "none";
            this.dropdown.setAttribute("hidden", "");

            // Accessibility wiring
            this.input.setAttribute("aria-autocomplete", "list");
            this.input.setAttribute("aria-expanded", "false");
            this.input.setAttribute("aria-controls", this.dropdown.id);
            this.dropdown.setAttribute("role", "listbox");

            // Event listeners on input
            this.input.addEventListener("input", (e) => this.handleInput(e));
            this.input.addEventListener("keyup", (e) => {
                if (e.key !== "ArrowDown" && e.key !== "ArrowUp" && e.key !== "Enter" && e.key !== "Escape" && e.key !== "Tab") {
                    this.handleInput(e);
                }
            });
            this.input.addEventListener("keydown", (e) => this.handleKeyDown(e));
            this.input.addEventListener("focus", () => this.handleFocus());

            // Close on click outside
            document.addEventListener("click", (e) => {
                if (this.container && !this.container.contains(e.target)) {
                    this.close();
                }
            });

            // Target selector change listener
            if (this.targetSelect) {
                this.targetSelect.addEventListener("change", () => {
                    if (this.input.value.trim().length >= 2) {
                        this.executeSearch(this.input.value.trim());
                    }
                });
            }
        }

        handleFocus() {
            const query = this.input.value.trim();
            if (query.length >= 2) {
                this.executeSearch(query);
            } else if (query.length === 0) {
                this.renderQuickPills();
            }
        }

        handleInput(e) {
            const query = this.input.value.trim();
            this.currentQuery = query;

            if (query.length < 2) {
                this.clearInlineBar();
                if (query.length === 0) {
                    this.renderQuickPills();
                } else {
                    this.close();
                }
                return;
            }

            this.executeSearch(query);
        }

        renderQuickPills() {
            this.dropdown.innerHTML = "";
            const currentTarget = this.targetSelect ? this.targetSelect.value : "";

            const header = document.createElement("div");
            header.className = "suggestion-dropdown-header";
            header.innerHTML = `
                <span class="dropdown-header-title">⚡ Quick Bioactive Targets</span>
                <span class="dropdown-header-hint">Click any to load</span>
            `;
            this.dropdown.appendChild(header);

            const pillsContainer = document.createElement("div");
            pillsContainer.className = "quick-suggestions-row";

            POPULAR_SUGGESTIONS.forEach(name => {
                const mol = findBioactiveMoleculeByName(name);
                if (!mol) return;

                const pill = document.createElement("button");
                pill.type = "button";
                pill.className = "quick-suggestion-pill";
                if (currentTarget && mol.target.toUpperCase().includes(currentTarget.toUpperCase())) {
                    pill.classList.add("pill-highlight");
                }

                pill.innerHTML = `
                    <span class="pill-icon">⌬</span>
                    <span class="pill-name">${escapeHtml(mol.name)}</span>
                    <span class="pill-target">${escapeHtml(mol.target)}</span>
                `;

                pill.addEventListener("click", (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.selectItem(mol);
                });

                pillsContainer.appendChild(pill);
            });

            this.dropdown.appendChild(pillsContainer);
            this.open();
        }

        executeSearch(query) {
            const currentTarget = this.targetSelect ? this.targetSelect.value : "";
            // 1. Instant local curated search
            const localResults = searchCuratedDataset(query, currentTarget);
            this.items = localResults;
            this.activeIndex = -1;

            // Render top result in Inline Suggestion Bar
            if (localResults.length > 0) {
                this.renderInlineBar(localResults[0]);
            } else {
                this.clearInlineBar();
            }

            // Render dropdown list
            this.render(this.items, query, true);
            this.open();

            // 2. Debounced PubChem query
            if (this.debounceTimer) clearTimeout(this.debounceTimer);
            if (this.abortController) this.abortController.abort();

            this.abortController = new AbortController();
            const signal = this.abortController.signal;

            this.debounceTimer = setTimeout(async () => {
                const pubchemResults = await fetchPubChemAutocomplete(query, signal);
                if (this.currentQuery !== query) return;

                const merged = deduplicateSuggestions(localResults, pubchemResults);
                this.items = merged;

                if (this.items.length > 0) {
                    this.renderInlineBar(this.items[0]);
                }

                this.render(this.items, query, false);
                this.open();
            }, 200);
        }

        renderInlineBar(topMolecule) {
            if (!this.inlineBar || !topMolecule) return;

            let targetHtml = "";
            if (topMolecule.target) {
                const isEgfr = topMolecule.target.toUpperCase().includes("EGFR");
                const badgeClass = isEgfr ? "badge-egfr" : "badge-cox2";
                targetHtml = `<span class="inline-target-chip ${badgeClass}">🎯 ${escapeHtml(topMolecule.target)}</span>`;
            }

            let formulaHtml = "";
            if (topMolecule.formula) {
                formulaHtml = `<span class="inline-formula-chip">${formatMolecularFormula(topMolecule.formula)}</span>`;
            }

            const isDockingPage = !document.getElementById("predict-btn") && !!document.getElementById("run-docking-btn");
            const actionLabel = isDockingPage ? "Dock Now" : "Screen Now";
            const actionTitle = isDockingPage ? "Fill and Run AutoDock Vina" : "Fill and Screen";

            this.inlineBar.innerHTML = `
                <div class="inline-suggestion-content">
                    <span class="inline-sparkle">✦</span>
                    <span class="inline-label">Inline Suggestion:</span>
                    <strong class="inline-name">${escapeHtml(topMolecule.name)}</strong>
                    ${formulaHtml}
                    ${targetHtml}
                </div>
                <div class="inline-suggestion-actions">
                    <button type="button" class="inline-apply-btn" title="Press Tab or Enter to apply">
                        <span>Fill (Tab)</span>
                        <span aria-hidden="true">↵</span>
                    </button>
                    <button type="button" class="inline-predict-btn" title="${actionTitle}">
                        <span>${actionLabel}</span>
                        <span aria-hidden="true">→</span>
                    </button>
                </div>
            `;

            this.inlineBar.style.display = "flex";

            // Click on apply button
            const applyBtn = this.inlineBar.querySelector(".inline-apply-btn");
            if (applyBtn) {
                applyBtn.addEventListener("click", (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.selectItem(topMolecule);
                });
            }

            // Click on Screen / Dock Now button
            const screenBtn = this.inlineBar.querySelector(".inline-predict-btn");
            if (screenBtn) {
                screenBtn.addEventListener("click", (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.selectItem(topMolecule);
                    const actionBtn = document.getElementById("predict-btn") || document.getElementById("run-docking-btn") || document.getElementById("admet-screen-btn");
                    if (actionBtn) actionBtn.click();
                });
            }

            // Clicking anywhere on the banner
            this.inlineBar.onclick = (e) => {
                if (e.target.tagName !== "BUTTON" && !e.target.closest("button")) {
                    this.selectItem(topMolecule);
                }
            };
        }

        clearInlineBar() {
            if (this.inlineBar) {
                this.inlineBar.innerHTML = "";
                this.inlineBar.style.display = "none";
            }
        }

        handleKeyDown(e) {
            // Tab key applies top inline suggestion
            if (e.key === "Tab") {
                if (this.items.length > 0) {
                    const selected = this.activeIndex >= 0 ? this.items[this.activeIndex] : this.items[0];
                    if (selected) {
                        e.preventDefault();
                        this.selectItem(selected);
                        return;
                    }
                }
            }

            // Right arrow at end of input completes top suggestion
            if (e.key === "ArrowRight" && this.input.selectionStart === this.input.value.length) {
                if (this.items.length > 0) {
                    const top = this.items[0];
                    if (top && top.name.toLowerCase().startsWith(this.input.value.trim().toLowerCase())) {
                        e.preventDefault();
                        this.selectItem(top);
                        return;
                    }
                }
            }

            if (!this.isOpen) {
                if ((e.key === "ArrowDown" || e.key === "ArrowUp") && this.input.value.trim().length >= 2) {
                    e.preventDefault();
                    this.executeSearch(this.input.value.trim());
                }
                return;
            }

            switch (e.key) {
                case "ArrowDown":
                    e.preventDefault();
                    if (this.items.length === 0) return;
                    this.activeIndex = (this.activeIndex + 1) % this.items.length;
                    this.updateActiveItem();
                    break;

                case "ArrowUp":
                    e.preventDefault();
                    if (this.items.length === 0) return;
                    this.activeIndex = (this.activeIndex - 1 + this.items.length) % this.items.length;
                    this.updateActiveItem();
                    break;

                case "Enter":
                    if (this.activeIndex >= 0 && this.activeIndex < this.items.length) {
                        e.preventDefault();
                        this.selectItem(this.items[this.activeIndex]);
                    } else if (this.items.length > 0) {
                        e.preventDefault();
                        this.selectItem(this.items[0]);
                    }
                    break;

                case "Escape":
                    e.preventDefault();
                    this.close();
                    break;
            }
        }

        updateActiveItem() {
            const elements = this.dropdown.querySelectorAll(".suggestion-item");
            elements.forEach((el, idx) => {
                const isActive = idx === this.activeIndex;
                el.classList.toggle("is-active", isActive);
                el.setAttribute("aria-selected", isActive ? "true" : "false");
                if (isActive) {
                    el.scrollIntoView({ block: "nearest", behavior: "smooth" });
                    // Update inline bar to match currently highlighted item
                    if (this.items[idx]) {
                        this.renderInlineBar(this.items[idx]);
                    }
                }
            });
        }

        render(items, query, isSearchingPubChem) {
            this.dropdown.innerHTML = "";

            if (!items || items.length === 0) {
                if (isSearchingPubChem) {
                    this.dropdown.innerHTML = `
                        <div class="suggestion-loading-state">
                            <span class="suggestion-spinner" aria-hidden="true"></span>
                            <span>Searching chemical libraries for "<strong>${escapeHtml(query)}</strong>"…</span>
                        </div>
                    `;
                } else {
                    this.dropdown.innerHTML = `
                        <div class="suggestion-empty-state">
                            <div class="empty-icon" aria-hidden="true">⌬</div>
                            <p class="empty-title">No matching molecules found for "<strong>${escapeHtml(query)}</strong>"</p>
                            <p class="empty-subtitle">You can continue typing a custom SMILES or full chemical name directly.</p>
                        </div>
                    `;
                }
                return;
            }

            const header = document.createElement("div");
            header.className = "suggestion-dropdown-header";
            header.innerHTML = `
                <span class="dropdown-header-title">Matching Molecules (${items.length})</span>
                ${isSearchingPubChem ? '<span class="dropdown-header-badge"><span class="badge-dot"></span> Checking PubChem</span>' : '<span class="dropdown-header-hint">↑↓ keys &amp; Enter/Tab to select</span>'}
            `;
            this.dropdown.appendChild(header);

            const listContainer = document.createElement("div");
            listContainer.className = "suggestion-list";

            items.forEach((item, index) => {
                const itemEl = document.createElement("div");
                itemEl.className = "suggestion-item";
                itemEl.setAttribute("role", "option");
                itemEl.setAttribute("id", `suggestion-item-${index}`);
                itemEl.setAttribute("aria-selected", index === this.activeIndex ? "true" : "false");

                // Target badge styling
                let targetBadge = "";
                if (item.target) {
                    const isEgfr = item.target.toUpperCase().includes("EGFR");
                    const isCox2 = item.target.toUpperCase().includes("COX-2");
                    const badgeClass = isEgfr ? "badge-egfr" : (isCox2 ? "badge-cox2" : "badge-target");
                    targetBadge = `<span class="suggestion-badge ${badgeClass}">🎯 ${escapeHtml(item.target)}</span>`;
                }

                // Formula display
                let formulaHtml = "";
                if (item.formula) {
                    formulaHtml = `<span class="suggestion-formula" title="Molecular Formula">${formatMolecularFormula(item.formula)}</span>`;
                }

                // Category tag
                let classTag = "";
                if (item.classType) {
                    classTag = `<span class="suggestion-class-tag">${escapeHtml(item.classType)}</span>`;
                }

                // Matched synonym note
                let synonymNote = "";
                if (item.matchedSynonym) {
                    synonymNote = `<span class="suggestion-synonym">matches <em>${escapeHtml(item.matchedSynonym)}</em></span>`;
                }

                itemEl.innerHTML = `
                    <div class="suggestion-icon" aria-hidden="true">⌬</div>
                    <div class="suggestion-content">
                        <div class="suggestion-top-row">
                            <span class="suggestion-name">${highlightMatchingText(item.name, query)}</span>
                            ${formulaHtml}
                            ${synonymNote}
                        </div>
                        <div class="suggestion-meta-row">
                            ${targetBadge}
                            ${classTag}
                        </div>
                    </div>
                    <div class="suggestion-action" aria-hidden="true">
                        <span>Select</span>
                        <span class="action-arrow">↵</span>
                    </div>
                `;

                itemEl.addEventListener("mouseenter", () => {
                    this.activeIndex = index;
                    this.updateActiveItem();
                });

                itemEl.addEventListener("click", (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.selectItem(item);
                });

                listContainer.appendChild(itemEl);
            });

            this.dropdown.appendChild(listContainer);
        }

        selectItem(item) {
            this.input.value = item.name;
            this.close();
            this.clearInlineBar();

            // Trigger consumer callback
            if (typeof this.onSelect === "function") {
                this.onSelect(item);
            }
        }

        open() {
            this.isOpen = true;
            this.dropdown.removeAttribute("hidden");
            this.dropdown.style.display = "block";
            this.input.setAttribute("aria-expanded", "true");
            if (this.container && this.container.classList) {
                this.container.classList.add("has-dropdown-open");
            }
        }

        close() {
            this.isOpen = false;
            this.dropdown.setAttribute("hidden", "");
            this.dropdown.style.display = "none";
            this.activeIndex = -1;
            this.input.setAttribute("aria-expanded", "false");
            if (this.container && this.container.classList) {
                this.container.classList.remove("has-dropdown-open");
            }
            if (this.debounceTimer) clearTimeout(this.debounceTimer);
            if (this.abortController) this.abortController.abort();
        }
    }

    // Factory helper
    function initMoleculeAutocomplete(options) {
        return new MoleculeAutocomplete(options);
    }

    // Auto-initialize on DOM ready for seamless integration
    function autoInit() {
        const smilesInput = document.getElementById("smiles-input");
        const searchContainer = document.getElementById("molecule-search-container") || smilesInput?.parentElement;
        const searchDropdown = document.getElementById("molecule-suggestions-dropdown");
        const targetSelect = document.getElementById("target-select");

        if (smilesInput && !window._bamiAutocompleteInstance) {
            window._bamiAutocompleteInstance = new MoleculeAutocomplete({
                input: smilesInput,
                container: searchContainer,
                dropdown: searchDropdown,
                targetSelect: targetSelect,
                onSelect: async (molecule) => {
                    smilesInput.value = molecule.name;

                    // Automatically select known target
                    if (targetSelect && molecule.target) {
                        if (molecule.target.toUpperCase().includes("EGFR")) {
                            targetSelect.value = "EGFR";
                        } else if (molecule.target.toUpperCase().includes("COX-2")) {
                            targetSelect.value = "COX-2";
                        }
                    }

                    const predictionMessage = document.getElementById("prediction-message");
                    if (predictionMessage) {
                        predictionMessage.textContent = `Selected ${molecule.name} (${molecule.formula ? molecule.formula + " · " : ""}${molecule.target ? molecule.target : "Bioactive Target"}). Ready to predict.`;
                        predictionMessage.className = "prediction-message success";
                    }

                    // Render molecular structure if RDKit and SMILES available
                    if (typeof window.renderMolecule === "function" && molecule.smiles) {
                        try {
                            await window.renderMolecule(molecule.smiles);
                            const structureStatus = document.getElementById("structure-status");
                            if (structureStatus) {
                                structureStatus.textContent = `${molecule.name} structure preview ready.`;
                            }
                        } catch (err) {
                            console.warn("Could not preview structure:", err);
                        }
                    }
                }
            });
            window.moleculeAutocomplete = window._bamiAutocompleteInstance;
        }

        // Also check drug-likeness input if on drug-likeness page
        const drugInput = document.getElementById("drug-smiles-input");
        const drugContainer = document.getElementById("drug-search-container") || drugInput?.parentElement;
        const drugDropdown = document.getElementById("drug-suggestions-dropdown");

        if (drugInput && !window._bamiDrugAutocompleteInstance) {
            window._bamiDrugAutocompleteInstance = new MoleculeAutocomplete({
                input: drugInput,
                container: drugContainer,
                dropdown: drugDropdown,
                onSelect: (molecule) => {
                    drugInput.value = molecule.name;
                }
            });
        }

        // Also check docking input if on docking page
        const dockingInput = document.getElementById("docking-smiles-input");
        const dockingContainer = document.getElementById("docking-search-container") || dockingInput?.parentElement;
        const dockingDropdown = document.getElementById("docking-suggestions-dropdown");

        if (dockingInput && !window._bamiDockingAutocompleteInstance) {
            window._bamiDockingAutocompleteInstance = new MoleculeAutocomplete({
                input: dockingInput,
                container: dockingContainer,
                dropdown: dockingDropdown,
                onSelect: (molecule) => {
                    dockingInput.value = molecule.name;
                    if (molecule.target && typeof window.BAMI?.setDockingTarget === "function") {
                        window.BAMI.setDockingTarget(molecule.target);
                    }
                    document.querySelectorAll(".preset-pill, .lead-pill").forEach(p => {
                        const isMatch = (p.dataset.name && p.dataset.name.toLowerCase() === molecule.name.toLowerCase()) ||
                                        (p.dataset.smiles && molecule.smiles && p.dataset.smiles === molecule.smiles);
                        p.classList.toggle("active", !!isMatch);
                    });
                }
            });
            window.dockingAutocomplete = window._bamiDockingAutocompleteInstance;
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", autoInit);
    } else {
        autoInit();
    }
    if (typeof window !== "undefined" && typeof window.addEventListener === "function") {
        window.addEventListener("load", autoInit);
    }

    // Export to global scope
    global.BAMI = global.BAMI || {};
    global.BAMI.BIOACTIVE_MOLECULES = BIOACTIVE_MOLECULES;
    global.BAMI.findBioactiveMoleculeByName = findBioactiveMoleculeByName;
    global.BAMI.findBioactiveMoleculeBySmiles = findBioactiveMoleculeBySmiles;
    global.BAMI.initMoleculeAutocomplete = initMoleculeAutocomplete;
    global.initMoleculeAutocomplete = initMoleculeAutocomplete;

})(typeof window !== "undefined" ? window : this);
