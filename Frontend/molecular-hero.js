/* =========================================================
   BAMI INTERACTIVE 3D/2.5D MOLECULAR HERO CANVAS
   Draws an animated, interactive rotating biomolecular structure
   with conjugated aromatic rings, covalent bonds, electron pulses,
   and mouse-reactive kinetic parallax.
   ========================================================= */

(function () {
    'use strict';

    const canvas = document.getElementById('molecular-hero-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let animationFrameId = null;
    let mouseX = 0;
    let mouseY = 0;
    let targetRotX = 0;
    let targetRotY = 0;
    let rotX = 0.2;
    let rotY = 0.4;
    let rotZ = 0.05;

    // Molecular model coordinates: stylized EGFR kinase inhibitor (Quinazoline + Phenyl core)
    const rawNodes = [
        // Quinazoline ring 1 (benzene fused)
        { x: -1.2, y: -0.7, z: 0.1, element: 'C', radius: 10, color: '#A78BFA' },
        { x: -0.6, y: -1.4, z: 0.2, element: 'C', radius: 10, color: '#A78BFA' },
        { x: 0.8, y: -1.4, z: 0.1, element: 'C', radius: 10, color: '#A78BFA' },
        { x: 1.5, y: -0.7, z: -0.1, element: 'C', radius: 10, color: '#A78BFA' },
        { x: 0.8, y: 0.0, z: -0.2, element: 'C', radius: 10, color: '#A78BFA' },
        { x: -0.6, y: 0.0, z: -0.1, element: 'C', radius: 10, color: '#A78BFA' },

        // Quinazoline ring 2 (pyrimidine with nitrogens)
        { x: 1.5, y: 0.7, z: -0.3, element: 'N', radius: 12, color: '#60A5FA' },
        { x: 0.8, y: 1.4, z: -0.4, element: 'C', radius: 10, color: '#A78BFA' },
        { x: -0.6, y: 1.4, z: -0.3, element: 'N', radius: 12, color: '#60A5FA' },

        // Aniline amine linker
        { x: 1.5, y: 2.2, z: -0.5, element: 'N', radius: 11, color: '#38BDF8' },

        // Phenyl ring
        { x: 2.8, y: 2.2, z: -0.6, element: 'C', radius: 10, color: '#C084FC' },
        { x: 3.5, y: 3.0, z: -0.7, element: 'C', radius: 10, color: '#C084FC' },
        { x: 4.8, y: 3.0, z: -0.8, element: 'C', radius: 10, color: '#C084FC' },
        { x: 5.5, y: 2.2, z: -0.8, element: 'C', radius: 10, color: '#C084FC' },
        { x: 4.8, y: 1.4, z: -0.7, element: 'C', radius: 10, color: '#C084FC' },
        { x: 3.5, y: 1.4, z: -0.6, element: 'C', radius: 10, color: '#C084FC' },

        // Halogen / acetylene substituents
        { x: 6.8, y: 2.2, z: -0.9, element: 'Cl', radius: 13, color: '#34D399' },
        { x: 3.5, y: 4.2, z: -0.7, element: 'F', radius: 11, color: '#F472B6' },

        // Peripheral solubilizing chain (morpholine / PEG tail)
        { x: -2.4, y: -0.7, z: 0.3, element: 'O', radius: 12, color: '#F87171' },
        { x: -3.2, y: -1.4, z: 0.4, element: 'C', radius: 9, color: '#DDD6FE' },
        { x: -4.4, y: -0.8, z: 0.5, element: 'O', radius: 11, color: '#F87171' },
        { x: -5.2, y: -1.6, z: 0.6, element: 'C', radius: 9, color: '#DDD6FE' },
        { x: -2.4, y: 0.0, z: 0.1, element: 'O', radius: 11, color: '#F87171' }
    ];

    // Bonds connecting node indices
    const rawBonds = [
        [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], // benzene ring
        [3, 6], [6, 7], [7, 8], [8, 5],                 // pyrimidine fused
        [7, 9],                                         // linker
        [9, 10], [10, 11], [11, 12], [12, 13], [13, 14], [14, 15], [15, 10], // phenyl
        [13, 16],                                       // Cl
        [11, 17],                                       // F
        [0, 18], [18, 19], [19, 20], [20, 21],          // tail
        [5, 22]
    ];

    // Traveling electron pulses along bonds
    const pulses = [
        { bondIdx: 0, progress: 0.1, speed: 0.012 },
        { bondIdx: 2, progress: 0.5, speed: 0.015 },
        { bondIdx: 6, progress: 0.8, speed: 0.014 },
        { bondIdx: 10, progress: 0.3, speed: 0.018 },
        { bondIdx: 13, progress: 0.6, speed: 0.016 },
        { bondIdx: 17, progress: 0.2, speed: 0.011 }
    ];

    function resize() {
        const rect = canvas.parentElement.getBoundingClientRect();
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        width = rect.width;
        height = rect.height || 420;

        canvas.width = width * dpr;
        canvas.height = height * dpr;
        ctx.scale(dpr, dpr);
    }

    window.addEventListener('resize', resize);
    resize();

    // Mouse interactive parallax
    const parentCard = canvas.parentElement;
    if (parentCard) {
        parentCard.addEventListener('mousemove', function (e) {
            const rect = parentCard.getBoundingClientRect();
            const relX = (e.clientX - rect.left) / rect.width - 0.5;
            const relY = (e.clientY - rect.top) / rect.height - 0.5;
            targetRotY = relX * 1.2;
            targetRotX = -relY * 0.9;
        });

        parentCard.addEventListener('mouseleave', function () {
            targetRotX = 0;
            targetRotY = 0;
        });
    }

    // 3D rotation projection helper
    function rotateAndProject(point, rX, rY, rZ, scale, cx, cy) {
        // Rotate Y
        let cosY = Math.cos(rY);
        let sinY = Math.sin(rY);
        let x1 = point.x * cosY + point.z * sinY;
        let y1 = point.y;
        let z1 = -point.x * sinY + point.z * cosY;

        // Rotate X
        let cosX = Math.cos(rX);
        let sinX = Math.sin(rX);
        let x2 = x1;
        let y2 = y1 * cosX - z1 * sinX;
        let z2 = y1 * sinX + z1 * cosX;

        // Rotate Z
        let cosZ = Math.cos(rZ);
        let sinZ = Math.sin(rZ);
        let x3 = x2 * cosZ - y2 * sinZ;
        let y3 = x2 * sinZ + y2 * cosZ;
        let z3 = z2;

        // Perspective projection
        const fov = 400;
        const depth = fov / (fov + z3 * 35);
        const projX = cx + x3 * scale * depth;
        const projY = cy + y3 * scale * depth;

        return {
            x: projX,
            y: projY,
            z: z3,
            depth: depth,
            element: point.element,
            radius: point.radius * depth,
            color: point.color
        };
    }

    let lastTime = 0;

    function render(currentTime) {
        const delta = (currentTime - lastTime) * 0.001 || 0.016;
        lastTime = currentTime;

        // Smooth rotation damping
        rotY += 0.008; // continuous gentle spin
        rotX += (targetRotX - rotX) * 0.06;
        rotY += (targetRotY * 0.5);

        ctx.clearRect(0, 0, width, height);

        const cx = width / 2;
        const cy = height / 2;
        const scale = Math.min(width, height) * 0.13;

        // Project all nodes
        const projectedNodes = rawNodes.map(node =>
            rotateAndProject(node, rotX, rotY, rotZ, scale, cx, cy)
        );

        // Sort items by depth (z) for proper painter's algorithm rendering
        // Draw bonds first
        rawBonds.forEach(bond => {
            const n1 = projectedNodes[bond[0]];
            const n2 = projectedNodes[bond[1]];
            if (!n1 || !n2) return;

            const avgZ = (n1.z + n2.z) / 2;
            const alpha = Math.max(0.25, Math.min(0.9, 0.65 + avgZ * 0.15));

            ctx.beginPath();
            ctx.moveTo(n1.x, n1.y);
            ctx.lineTo(n2.x, n2.y);
            ctx.lineWidth = Math.max(1.5, 3.2 * ((n1.depth + n2.depth) / 2));

            const grad = ctx.createLinearGradient(n1.x, n1.y, n2.x, n2.y);
            grad.addColorStop(0, n1.color);
            grad.addColorStop(1, n2.color);

            ctx.strokeStyle = grad;
            ctx.globalAlpha = alpha;
            ctx.stroke();
            ctx.globalAlpha = 1.0;
        });

        // Update and draw traveling electron pulses
        pulses.forEach((pulse, idx) => {
            pulse.progress += pulse.speed;
            if (pulse.progress > 1) pulse.progress = 0;

            const bond = rawBonds[pulse.bondIdx];
            if (!bond) return;
            const n1 = projectedNodes[bond[0]];
            const n2 = projectedNodes[bond[1]];
            if (!n1 || !n2) return;

            const px = n1.x + (n2.x - n1.x) * pulse.progress;
            const py = n1.y + (n2.y - n1.y) * pulse.progress;

            ctx.beginPath();
            ctx.arc(px, py, 3.5, 0, Math.PI * 2);
            ctx.fillStyle = '#FFFFFF';
            ctx.shadowColor = '#651FFF';
            ctx.shadowBlur = 10;
            ctx.fill();
            ctx.shadowBlur = 0;
        });

        // Draw atom nodes (back to front)
        const sortedIndices = projectedNodes
            .map((node, index) => ({ node, index }))
            .sort((a, b) => a.node.z - b.node.z);

        sortedIndices.forEach(({ node }) => {
            const rad = Math.max(4, node.radius);

            // Glow aura
            const aura = ctx.createRadialGradient(node.x, node.y, rad * 0.2, node.x, node.y, rad * 2.2);
            aura.addColorStop(0, node.color);
            aura.addColorStop(1, 'transparent');
            ctx.globalAlpha = 0.35;
            ctx.beginPath();
            ctx.arc(node.x, node.y, rad * 2.2, 0, Math.PI * 2);
            ctx.fillStyle = aura;
            ctx.fill();
            ctx.globalAlpha = 1.0;

            // Atom sphere gradient
            const sphereGrad = ctx.createRadialGradient(
                node.x - rad * 0.3,
                node.y - rad * 0.3,
                rad * 0.1,
                node.x,
                node.y,
                rad
            );
            sphereGrad.addColorStop(0, '#FFFFFF');
            sphereGrad.addColorStop(0.45, node.color);
            sphereGrad.addColorStop(1, '#1A0E2E');

            ctx.beginPath();
            ctx.arc(node.x, node.y, rad, 0, Math.PI * 2);
            ctx.fillStyle = sphereGrad;
            ctx.fill();

            // Element label inside sphere
            ctx.font = `bold ${Math.max(8, Math.round(rad * 0.85))}px 'DM Sans', sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#FFFFFF';
            ctx.shadowColor = 'rgba(0,0,0,0.6)';
            ctx.shadowBlur = 4;
            ctx.fillText(node.element, node.x, node.y);
            ctx.shadowBlur = 0;
        });

        animationFrameId = requestAnimationFrame(render);
    }

    animationFrameId = requestAnimationFrame(render);
})();
