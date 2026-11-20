import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';

/**
 * BAMI Molecular Intelligence - Responsive 3D Micro-Particle Wave
 * ===============================================================
 * Minimalist, delicate micro-particle wave field with real-time
 * cursor parallax and kinetic ripple elevation.
 * - Tiny, crisp stardust particles (1.2px - 2.5px)
 * - Clean bio-computational gradient (Violet / Cobalt / Cyan / Emerald)
 * - Full-screen cursor & touch parallax
 * - NormalBlending for crystal-clear visibility on light & dark pages
 * - Highly optimized 60fps WebGL
 */

const existingCanvas = document.getElementById('particle-wave-background');
if (existingCanvas) {
    existingCanvas.remove();
}
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
    const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 100);

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isMobile = window.matchMedia('(max-width: 768px)').matches;

    // Breathable micro-particle grid (delicate, sleek, minimal)
    const columns = isMobile ? 60 : 92;
    const rows = isMobile ? 36 : 52;
    const count = columns * rows;

    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const sizes = new Float32Array(count);

    // Refined BAMI Bio-Computational Palette
    const colorStops = [
        new THREE.Color('#6d28d9'), // Deep Electric Violet
        new THREE.Color('#2563eb'), // Royal Azure
        new THREE.Color('#0284c7'), // Clean Sky Blue
        new THREE.Color('#0d9488'), // Teal Bio-Core
        new THREE.Color('#8b5cf6')  // Vibrant Violet
    ];
    const tempColor = new THREE.Color();

    let seed = 5123;
    const random = () => {
        seed = (seed * 1664525 + 1013904223) >>> 0;
        return seed / 4294967296;
    };

    const gridWidth = 36;
    const gridDepth = 24;

    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < columns; c++) {
            const index = r * columns + c;
            const offset = index * 3;

            const u = c / (columns - 1);
            const v = r / (rows - 1);

            const x = (u - 0.5) * gridWidth;
            const z = (v - 0.5) * gridDepth;

            // Gradient across width
            const colorPos = u * (colorStops.length - 1);
            const cIdx = Math.min(Math.floor(colorPos), colorStops.length - 2);
            tempColor.copy(colorStops[cIdx]).lerp(colorStops[cIdx + 1], colorPos - cIdx);

            const brightness = 0.92 + random() * 0.18;

            positions[offset] = x + (random() - 0.5) * 0.12;
            positions[offset + 1] = 0;
            positions[offset + 2] = z + (random() - 0.5) * 0.12;

            colors[offset] = tempColor.r * brightness;
            colors[offset + 1] = tempColor.g * brightness;
            colors[offset + 2] = tempColor.b * brightness;

            // TINY micro-particle size (delicate & sleek)
            sizes[index] = 1.1 + random() * 0.9;
        }
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1));

    // Custom Shader for delicate micro-particles & cursor reactivity
    const material = new THREE.ShaderMaterial({
        transparent: true,
        depthWrite: false,
        blending: THREE.NormalBlending,
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

                // Calming ambient wave motion
                float wave = sin(pos.x * 0.22 + uTime * 0.45) * cos(pos.z * 0.24 + uTime * 0.38) * 1.1;
                wave += sin(pos.x * 0.4 - pos.z * 0.3 + uTime * 0.26) * 0.35;
                pos.y += wave;

                // Cursor interactive ripple & elevation
                float distToMouse = length(pos.xz - uMouseWorld);
                float ripple = sin(distToMouse * 0.85 - uTime * 2.8) * exp(-distToMouse * 0.24) * 1.8;
                pos.y += ripple * uMouseIntensity;

                vec4 viewPos = modelViewMatrix * vec4(pos, 1.0);
                gl_Position = projectionMatrix * viewPos;

                // Delicate point sizing - small micro-dots
                float hoverBoost = (1.0 - smoothstep(0.0, 5.5, distToMouse)) * uMouseIntensity;
                gl_PointSize = aSize * uPixelRatio * (1.0 + hoverBoost * 0.6) * (18.0 / -viewPos.z);

                vColor = color;
                // Crisp alpha
                float baseAlpha = 0.68 + (pos.y + 1.2) * 0.12;
                vAlpha = clamp(baseAlpha + hoverBoost * 0.32, 0.3, 1.0);
            }
        `,
        fragmentShader: `
            varying vec3 vColor;
            varying float vAlpha;

            void main() {
                // Crisp circular micro-dot with soft anti-aliased edge
                float dist = length(gl_PointCoord - vec2(0.5));
                if (dist > 0.5) discard;
                float core = 1.0 - smoothstep(0.1, 0.48, dist);
                gl_FragColor = vec4(vColor, core * vAlpha);
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
        const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);

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

            // Smooth mouse spring lerp
            currentMouseX += (targetMouseX - currentMouseX) * 0.06;
            currentMouseY += (targetMouseY - currentMouseY) * 0.06;
            currentMouseActive += (mouseActiveTarget - currentMouseActive) * 0.05;

            // Responsive 3D Parallax Camera
            camera.position.x = currentMouseX * 4.2;
            camera.position.y = 7.5 + currentMouseY * 2.2;
            camera.lookAt(0, 0, 0);

            // Project cursor into world plane
            const mouseWorldX = currentMouseX * 16.0;
            const mouseWorldZ = -currentMouseY * 11.0;

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
    console.error('Unable to initialize the responsive micro-particle wave background:', error);
}
