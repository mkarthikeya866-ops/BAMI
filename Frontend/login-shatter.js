/* =========================================================
   BAMI MOLECULAR LOGIN SHATTER PORTAL
   =========================================================
   Pure Vanilla JavaScript & HTML5 Canvas
   Zero dependencies. Hardware accelerated 60fps physics.

   Cinematic Sequence:
   1. Deep quantum void overlay appears (#0A0518).
   2. Gigantic 3D-styled 'BAMI' typography falls from the top with gravity.
   3. Central focal impact creates camera shake, shockwaves, and photon flash.
   4. The 'BAMI' text shatters into realistic chemical molecules:
      - Benzene / aromatic rings (6-carbon rings with delocalized bonds)
      - Diatomic & triatomic molecules with covalent bond rods
      - Colored CPK element spheres (C, N, O, S, H)
      - Chemical formula floaters (COX-2, EGFR, —OH, =O, NH2)
      - Glowing quantum spark trails
   5. Molecular cloud disperses outward into ambient space,
      and smoothly opens the actual application workspace.
   ========================================================= */

let isAnimationRunning = false;

// CPK Color Palette
const CPK_COLORS = {
    C: { color: "#A855F7", darkColor: "#581C87", glow: "rgba(168, 85, 247, 0.5)" }, // Carbon (Violet-Slate)
    N: { color: "#38BDF8", darkColor: "#0369A1", glow: "rgba(56, 189, 248, 0.5)" }, // Nitrogen (Sky Blue)
    O: { color: "#F43F5E", darkColor: "#9F1239", glow: "rgba(244, 63, 94, 0.5)" },  // Oxygen (Crimson)
    S: { color: "#FACC15", darkColor: "#854D0E", glow: "rgba(250, 204, 21, 0.5)" }, // Sulfur (Amber)
    H: { color: "#FFFFFF", darkColor: "#94A3B8", glow: "rgba(255, 255, 255, 0.4)" }  // Hydrogen (White)
};

const FORMULA_LIST = [
    "⌬ Benzene", "COX-2", "EGFR", "—OH", "=O",
    "—NH₂", "—COOH", "—CH₃", "C₆H₆", "XGBoost", "pIC₅₀"
];

/**
 * Synthesize cinematic bass thud and crystal shatter using Web Audio API
 */
function playImpactAudio() {
    try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();
        if (ctx.state === "suspended") {
            ctx.resume().catch(() => {});
        }

        const now = ctx.currentTime;

        // 1. Heavy cinematic bass drop
        const osc = ctx.createOscillator();
        const oscGain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(150, now);
        osc.frequency.exponentialRampToValueAtTime(30, now + 0.65);
        oscGain.gain.setValueAtTime(0.65, now);
        oscGain.gain.exponentialRampToValueAtTime(0.001, now + 0.7);
        osc.connect(oscGain);
        oscGain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.7);

        // 2. High-frequency molecular shatter burst
        const bufferSize = Math.floor(ctx.sampleRate * 0.4);
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const output = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            output[i] = (Math.random() * 2 - 1) * Math.exp(-i / (ctx.sampleRate * 0.08));
        }

        const noise = ctx.createBufferSource();
        noise.buffer = buffer;

        const bandpass = ctx.createBiquadFilter();
        bandpass.type = "bandpass";
        bandpass.frequency.setValueAtTime(2200, now);
        bandpass.frequency.exponentialRampToValueAtTime(450, now + 0.45);
        bandpass.Q.value = 2.8;

        const noiseGain = ctx.createGain();
        noiseGain.gain.setValueAtTime(0.35, now);
        noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);

        noise.connect(bandpass);
        bandpass.connect(noiseGain);
        noiseGain.connect(ctx.destination);
        noise.start(now);
        noise.stop(now + 0.45);
    } catch (_) {
        // Audio policy blocked or unsupported - continue silently
    }
}

/**
 * Universal cross-browser safe rounded rectangle path
 */
