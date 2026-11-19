/* =========================================================
   BAMI PREDICTION HISTORY SERVICE
   Local storage persistence for up to 50 molecule predictions.
   ========================================================= */

(function (window) {
    'use strict';

    const STORAGE_KEY = 'bami_prediction_history';
    const MAX_ENTRIES = 50;

    const BAMIHistory = {
        STORAGE_KEY: STORAGE_KEY,
        MAX_ENTRIES: MAX_ENTRIES,

        /**
         * Retrieve all saved history entries, sorted newest first.
         * Gracefully handles corrupted data, older schema versions, and missing storage.
         * @returns {Array} List of prediction objects (at most 50)
         */
        getHistory: function () {
            try {
                if (typeof window.localStorage === 'undefined') {
                    console.warn('localStorage is not available in this environment.');
                    return [];
                }
                const raw = window.localStorage.getItem(STORAGE_KEY);
                if (!raw) return [];
                const parsed = JSON.parse(raw);
                if (!Array.isArray(parsed)) return [];

                // Sanitize and normalize entries, ensuring valid objects
                return parsed
                    .filter(function (entry) {
                        return entry && (typeof entry === 'object');
                    })
                    .slice(0, MAX_ENTRIES);
            } catch (err) {
                console.warn('Error reading BAMI history from localStorage:', err);
                return [];
            }
        },

        /**
         * Add a new successful prediction to the history.
         * Automatically trims the list to keep at most 50 entries, removing the oldest.
         * @param {Object} predictionData Data from FastAPI backend prediction response
         * @param {Object} [meta] Additional metadata like compoundName, raw input
         * @returns {Object|null} The saved entry or null on error
         */
        addPrediction: function (predictionData, meta) {
            try {
                if (!predictionData || typeof predictionData !== 'object') {
                    return null;
                }

                meta = meta || {};

                // Determine prediction label
                const predictionText =
                    typeof predictionData.prediction === 'string'
                        ? predictionData.prediction
                        : typeof predictionData.class_id === 'number'
                            ? (predictionData.class_id === 1 ? 'Active' : 'Inactive')
                            : 'Unknown';

                // Do not record failed/unknown predictions
                if (predictionText === 'Unknown') {
                    return null;
                }

                const smiles =
                    predictionData.canonical_smiles ||
                    predictionData.smiles ||
                    meta.smiles ||
                    '';

                if (!smiles) {
                    return null;
                }

                const target =
                    predictionData.target ||
                    meta.target ||
                    'Unknown Target';

                const descriptors =
                    (predictionData.molecular_descriptors && typeof predictionData.molecular_descriptors === 'object')
                        ? predictionData.molecular_descriptors
                        : (predictionData.descriptors && typeof predictionData.descriptors === 'object')
                            ? predictionData.descriptors
                            : null;

                const score = Number.isFinite(Number(predictionData.probability_active))
                    ? Number(predictionData.probability_active)
                    : null;

                const scoreType = predictionData.probability_type ||
                    (target === 'EGFR' ? 'calibrated_probability' : 'model_probability');

                const threshold = Number.isFinite(Number(predictionData.classification_threshold))
                    ? Number(predictionData.classification_threshold)
                    : 0.5;

                const entry = {
                    id: 'pred_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7),
                    timestamp: new Date().toISOString(),
                    input: meta.rawInput || meta.input || smiles,
                    compound_name: meta.compoundName || meta.name || '',
                    smiles: smiles,
                    target: target,
                    target_uniprot: predictionData.target_uniprot || (target === 'EGFR' ? 'P00533' : (target === 'COX-2' ? 'P35354' : '')),
                    prediction: predictionText,
                    score: score,
                    score_type: scoreType,
                    threshold: threshold,
                    model: predictionData.model || (target === 'EGFR' ? 'Tuned EGFR XGBoost' : 'Final XGBoost'),
                    descriptors: descriptors ? {
                        mw: descriptors.molecular_weight ?? descriptors.Molecular_Weight ?? null,
                        logp: descriptors.logp ?? descriptors.LogP ?? null,
                        tpsa: descriptors.tpsa ?? descriptors.TPSA ?? null,
                        hbd: descriptors.h_bond_donors ?? descriptors.HBD ?? null,
                        hba: descriptors.h_bond_acceptors ?? descriptors.HBA ?? null,
                        rotatable_bonds: descriptors.rotatable_bonds ?? descriptors.Rotatable_Bonds ?? null
                    } : null
                };

                const history = this.getHistory();
                // Prepend new entry
                history.unshift(entry);

                // Keep at most MAX_ENTRIES (50)
                const trimmed = history.slice(0, MAX_ENTRIES);

                window.localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
                return entry;
            } catch (err) {
                console.warn('Error saving prediction to localStorage:', err);
                return null;
            }
        },

        /**
         * Remove a single entry by ID.
         */
        removeEntry: function (id) {
            try {
                const history = this.getHistory();
                const filtered = history.filter(function (item) {
                    return item.id !== id;
                });
                window.localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
                return true;
            } catch (err) {
                console.warn('Error removing history entry:', err);
                return false;
            }
        },

        /**
         * Clear all saved history entries from localStorage.
         */
        clearHistory: function () {
            try {
                if (typeof window.localStorage !== 'undefined') {
                    window.localStorage.removeItem(STORAGE_KEY);
                    return true;
                }
                return false;
            } catch (err) {
                console.warn('Error clearing history:', err);
                return false;
            }
        },

        /**
         * Format ISO timestamp to a human-readable local string.
         */
        formatDate: function (isoString) {
            if (!isoString) return '--';
            try {
                const date = new Date(isoString);
                if (isNaN(date.getTime())) return isoString;
                return date.toLocaleString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch (e) {
                return isoString;
            }
        }
    };

    window.BAMIHistory = BAMIHistory;

})(typeof window !== 'undefined' ? window : this);
