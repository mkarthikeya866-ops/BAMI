/* =========================================================
   BAMI INTERACTIVE 3D MOLECULAR HERO CANVAS
   Sleek, compact bioactive pharmacophore core with smooth
   cursor-responsive 3D rotation, depth projection, and drag physics.
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

    // Smooth rotational state & target damping
    let rotX = 0.22;
    let rotY = 0.35;
    let rotZ = 0.08;
    let targetTiltX = 0;
    let targetTiltY = 0;
    let currentTiltX = 0;
    let currentTiltY = 0;

    let isDragging = false;
    let startPointerX = 0;
    let startPointerY = 0;
    let dragVelocityX = 0;
    let dragVelocityY = 0;

    // Compact, refined Bioactive Lead Model (sleek atom nodes)
    const rawNodes = [
        // Core Ring A (Aromatic benzene)
        { x: -1.2, y: -0.7, z: 0.1, element: 'C', radius: 6.5, color: '#8B5CF6' },
        { x: -0.6, y: -1.4, z: 0.2, element: 'C', radius: 6.5, color: '#8B5CF6' },
        { x: 0.8, y: -1.4, z: 0.1, element: 'C', radius: 6.5, color: '#8B5CF6' },
        { x: 1.5, y: -0.7, z: -0.1, element: 'C', radius: 6.5, color: '#8B5CF6' },
        { x: 0.8, y: 0.0, z: -0.2, element: 'C', radius: 6.5, color: '#8B5CF6' },
        { x: -0.6, y: 0.0, z: -0.1, element: 'C', radius: 6.5, color: '#8B5CF6' },

        // Core Ring B (Pyrimidine heteroatoms)
        { x: 1.5, y: 0.7, z: -0.3, element: 'N', radius: 7.5, color: '#38BDF8' },
        { x: 0.8, y: 1.4, z: -0.4, element: 'C', radius: 6.5, color: '#8B5CF6' },
        { x: -0.6, y: 1.4, z: -0.3, element: 'N', radius: 7.5, color: '#38BDF8' },

        // Pharmacophore Linker
        { x: 1.5, y: 2.2, z: -0.5, element: 'NH', radius: 7.0, color: '#06B6D4' },

        // Target Phenyl Ring
        { x: 2.7, y: 2.2, z: -0.6, element: 'C', radius: 6.5, color: '#A855F7' },
        { x: 3.4, y: 3.1, z: -0.7, element: 'C', radius: 6.5, color: '#A855F7' },
        { x: 4.6, y: 3.1, z: -0.8, element: 'C', radius: 6.5, color: '#A855F7' },
        { x: 5.3, y: 2.2, z: -0.8, element: 'F', radius: 7.5, color: '#EC4899' },
        { x: 4.6, y: 1.3, z: -0.7, element: 'C', radius: 6.5, color: '#A855F7' },
        { x: 3.4, y: 1.3, z: -0.6, element: 'C', radius: 6.5, color: '#A855F7' }
    ];

    // Covalent bonds connecting the pharmacophore
    const rawBonds = [
        [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], // Ring A
        [3, 6], [6, 7], [7, 8], [8, 5],                 // Ring B
        [7, 9],                                         // Amine linker
        [9, 10], [10, 11], [11, 12], [12, 13], [13, 14], [14, 15], [15, 10] // Phenyl ring
    ];

    function resize() {
        const parent = canvas.parentElement;
        if (!parent) return;
        const rect = parent.getBoundingClientRect();
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        width = rect.width;
        height = rect.height || 420;

        canvas.width = width * dpr;
        canvas.height = height * dpr;
        ctx.scale(dpr, dpr);
    }

    window.addEventListener('resize', resize, { passive: true });
    resize();

    // =========================================================
    // CURSOR & TOUCH RESPONSIVE PARALLAX
    // =========================================================
    window.addEventListener('pointermove', function (e) {
        if (isDragging) return;
        const normX = (e.clientX / window.innerWidth) - 0.5;
        const normY = (e.clientY / window.innerHeight) - 0.5;
        targetTiltY = normX * 0.9;
        targetTiltX = -normY * 0.7;
    }, { passive: true });

    const stage = canvas.parentElement;
    if (stage) {
        stage.style.cursor = 'grab';

        const onPointerDown = (e) => {
            isDragging = true;
            stage.style.cursor = 'grabbing';
            startPointerX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
            startPointerY = e.clientY || (e.touches && e.touches[0].clientY) || 0;
            dragVelocityX = 0;
            dragVelocityY = 0;
        };

        const onPointerMove = (e) => {
            if (!isDragging) return;
            const px = e.clientX || (e.touches && e.touches[0].clientX) || 0;
            const py = e.clientY || (e.touches && e.touches[0].clientY) || 0;
            const dx = px - startPointerX;
            const dy = py - startPointerY;

            startPointerX = px;
            startPointerY = py;

            dragVelocityX = dx * 0.008;
            dragVelocityY = dy * 0.008;

            rotY += dragVelocityX;
            rotX -= dragVelocityY;
        };

        const onPointerUp = () => {
            isDragging = false;
            stage.style.cursor = 'grab';
        };

        stage.addEventListener('mousedown', onPointerDown);
        window.addEventListener('mousemove', onPointerMove);
        window.addEventListener('mouseup', onPointerUp);

        stage.addEventListener('touchstart', onPointerDown, { passive: true });
        window.addEventListener('touchmove', onPointerMove, { passive: true });
        window.addEventListener('touchend', onPointerUp, { passive: true });
    }

    // 3D rotation projection helper
    function rotateAndProject(point, rX, rY, rZ, scale, cx, cy) {
        const cosY = Math.cos(rY);
        const sinY = Math.sin(rY);
        const x1 = point.x * cosY + point.z * sinY;
        const y1 = point.y;
        const z1 = -point.x * sinY + point.z * cosY;

        const cosX = Math.cos(rX);
        const sinX = Math.sin(rX);
        const x2 = x1;
        const y2 = y1 * cosX - z1 * sinX;
        const z2 = y1 * sinX + z1 * cosX;

        const cosZ = Math.cos(rZ);
        const sinZ = Math.sin(rZ);
        const x3 = x2 * cosZ - y2 * sinZ;
        const y3 = x2 * sinZ + y2 * cosZ;
        const z3 = z2;

        const fov = 420;
        const depth = fov / (fov + z3 * 36);
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

    // =========================================================
    // RENDER LOOP
    // =========================================================
    function render() {
        if (document.hidden) {
            animationFrameId = requestAnimationFrame(render);
            return;
        }

        if (isDragging) {
            // Drag rotation active
        } else {
            rotY += 0.008 + dragVelocityX;
            rotX += dragVelocityY;
            dragVelocityX *= 0.94;
            dragVelocityY *= 0.94;
        }

        // Smooth cursor tilt interpolation
        currentTiltX += (targetTiltX - currentTiltX) * 0.06;
        currentTiltY += (targetTiltY - currentTiltY) * 0.06;

        const effectiveRotX = rotX + currentTiltX;
        const effectiveRotY = rotY + currentTiltY;

        ctx.clearRect(0, 0, width, height);

        const cx = width / 2;
        const cy = height / 2;
        const scale = Math.min(width, height) * 0.108; // Sleek, compact scale

        // Project all nodes
        const projectedNodes = rawNodes.map(node =>
            rotateAndProject(node, effectiveRotX, effectiveRotY, rotZ, scale, cx, cy)
        );

        // 1. Draw Covalent Bonds (Fine, elegant lines)
        rawBonds.forEach(bond => {
            const n1 = projectedNodes[bond[0]];
            const n2 = projectedNodes[bond[1]];
            if (!n1 || !n2) return;

            const avgZ = (n1.z + n2.z) / 2;
            const alpha = Math.max(0.28, Math.min(0.9, 0.65 + avgZ * 0.15));

            ctx.beginPath();
            ctx.moveTo(n1.x, n1.y);
            ctx.lineTo(n2.x, n2.y);
            ctx.lineWidth = Math.max(1.2, 2.4 * ((n1.depth + n2.depth) / 2));

            const grad = ctx.createLinearGradient(n1.x, n1.y, n2.x, n2.y);
            grad.addColorStop(0, n1.color);
            grad.addColorStop(1, n2.color);

            ctx.strokeStyle = grad;
            ctx.globalAlpha = alpha;
            ctx.stroke();
            ctx.globalAlpha = 1.0;
        });

        // 2. Draw Atom Nodes (Sorted back-to-front by z depth)
        const sortedIndices = projectedNodes
            .map((node, index) => ({ node, index }))
            .sort((a, b) => a.node.z - b.node.z);

        sortedIndices.forEach(({ node }) => {
            const rad = Math.max(3.5, node.radius);

            // Subtle glow aura
            const aura = ctx.createRadialGradient(node.x, node.y, rad * 0.2, node.x, node.y, rad * 1.8);
            aura.addColorStop(0, node.color);
            aura.addColorStop(1, 'transparent');
            ctx.globalAlpha = 0.28;
            ctx.beginPath();
            ctx.arc(node.x, node.y, rad * 1.8, 0, Math.PI * 2);
            ctx.fillStyle = aura;
            ctx.fill();
            ctx.globalAlpha = 1.0;

            // 3D Spherical shading
            const sphereGrad = ctx.createRadialGradient(
                node.x - rad * 0.35,
                node.y - rad * 0.35,
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

            // Element chemical symbol
            ctx.font = `bold ${Math.max(7, Math.round(rad * 0.82))}px 'Space Grotesk', -apple-system, sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#FFFFFF';
            ctx.shadowColor = 'rgba(0,0,0,0.6)';
            ctx.shadowBlur = 3;
            ctx.fillText(node.element, node.x, node.y + 0.5);
            ctx.shadowBlur = 0;
        });

        animationFrameId = requestAnimationFrame(render);
    }

    animationFrameId = requestAnimationFrame(render);
})();