function drawSafeRoundRect(ctx, x, y, w, h, r) {
    const radius = Math.max(0, Math.min(r, Math.abs(h) / 2, Math.abs(w) / 2));
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + w - radius, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
    ctx.lineTo(x + w, y + h - radius);
    ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
    ctx.lineTo(x + radius, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
}

/**
 * Main Trigger Function
 */
function trigger(onComplete, isPreview = false) {
    if (isAnimationRunning) {
        console.warn("BAMI shatter animation already running.");
        return;
    }
    isAnimationRunning = true;

    // Safety timeout: Ensure page is NEVER stuck
    let safetyTimeout = setTimeout(() => {
        cleanup();
        if (typeof onComplete === "function") onComplete();
    }, 3800);

    // Container overlay
    const overlay = document.createElement("div");
    overlay.id = "bami-login-portal-overlay";
    overlay.style.cssText = `
        position: fixed;
        inset: 0;
        width: 100vw;
        height: 100vh;
        z-index: 999999;
        background: #090414;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        opacity: 0;
        transition: opacity 0.24s cubic-bezier(0.16, 1, 0.3, 1);
        pointer-events: auto;
        cursor: wait;
    `;

    const canvas = document.createElement("canvas");
    canvas.style.cssText = `
        display: block;
        width: 100%;
        height: 100%;
        position: absolute;
        top: 0;
        left: 0;
    `;
    overlay.appendChild(canvas);
    document.body.appendChild(overlay);

    // Force reflow for fade in
    void overlay.offsetWidth;
    overlay.style.opacity = "1";

    const ctx = canvas.getContext("2d");
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    function handleResize() {
        width = canvas.width = window.innerWidth || 1200;
        height = canvas.height = window.innerHeight || 800;
    }
    if (typeof window !== "undefined" && typeof window.addEventListener === "function") {
        window.addEventListener("resize", handleResize);
    }

    // Simulation parameters
    const centerX = width / 2;
    const targetY = height / 2;
    const fontSize = Math.max(90, Math.min(width * 0.18, 170));

    // State Machine
    let state = "FALLING"; // "FALLING" -> "SHATTERING" -> "REVEAL"
    let letterY = -fontSize * 1.6;
    let letterVy = 2.5;
    const gravity = 1.38;
    let impactTime = 0;
    let shakeFrames = 0;

    // Particle systems
    const trailSparks = [];
    const shockwaves = [];
    const molecules = [];
    const atoms = [];
    const formulaBadges = [];
    const quantumDust = [];

    // Helper: Random in range
    const rand = (min, max) => min + Math.random() * (max - min);

    // Initialize Molecular Entities upon impact
    function explodeIntoMolecules() {
        playImpactAudio();
        shakeFrames = 12;

        // 1. Expanding shockwave rings
        shockwaves.push(
            { x: centerX, y: targetY, radius: 20, maxRadius: Math.max(width, height) * 0.88, alpha: 1, speed: 28, width: 9 },
            { x: centerX, y: targetY, radius: 10, maxRadius: Math.max(width, height) * 0.65, alpha: 0.85, speed: 20, width: 5 }
        );

        // 2. Benzene & Aromatic Rings (16 rings)
        for (let i = 0; i < 16; i++) {
            const angle = rand(0, Math.PI * 2);
            const speed = rand(7, 19);
            molecules.push({
                type: "benzene",
                x: centerX + rand(-40, 40),
                y: targetY + rand(-30, 30),
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed - rand(1, 4),
                rot: rand(0, Math.PI * 2),
                vrot: rand(-0.09, 0.09),
                radius: rand(18, 32),
                color: i % 2 === 0 ? "#C084FC" : "#38BDF8",
                hasCircle: Math.random() > 0.4,
                subText: i % 3 === 0 ? (i % 2 === 0 ? "OH" : "NH₂") : "",
                alpha: 1
            });
        }

        // 3. Diatomic & Triatomic Bonded Clusters (24 clusters)
        for (let i = 0; i < 24; i++) {
            const angle = rand(0, Math.PI * 2);
            const speed = rand(6, 18);
            const isTri = Math.random() > 0.5;
            const bondLen = rand(22, 34);

            const atomKeys = ["C", "N", "O", "S", "H"];
            const c1 = CPK_COLORS[atomKeys[Math.floor(Math.random() * atomKeys.length)]];
            const c2 = CPK_COLORS[atomKeys[Math.floor(Math.random() * atomKeys.length)]];
            const c3 = CPK_COLORS[atomKeys[Math.floor(Math.random() * atomKeys.length)]];

            const clusterAtoms = [
                { rx: -bondLen / 2, ry: 0, radius: rand(8, 12), ...c1, symbol: "C" },
                { rx: bondLen / 2, ry: 0, radius: rand(8, 12), ...c2, symbol: "O" }
            ];
            if (isTri) {
                clusterAtoms.push({ rx: 0, ry: -bondLen * 0.86, radius: rand(7, 11), ...c3, symbol: "N" });
            }

            molecules.push({
                type: "cluster",
                x: centerX + rand(-50, 50),
                y: targetY + rand(-35, 35),
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed - rand(2, 5),
                rot: rand(0, Math.PI * 2),
                vrot: rand(-0.12, 0.12),
                atoms: clusterAtoms,
                isDouble: Math.random() > 0.6,
                alpha: 1
            });
        }

        // 4. Single CPK Atom Spheres (38 spheres)
        const keys = ["C", "N", "O", "S", "H"];
        for (let i = 0; i < 38; i++) {
            const sym = keys[Math.floor(Math.random() * keys.length)];
            const data = CPK_COLORS[sym];
            const angle = rand(0, Math.PI * 2);
            const speed = rand(5, 22);
            atoms.push({
                x: centerX + rand(-40, 40),
                y: targetY + rand(-40, 40),
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed - rand(1, 6),
                radius: sym === "H" ? 8 : rand(11, 16),
                symbol: sym,
                ...data,
                alpha: 1
            });
        }

        // 5. Floating Chemical Formula Badges (12 badges)
        for (let i = 0; i < 12; i++) {
            const text = FORMULA_LIST[i % FORMULA_LIST.length];
            const angle = rand(0, Math.PI * 2);
            const speed = rand(5, 14);
            formulaBadges.push({
                x: centerX,
                y: targetY,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed - rand(2, 5),
                rot: rand(-0.2, 0.2),
                vrot: rand(-0.02, 0.02),
                formula: text,
                alpha: 1
            });
        }

        // 6. Quantum Spark Dust (80 glowing particles)
        for (let i = 0; i < 80; i++) {
            const angle = rand(0, Math.PI * 2);
            const speed = rand(4, 26);
            quantumDust.push({
                x: centerX,
                y: targetY,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                radius: rand(1.5, 3.8),
                color: Math.random() > 0.5 ? "#00E5FF" : (Math.random() > 0.5 ? "#A78BFA" : "#F43F5E"),
                alpha: 1,
                decay: rand(0.012, 0.024)
            });
        }
    }

    let animId;
    function cleanup() {
        if (safetyTimeout) {
            clearTimeout(safetyTimeout);
            safetyTimeout = null;
        }
        cancelAnimationFrame(animId);
        if (typeof window !== "undefined" && typeof window.removeEventListener === "function") {
            window.removeEventListener("resize", handleResize);
        }
        overlay.remove();
        isAnimationRunning = false;
    }

    function renderFrame(timestamp) {
        try {
            const now = typeof timestamp === "number" ? timestamp : performance.now();
            animId = requestAnimationFrame(renderFrame);

            // Screen Shake calculation
            let shakeX = 0;
            let shakeY = 0;
            if (shakeFrames > 0) {
                shakeX = (Math.random() - 0.5) * shakeFrames * 1.8;
                shakeY = (Math.random() - 0.5) * shakeFrames * 1.8;
                shakeFrames--;
            }

            // Clear Canvas
            ctx.save();
            ctx.translate(shakeX, shakeY);
            ctx.fillStyle = "#0A0518";
            ctx.fillRect(0, 0, width, height);

            // Draw Subtle Quantum Grid
            ctx.strokeStyle = "rgba(124, 58, 237, 0.08)";
            ctx.lineWidth = 1;
            const gridSpacing = 60;
            for (let x = 0; x < width; x += gridSpacing) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, height);
                ctx.stroke();
            }
            for (let y = 0; y < height; y += gridSpacing) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
                ctx.stroke();
            }

            // Central radial glow
            const centerGlow = ctx.createRadialGradient(centerX, targetY, 10, centerX, targetY, width * 0.6);
            centerGlow.addColorStop(0, "rgba(101, 31, 255, 0.22)");
            centerGlow.addColorStop(0.5, "rgba(49, 16, 102, 0.12)");
            centerGlow.addColorStop(1, "rgba(10, 5, 24, 0)");
            ctx.fillStyle = centerGlow;
            ctx.fillRect(0, 0, width, height);

            // ==========================================
            // PHASE 1: FALLING BAMI TEXT
            // ==========================================
            if (state === "FALLING") {
                letterVy += gravity;
                letterY += letterVy;

                // Add trailing speed sparks
                for (let i = 0; i < 4; i++) {
                    trailSparks.push({
                        x: centerX + rand(-fontSize * 1.2, fontSize * 1.2),
                        y: letterY + rand(-fontSize * 0.2, fontSize * 0.2),
                        vx: rand(-1.5, 1.5),
                        vy: -letterVy * 0.4 + rand(-2, 2),
                        radius: rand(1.5, 3.5),
                        color: Math.random() > 0.5 ? "#A78BFA" : "#00E5FF",
                        alpha: 0.9
                    });
                }

                // Draw trail sparks
                for (let i = trailSparks.length - 1; i >= 0; i--) {
                    const sp = trailSparks[i];
                    sp.x += sp.vx;
                    sp.y += sp.vy;
                    sp.alpha -= 0.035;
                    if (sp.alpha <= 0) {
                        trailSparks.splice(i, 1);
                        continue;
                    }
                    ctx.save();
                    ctx.fillStyle = sp.color;
                    ctx.globalAlpha = sp.alpha;
                    ctx.beginPath();
                    ctx.arc(sp.x, sp.y, sp.radius, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.restore();
                }

                // Target landing shadow ring
                const distanceToTarget = Math.max(0, targetY - letterY);
                const shadowScale = Math.max(0.2, 1 - distanceToTarget / (height * 0.8));
                ctx.save();
                const shadowGrad = ctx.createRadialGradient(centerX, targetY + fontSize * 0.45, 1, centerX, targetY + fontSize * 0.45, fontSize * 1.4 * shadowScale);
                shadowGrad.addColorStop(0, `rgba(167, 139, 250, ${0.5 * shadowScale})`);
                shadowGrad.addColorStop(1, "rgba(167, 139, 250, 0)");
                ctx.fillStyle = shadowGrad;
                ctx.beginPath();
                ctx.ellipse(centerX, targetY + fontSize * 0.45, fontSize * 1.4 * shadowScale, fontSize * 0.3 * shadowScale, 0, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();

                // Draw Huge Falling BAMI text
                ctx.save();
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.font = `900 ${fontSize}px system-ui, -apple-system, 'Inter', 'Segoe UI', sans-serif`;

                // 3D Shadow layer
                ctx.fillStyle = "rgba(48, 14, 99, 0.9)";
                ctx.fillText("BAMI", centerX + 6, letterY + 8);

                // Neon Outer Glow
                ctx.shadowColor = "#8B5CF6";
                ctx.shadowBlur = 32;
                ctx.strokeStyle = "rgba(167, 139, 250, 0.9)";
                ctx.lineWidth = 4;
                ctx.strokeText("BAMI", centerX, letterY);

                // Face Gradient
                const textGrad = ctx.createLinearGradient(0, letterY - fontSize * 0.5, 0, letterY + fontSize * 0.5);
                textGrad.addColorStop(0, "#FFFFFF");
                textGrad.addColorStop(0.35, "#DDD6FE");
                textGrad.addColorStop(0.75, "#8B5CF6");
                textGrad.addColorStop(1, "#00E5FF");
                ctx.fillStyle = textGrad;
                ctx.fillText("BAMI", centerX, letterY);

                ctx.restore();

                // Impact trigger check
                if (letterY >= targetY) {
                    state = "SHATTERING";
                    impactTime = now;
                    explodeIntoMolecules();
                }
            }

            // ==========================================
            // PHASE 2 & 3: MOLECULAR SHATTER & DISPERSION
            // ==========================================
            if (state === "SHATTERING" || state === "REVEAL") {
                const elapsedShatter = now - impactTime;

                // 1. Draw Expanding Shockwaves
                for (let i = shockwaves.length - 1; i >= 0; i--) {
                    const sw = shockwaves[i];
                    sw.radius += sw.speed;
                    sw.alpha *= 0.95;
                    sw.width *= 0.97;

                    if (sw.alpha <= 0.01) {
                        shockwaves.splice(i, 1);
                        continue;
                    }

                    ctx.save();
                    ctx.beginPath();
                    ctx.arc(sw.x, sw.y, sw.radius, 0, Math.PI * 2);
                    ctx.strokeStyle = `rgba(0, 229, 255, ${sw.alpha * 0.8})`;
                    ctx.lineWidth = Math.max(1, sw.width);
                    ctx.shadowColor = "#00E5FF";
                    ctx.shadowBlur = 18;
                    ctx.stroke();

                    // Inner violet ring
                    ctx.beginPath();
                    ctx.arc(sw.x, sw.y, sw.radius * 0.86, 0, Math.PI * 2);
                    ctx.strokeStyle = `rgba(167, 139, 250, ${sw.alpha * 0.6})`;
                    ctx.lineWidth = Math.max(1, sw.width * 0.6);
                    ctx.stroke();
                    ctx.restore();
                }

                // 2. Draw Benzene and Cluster Molecules
                for (const m of molecules) {
                    m.x += m.vx;
                    m.y += m.vy;
                    m.rot += m.vrot;
                    m.vx *= 0.985; // Atmospheric resistance
                    m.vy *= 0.985;
                    if (elapsedShatter > 1600) m.alpha -= 0.018;

                    if (m.alpha <= 0) continue;

                    ctx.save();
                    ctx.globalAlpha = Math.max(0, m.alpha);

                    if (m.type === "benzene") {
                        // Draw 6-Membered Aromatic Ring
                        ctx.save();
                        ctx.translate(m.x, m.y);
                        ctx.rotate(m.rot);

                        // Hexagon border
                        ctx.beginPath();
                        for (let i = 0; i < 6; i++) {
                            const a = (Math.PI / 3) * i;
                            const px = m.radius * Math.cos(a);
                            const py = m.radius * Math.sin(a);
                            if (i === 0) ctx.moveTo(px, py);
                            else ctx.lineTo(px, py);
                        }
                        ctx.closePath();
                        ctx.strokeStyle = m.color;
                        ctx.lineWidth = 2.6;
                        ctx.shadowColor = m.color;
                        ctx.shadowBlur = 10;
                        ctx.stroke();

                        // Inner delocalized ring
                        if (m.hasCircle) {
                            ctx.beginPath();
                            ctx.arc(0, 0, m.radius * 0.58, 0, Math.PI * 2);
                            ctx.strokeStyle = "rgba(192, 132, 252, 0.75)";
                            ctx.lineWidth = 1.8;
                            ctx.stroke();
                        } else {
                            // 3 Alternating Double Bonds
                            for (let i = 0; i < 3; i++) {
                                const a1 = (Math.PI / 3) * (i * 2);
                                const a2 = (Math.PI / 3) * (i * 2 + 1);
                                const inR = m.radius * 0.76;
                                ctx.beginPath();
                                ctx.moveTo(inR * Math.cos(a1), inR * Math.sin(a1));
                                ctx.lineTo(inR * Math.cos(a2), inR * Math.sin(a2));
                                ctx.strokeStyle = "rgba(192, 132, 252, 0.85)";
                                ctx.lineWidth = 1.6;
                                ctx.stroke();
                            }
                        }

                        // Vertex Carbon Atoms
                        for (let i = 0; i < 6; i++) {
                            const a = (Math.PI / 3) * i;
                            ctx.beginPath();
                            ctx.arc(m.radius * Math.cos(a), m.radius * Math.sin(a), 2.8, 0, Math.PI * 2);
                            ctx.fillStyle = "#FFFFFF";
                            ctx.fill();
                        }

                        // Substituent attachment
                        if (m.subText) {
                            ctx.beginPath();
                            ctx.moveTo(0, -m.radius);
                            ctx.lineTo(0, -m.radius - 12);
                            ctx.strokeStyle = m.color;
                            ctx.lineWidth = 2;
                            ctx.stroke();

                            ctx.fillStyle = "#38BDF8";
                            ctx.font = "bold 12px system-ui, sans-serif";
                            ctx.textAlign = "center";
                            ctx.textBaseline = "bottom";
                            ctx.fillText(m.subText, 0, -m.radius - 14);
                        }

                        ctx.restore();
                    } else if (m.type === "cluster") {
                        // Draw Diatomic/Triatomic Molecule with Covalent Bonds
                        ctx.save();
                        ctx.translate(m.x, m.y);
                        ctx.rotate(m.rot);

                        // Bond Sticks
                        for (let i = 0; i < m.atoms.length - 1; i++) {
                            const a1 = m.atoms[i];
                            const a2 = m.atoms[i + 1];
                            ctx.beginPath();
                            ctx.moveTo(a1.rx, a1.ry);
                            ctx.lineTo(a2.rx, a2.ry);
                            ctx.strokeStyle = "rgba(226, 232, 240, 0.75)";
                            ctx.lineWidth = m.isDouble ? 5.5 : 3.2;
                            ctx.stroke();

                            if (m.isDouble) {
                                ctx.beginPath();
                                ctx.moveTo(a1.rx, a1.ry);
                                ctx.lineTo(a2.rx, a2.ry);
                                ctx.strokeStyle = "#090414";
                                ctx.lineWidth = 1.6;
                                ctx.stroke();
                            }
                        }

                        // Atom Spheres
                        for (const at of m.atoms) {
                            ctx.save();
                            ctx.translate(at.rx, at.ry);

                            // Glow
                            ctx.beginPath();
                            ctx.arc(0, 0, at.radius * 2.2, 0, Math.PI * 2);
                            ctx.fillStyle = at.glow;
                            ctx.fill();

                            // Sphere ball
                            const grad = ctx.createRadialGradient(-at.radius * 0.3, -at.radius * 0.3, 1, 0, 0, at.radius);
                            grad.addColorStop(0, "#FFFFFF");
                            grad.addColorStop(0.3, at.color);
                            grad.addColorStop(1, at.darkColor);
                            ctx.fillStyle = grad;
                            ctx.beginPath();
                            ctx.arc(0, 0, at.radius, 0, Math.PI * 2);
                            ctx.fill();

                            // Symbol
                            ctx.fillStyle = "#FFFFFF";
                            ctx.font = `bold ${Math.round(at.radius * 1.05)}px system-ui, sans-serif`;
                            ctx.textAlign = "center";
                            ctx.textBaseline = "middle";
                            ctx.fillText(at.symbol, 0, 1);

                            ctx.restore();
                        }
                        ctx.restore();
                    }

                    ctx.restore();
                }

                // 3. Draw Single CPK Atom Spheres
                for (const at of atoms) {
                    at.x += at.vx;
                    at.y += at.vy;
                    at.vx *= 0.985;
                    at.vy *= 0.985;
                    if (elapsedShatter > 1600) at.alpha -= 0.018;

                    if (at.alpha <= 0) continue;

                    ctx.save();
                    ctx.globalAlpha = Math.max(0, at.alpha);
                    ctx.translate(at.x, at.y);

                    // Glow aura
                    ctx.beginPath();
                    ctx.arc(0, 0, at.radius * 2.3, 0, Math.PI * 2);
                    ctx.fillStyle = at.glow;
                    ctx.fill();

                    // Shaded sphere
                    const grad = ctx.createRadialGradient(-at.radius * 0.3, -at.radius * 0.3, 1, 0, 0, at.radius);
                    grad.addColorStop(0, "#FFFFFF");
                    grad.addColorStop(0.35, at.color);
                    grad.addColorStop(1, at.darkColor);
                    ctx.fillStyle = grad;
                    ctx.beginPath();
                    ctx.arc(0, 0, at.radius, 0, Math.PI * 2);
                    ctx.fill();

                    // Symbol
                    ctx.fillStyle = "#FFFFFF";
                    ctx.font = `800 ${Math.round(at.radius * 1.1)}px system-ui, sans-serif`;
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText(at.symbol, 0, 1);

                    ctx.restore();
                }

                // 4. Draw Chemical Formula Floaters
                for (const fb of formulaBadges) {
                    fb.x += fb.vx;
                    fb.y += fb.vy;
                    fb.rot += fb.vrot;
                    fb.vx *= 0.985;
                    fb.vy *= 0.985;
                    if (elapsedShatter > 1600) fb.alpha -= 0.018;

                    if (fb.alpha <= 0) continue;

                    ctx.save();
                    ctx.globalAlpha = Math.max(0, fb.alpha);
                    ctx.translate(fb.x, fb.y);
                    ctx.rotate(fb.rot);

                    ctx.font = "bold 13px system-ui, sans-serif";
                    const tw = ctx.measureText(fb.formula).width;
                    const w = tw + 22;
                    const h = 26;

                    ctx.fillStyle = "rgba(25, 14, 46, 0.82)";
                    ctx.strokeStyle = "rgba(167, 139, 250, 0.45)";
                    ctx.lineWidth = 1.4;
                    drawSafeRoundRect(ctx, -w / 2, -h / 2, w, h, 13);
                    ctx.fill();
                    ctx.stroke();

                    ctx.fillStyle = "#F3E8FF";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText(fb.formula, 0, 1);

                    ctx.restore();
                }

                // 5. Draw Quantum Spark Dust
                for (let i = quantumDust.length - 1; i >= 0; i--) {
                    const qd = quantumDust[i];
                    qd.x += qd.vx;
                    qd.y += qd.vy;
                    qd.vx *= 0.97;
                    qd.vy *= 0.97;
                    qd.alpha -= qd.decay;

                    if (qd.alpha <= 0) {
                        quantumDust.splice(i, 1);
                        continue;
                    }

                    ctx.save();
                    ctx.fillStyle = qd.color;
                    ctx.globalAlpha = qd.alpha;
                    ctx.shadowColor = qd.color;
                    ctx.shadowBlur = 8;
                    ctx.beginPath();
                    ctx.arc(qd.x, qd.y, qd.radius, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.restore();
                }

                // Transition trigger to reveal actual page
                if (elapsedShatter > 1900 && state !== "REVEAL") {
                    state = "REVEAL";
                    overlay.style.transition = "opacity 0.65s cubic-bezier(0.16, 1, 0.3, 1)";
                    overlay.style.opacity = "0";

                    // Trigger navigation when fade completes
                    setTimeout(() => {
                        cleanup();
                        if (typeof onComplete === "function") {
                            onComplete();
                        }
                    }, 650);
                }
            }

            ctx.restore();
        } catch (err) {
            console.error("Frame render error in shatter portal:", err);
            cleanup();
            if (typeof onComplete === "function") onComplete();
        }
    }

    animId = requestAnimationFrame(renderFrame);
}

// Universal Global Registration (works in both Classic <script> and ES Module contexts)
const BamiLoginShatter = {
    trigger: trigger
};

if (typeof window !== "undefined") {
    window.BamiLoginShatter = BamiLoginShatter;
    window.triggerBamiLoginShatterPortal = trigger;
}

// Auto-bind to Preview button if present in DOM for instant responsiveness
function bindPreviewTrigger() {
    const previewBtn = document.getElementById("preview-shatter-btn");
    if (previewBtn) {
        previewBtn.onclick = function (e) {
            if (e) e.preventDefault();
            trigger(function () {
                const notice = document.getElementById("auth-notice");
                if (notice) {
                    notice.textContent = "🎬 Cinematic sequence preview completed! Click Quick Sign In or Sign in to enter.";
                    notice.classList.remove("auth-notice-error");
                    notice.hidden = false;
                }
            }, true);
        };
    }
}

if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bindPreviewTrigger);
    } else {
        bindPreviewTrigger();
    }
}
