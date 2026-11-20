import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';

/**
 * BAMI Molecular Intelligence - Responsive 3D Particle Wave Field
 * ===============================================================
 * Clean, lightweight, cursor-responsive Three.js particle field.
 * - Minimalist bio-computational color palette (Violet / Royal Blue / Cyan)
 * - Real-time 3D camera parallax & cursor-driven wave distortion
 * - Touch & pointer support with smooth dampening (lerp)
 * - Hardware accelerated 60fps with low power consumption
 */

const canvas = document.createElement('canvas');
canvas.id = 'particle-wave-background';
canvas.setAttribute('aria-hidden', 'true');
document.body.prepend(canvas);

try {
    const renderer = new THREE.WebGLRenderer({
        canvas,
        alpha: true,
        antialias: false,
        powerPreference: 'low-power'
    });

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isMobile = window.matchMedia('(max-width: 768px)').matches;

    // Clean, breathable particle grid (lightweight & minimal)
    const columns = isMobile ? 48 : 72;
    const rows = isMobile ? 28 : 42;
    const count = columns * rows;

    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const sizes = new Float32Array(count);

    // BAMI Sophisticated Bio-Tech Palette: Electric Violet -> Cobalt -> Clean Cyan
    const colorStops = [
        new THREE.Color('#7c3aed'), // Electric Violet
        new THREE.Color('#3b82f6'), // Electric Blue
        new THREE.Color('#06b6d4'), // Cyan Teal
        new THREE.Color('#a855f7')  // Soft Lavender
    ];
    const tempColor = new THREE.Color();

    let seed = 4219;
    const random = () => {
        seed = (seed * 1664525 + 1013904223) >>> 0;
        return seed / 4294967296;
    };

    const gridWidth = 34;
    const gridDepth = 22;

    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < columns; c++) {
            const index = r * columns + c;
            const offset = index * 3;

            // Normalized coordinates (-0.5 to 0.5)
            const u = c / (columns - 1);
            const v = r / (rows - 1);

            const x = (u - 0.5) * gridWidth;
            const z = (v - 0.5) * gridDepth;

            // Smooth color gradient across the grid
            const colorPos = u * (colorStops.length - 1);
            const cIdx = Math.min(Math.floor(colorPos), colorStops.length - 2);
            tempColor.copy(colorStops[cIdx]).lerp(colorStops[cIdx + 1], colorPos - cIdx);

            const brightness = 0.85 + random() * 0.25;

            // Small jitter for natural, organic look
            positions[offset] = x + (random() - 0.5) * 0.15;
            positions[offset + 1] = 0;
            positions[offset + 2] = z + (random() - 0.5) * 0.15;

            colors[offset] = tempColor.r * brightness;
            colors[offset + 1] = tempColor.g * brightness;
            colors[offset + 2] = tempColor.b * brightness;

            sizes[index] = 2.4 + random() * 1.8;
        }
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1));

    // Custom Shader for silky smooth 60fps cursor responsiveness
    const material = new THREE.ShaderMaterial({
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms: {
            uTime: { value: 0 },
            uPixelRatio: { value: 1 },
            uMouseWorld: { value: new THREE.Vector2(0, 0) },
            uMouseIntensity: { value: 0 }
        },
        vertexShader: `
            attribute float aSize;
            attribute vec3 color;
            uniform float uTime;
            uniform float uPixelRatio;
            uniform vec2 uMouseWorld;
            uniform float uMouseIntensity;
            varying vec3 vColor;
            varying float vAlpha;

            void main() {
                vec3 pos = position;

                // Simple, calming ambient wave motion
                float wave = sin(pos.x * 0.22 + uTime * 0.45) * cos(pos.z * 0.25 + uTime * 0.35) * 0.95;
                wave += sin(pos.x * 0.45 - pos.z * 0.35 + uTime * 0.25) * 0.35;
                pos.y += wave;

                // Interactive cursor ripple / elevation
                float distToMouse = length(pos.xz - uMouseWorld);
                float ripple = sin(distToMouse * 0.9 - uTime * 2.2) * exp(-distToMouse * 0.28) * 1.8;
                pos.y += ripple * uMouseIntensity;

                vec4 viewPos = modelViewMatrix * vec4(pos, 1.0);
                gl_Position = projectionMatrix * viewPos;

                // Interactive point sizing
                float hoverBoost = (1.0 - smoothstep(0.0, 5.0, distToMouse)) * uMouseIntensity;
                gl_PointSize = aSize * uPixelRatio * (1.0 + hoverBoost * 0.5) * (50.0 / -viewPos.z);

                vColor = color;
                // Soft alpha falloff + cursor proximity glow
                float baseAlpha = 0.55 + (pos.y + 1.2) * 0.12;
                vAlpha = clamp(baseAlpha + hoverBoost * 0.4, 0.2, 0.95);
            }
        `,
        fragmentShader: `
            varying vec3 vColor;
            varying float vAlpha;

            void main() {
                // Soft circular glowing particle
                float dist = length(gl_PointCoord - vec2(0.5));
                if (dist > 0.5) discard;
                float glow = pow(1.0 - smoothstep(0.0, 0.48, dist), 1.6);
                gl_FragColor = vec4(vColor, glow * vAlpha);
            }
        `
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // =========================================================
    // CURSOR TRACKING & PARALLAX STATE
    // =========================================================
    let targetMouseX = 0;
    let targetMouseY = 0;
    let currentMouseX = 0;
    let currentMouseY = 0;
    let mouseActiveTarget = 0;
    let currentMouseActive = 0;

    const onPointerMove = (e) => {
        mouseActiveTarget = 1.0;
        // Normalized coordinates (-1 to 1)
        targetMouseX = (e.clientX / window.innerWidth) * 2 - 1;
        targetMouseY = -(e.clientY / window.innerHeight) * 2 + 1;
    };

    const onPointerLeave = () => {
        mouseActiveTarget = 0.0;
        targetMouseX = 0;
        targetMouseY = 0;
    };

    const onTouchMove = (e) => {
        if (e.touches && e.touches.length > 0) {
            mouseActiveTarget = 1.0;
            const touch = e.touches[0];
            targetMouseX = (touch.clientX / window.innerWidth) * 2 - 1;
            targetMouseY = -(touch.clientY / window.innerHeight) * 2 + 1;
        }
    };

    window.addEventListener('pointermove', onPointerMove, { passive: true });
    window.addEventListener('pointerleave', onPointerLeave, { passive: true });
    window.addEventListener('touchmove', onTouchMove, { passive: true });
    window.addEventListener('touchend', onPointerLeave, { passive: true });

    // =========================================================
    // RESIZE & CAMERA SETUP
    // =========================================================
    const resize = () => {
        const width = window.innerWidth;
        const height = window.innerHeight;
        const pixelRatio = Math.min(window.devicePixelRatio || 1, 1.5);

        renderer.setPixelRatio(pixelRatio);
        renderer.setSize(width, height, false);

        camera.aspect = width / height;
        camera.position.set(0, 7.5, 20);
        camera.lookAt(0, 0, 0);
        camera.updateProjectionMatrix();

        const viewWidth = 2 * camera.position.length()
            * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))
            * camera.aspect;
        particles.scale.x = Math.min(1.15, viewWidth * 0.95 / gridWidth);

        material.uniforms.uPixelRatio.value = pixelRatio;
    };

    // =========================================================
    // ANIMATION & RENDER LOOP
    // =========================================================
    let frameId;
    let previousFrame = 0;

    const render = (now) => {
        frameId = undefined;
        if (document.hidden) return;

        if (reducedMotion || now - previousFrame >= 16) {
            previousFrame = now;
            const timeSeconds = reducedMotion ? 0 : now * 0.001;

            // Smooth mouse interpolation (spring lerp)
            currentMouseX += (targetMouseX - currentMouseX) * 0.055;
            currentMouseY += (targetMouseY - currentMouseY) * 0.055;
            currentMouseActive += (mouseActiveTarget - currentMouseActive) * 0.04;

            // Responsive 3D Camera Parallax
            camera.position.x = currentMouseX * 3.8;
            camera.position.y = 7.5 + currentMouseY * 2.0;
            camera.lookAt(0, 0, 0);

            // Project cursor into world grid coordinates for the ripple effect
            const mouseWorldX = currentMouseX * 15.0;
            const mouseWorldZ = -currentMouseY * 10.0;

            material.uniforms.uTime.value = timeSeconds;
            material.uniforms.uMouseWorld.value.set(mouseWorldX, mouseWorldZ);
            material.uniforms.uMouseIntensity.value = currentMouseActive;

            renderer.render(scene, camera);
        }

        if (!reducedMotion) {
            frameId = window.requestAnimationFrame(render);
        }
    };

    const startRendering = () => {
        if (reducedMotion || frameId === undefined) {
            frameId = window.requestAnimationFrame(render);
        }
    };

    const stopRendering = () => {
        if (frameId !== undefined) {
            window.cancelAnimationFrame(frameId);
            frameId = undefined;
        }
    };

    resize();
    window.addEventListener('resize', resize, { passive: true });
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) stopRendering();
        else startRendering();
    });

    startRendering();

} catch (error) {
    canvas.remove();
    console.error('Unable to initialize the responsive particle wave background:', error);
}
