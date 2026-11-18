import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';

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
    const camera = new THREE.PerspectiveCamera(52, 1, 0.1, 100);
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const smallViewport = window.matchMedia('(max-width: 700px)').matches;
    const columns = smallViewport ? 100 : 150;
    const rows = smallViewport ? 44 : 72;
    const count = columns * rows;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    const colorStops = [
        new THREE.Color('#ff9b52'),
        new THREE.Color('#ff6eae'),
        new THREE.Color('#bc83ff'),
        new THREE.Color('#62aaff'),
        new THREE.Color('#59e1b5')
    ];
    const color = new THREE.Color();

    let seed = 8219;
    const random = () => {
        seed = (seed * 1664525 + 1013904223) >>> 0;
        return seed / 4294967296;
    };

    for (let row = 0; row < rows; row += 1) {
        for (let column = 0; column < columns; column += 1) {
            const index = row * columns + column;
            const offset = index * 3;
            const x = (column / (columns - 1) - 0.5) * 36;
            const z = (row / (rows - 1) - 0.5) * 24;
            const colorPosition = column / (columns - 1) * (colorStops.length - 1);
            const colorIndex = Math.min(Math.floor(colorPosition), colorStops.length - 2);
            color.copy(colorStops[colorIndex]).lerp(
                colorStops[colorIndex + 1],
                colorPosition - colorIndex
            );
            const brightness = 0.72 + random() * 0.38;

            positions[offset] = x + (random() - 0.5) * 0.12;
            positions[offset + 1] = (random() - 0.5) * 0.8;
            positions[offset + 2] = z + (random() - 0.5) * 0.12;
            colors[offset] = color.r * brightness;
            colors[offset + 1] = color.g * brightness;
            colors[offset + 2] = color.b * brightness;
            sizes[index] = 2.2 + random() * 2.0;
        }
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1));

    const material = new THREE.ShaderMaterial({
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms: {
            uTime: { value: 0 },
            uPixelRatio: { value: 1 }
        },
        vertexShader: `
            attribute float aSize;
            attribute vec3 color;
            uniform float uTime;
            uniform float uPixelRatio;
            varying vec3 vColor;
            varying float vDepth;

            void main() {
                vec3 flowingPosition = position;
                float phase = position.x * 0.32 + position.z * 0.52;
                flowingPosition.y += sin(phase + uTime * 0.27) * 1.25;
                flowingPosition.y += sin(position.x * 0.67 - position.z * 0.32 - uTime * 0.37) * 0.48;
                flowingPosition.y += cos(position.z * 0.78 + uTime * 0.19) * 0.36;
                flowingPosition.y += sin(position.z * 0.55 + uTime * 0.22 + position.x * 0.13) * 0.3;
                flowingPosition.z += sin(position.x * 0.2 + uTime * 0.12 + position.z * 0.2) * 0.5;

                vec4 viewPosition = modelViewMatrix * vec4(flowingPosition, 1.0);
                gl_Position = projectionMatrix * viewPosition;
                gl_PointSize = aSize * uPixelRatio * (56.0 / -viewPosition.z);
                vColor = color;
                vDepth = clamp((-viewPosition.z - 10.0) / 28.0, 0.0, 1.0);
            }
        `,
        fragmentShader: `
            varying vec3 vColor;
            varying float vDepth;

            void main() {
                float radius = length(gl_PointCoord - vec2(0.5));
                float glow = 1.0 - smoothstep(0.2, 0.5, radius);
                if (glow < 0.03) discard;
                gl_FragColor = vec4(vColor, glow * (0.72 + vDepth * 0.2));
            }
        `
    });
    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    const resize = () => {
        const width = window.innerWidth;
        const height = window.innerHeight;
        const pixelRatio = Math.min(window.devicePixelRatio || 1, 1.25);
        renderer.setPixelRatio(pixelRatio);
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.position.set(0, 8, 23);
        camera.lookAt(0, 0, 0);
        camera.updateProjectionMatrix();
        const viewWidth = 2 * camera.position.length()
            * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))
            * camera.aspect;
        particles.scale.x = Math.min(1, viewWidth * 0.92 / 36);
        material.uniforms.uPixelRatio.value = pixelRatio;
    };

    let frameId;
    let previousFrame = 0;
    const render = (now) => {
        frameId = undefined;
        if (document.hidden) return;
        if (reducedMotion || now - previousFrame >= 33) {
            previousFrame = now;
            material.uniforms.uTime.value = reducedMotion ? 0 : now * 0.001;
            renderer.render(scene, camera);
        }
        if (!reducedMotion) frameId = window.requestAnimationFrame(render);
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
    console.error('Unable to initialize the particle-wave background:', error);
}
