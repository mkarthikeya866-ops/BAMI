const localHosts = new Set(["localhost", "127.0.0.1"]);
const apiOrigin = localHosts.has(window.location.hostname)
    ? `http://${window.location.hostname}:8000`
    : window.location.origin;

export async function loadFirebaseConfig() {
    const response = await fetch(`${apiOrigin}/api/v1/firebase-config`, {
        signal: AbortSignal.timeout(10000)
    });
    const config = await response.json().catch(() => null);
    if (!response.ok) {
        throw new Error(
            config?.detail || "Firebase is not configured for this application yet."
        );
    }
    return config;
}
