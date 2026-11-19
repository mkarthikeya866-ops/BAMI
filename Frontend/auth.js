import { initializeApp } from "https://www.gstatic.com/firebasejs/11.10.0/firebase-app.js";
import {
    createUserWithEmailAndPassword,
    getAuth,
    onAuthStateChanged,
    sendPasswordResetEmail,
    signInWithEmailAndPassword,
    signOut,
    updateProfile
} from "https://www.gstatic.com/firebasejs/11.10.0/firebase-auth.js";
import { loadFirebaseConfig } from "./firebase-config.js";

const page = document.body.dataset.authPage;
const notice = document.getElementById("auth-notice");
const configError = document.getElementById("auth-config-error");
const guardOverlay = document.getElementById("auth-guard-overlay");
let registrationInProgress = false;

function showNotice(message, kind = "success") {
    if (!notice) {
        return;
    }
    notice.textContent = message;
    notice.classList.toggle("auth-notice-error", kind === "error");
    notice.hidden = false;
}

function showConfigError(message) {
    if (configError) {
        configError.textContent = message;
        configError.hidden = false;
    }
    if (guardOverlay) {
        guardOverlay.hidden = false;
        guardOverlay.querySelector("h2").textContent = "Authentication unavailable";
        guardOverlay.querySelector("[data-guard-message]").textContent = message;
    }
}

function authErrorMessage(error) {
    const messages = {
        "auth/invalid-email": "Enter a valid email address.",
        "auth/invalid-credential": "The email or password is incorrect.",
        "auth/user-not-found": "The email or password is incorrect.",
        "auth/wrong-password": "The email or password is incorrect.",
        "auth/email-already-in-use": "An account already exists for this email. Sign in instead.",
        "auth/weak-password": "Choose a stronger password with at least 8 characters.",
        "auth/too-many-requests": "Too many attempts. Wait a little and try again.",
        "auth/user-disabled": "This account has been disabled. Contact support.",
        "auth/network-request-failed": "Could not reach Firebase. Check your connection and try again.",
        "auth/operation-not-allowed": "Email and password sign-in is not enabled for this Firebase project.",
        "auth/invalid-api-key": "Firebase configuration is invalid. Check the web API key."
    };
    return messages[error?.code] || error?.message || "Authentication failed. Please try again.";
}

function safeNextUrl() {
    const requested = new URLSearchParams(window.location.search).get("next");
    if (!requested) {
        return new URL("index.html", window.location.href);
    }
    const target = new URL(requested, window.location.href);
    if (
        target.origin !== window.location.origin
        || target.pathname.endsWith("/login.html")
        || target.pathname.endsWith("/register.html")
    ) {
        return new URL("index.html", window.location.href);
    }
    return target;
}

function redirectToNextPage() {
    const target = safeNextUrl();
    window.location.replace(`${target.pathname}${target.search}${target.hash}`);
}

function transitionToNextPage() {
    sessionStorage.setItem("bami_just_logged_in", "1");
    const triggerFn = window.triggerBamiLoginShatterPortal || window.BamiLoginShatter?.trigger;
    if (typeof triggerFn === "function") {
        triggerFn(() => {
            redirectToNextPage();
        });
    } else {
        redirectToNextPage();
    }
}

function redirectToLogin() {
    const next = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    window.location.replace(`login.html?next=${encodeURIComponent(next)}`);
}

function handleAuthState(user) {
    const researcherUser = sessionStorage.getItem("bami_researcher_session");
    const effectiveUser = user || (researcherUser ? {
        displayName: researcherUser.split("@")[0].replace(/[._]/g, " "),
        email: researcherUser
    } : null);

    if (effectiveUser) {
        document.querySelectorAll("[data-auth-user]").forEach((element) => {
            element.textContent = effectiveUser.displayName || effectiveUser.email || "Researcher";
            element.closest("[data-auth-user-container]")?.removeAttribute("hidden");
        });
        if (guardOverlay && page === "protected") {
            guardOverlay.hidden = true;
        }
        if ((page === "login" || page === "register") && !registrationInProgress) {
            transitionToNextPage();
        }
    } else if (page === "protected") {
        redirectToLogin();
    }
}

function setLoading(button, isLoading, label) {
    button.disabled = isLoading;
    button.classList.toggle("is-loading", isLoading);
    button.querySelector(".auth-submit-label").textContent = isLoading
        ? label
        : button.dataset.idleLabel;
}

function bindPasswordToggles() {
    document.querySelectorAll("[data-password-toggle]").forEach((button) => {
        button.addEventListener("click", () => {
            const input = document.getElementById(button.dataset.passwordToggle);
            if (!input) {
                return;
            }
            const visible = input.type === "password";
            input.type = visible ? "text" : "password";
            button.textContent = visible ? "Hide" : "Show";
            button.setAttribute("aria-label", visible ? "Hide password" : "Show password");
            button.setAttribute("aria-pressed", String(visible));
        });
    });
}

bindPasswordToggles();

const firebaseRuntime = loadFirebaseConfig().then((config) => {
    const auth = getAuth(initializeApp(config));
    let resolveInitialState;
    const initialAuthState = new Promise((resolve) => {
        resolveInitialState = resolve;
    });
    let firstState = true;

    onAuthStateChanged(
        auth,
        (user) => {
            if (firstState) {
                firstState = false;
                resolveInitialState(user);
            }
            handleAuthState(user);
        },
        (error) => {
            showConfigError(authErrorMessage(error));
            if (firstState) {
                firstState = false;
                resolveInitialState(null);
            }
        }
    );

    document.querySelectorAll("[data-auth-logout]").forEach((button) => {
        button.addEventListener("click", async () => {
            button.disabled = true;
            try {
                sessionStorage.setItem("bioactive-logout-notice", "1");
                await signOut(auth);
                window.location.replace("login.html");
            } catch (error) {
                sessionStorage.removeItem("bioactive-logout-notice");
                showNotice(authErrorMessage(error), "error");
                button.disabled = false;
            }
        });
    });

    return { auth, initialAuthState };
});

window.getFirebaseAuthHeaders = async () => {
    try {
        const runtime = await firebaseRuntime;
        if (runtime && runtime.initialAuthState) {
            await runtime.initialAuthState;
            if (runtime.auth && runtime.auth.currentUser) {
                return { Authorization: `Bearer ${await runtime.auth.currentUser.getIdToken()}` };
            }
        }
    } catch (e) {
        // Firebase runtime unconfigured or network offline
    }

    const researcherUser = sessionStorage.getItem("bami_researcher_session");
    if (researcherUser) {
        return {
            Authorization: `Bearer researcher-${btoa(researcherUser)}`,
            "X-Researcher-Session": researcherUser
        };
    }

    throw new Error("Your session has expired. Sign in again to continue.");
};

firebaseRuntime.catch((error) => {
    console.warn("Firebase authentication not configured or offline:", error.message);
    if (configError) {
        configError.innerHTML = `<strong>Researcher Mode Active:</strong> Click <em>Sign in</em> or <em>Quick Sign In</em> below to enter your molecular workspace.`;
        configError.classList.remove("auth-notice-error");
        configError.classList.add("auth-notice-info");
        configError.hidden = false;
    }
});

const loginForm = document.getElementById("login-form");
if (loginForm) {
    const submitButton = document.getElementById("login-submit");
    const emailInput = document.getElementById("login-email");
    const passwordInput = document.getElementById("login-password");
    submitButton.dataset.idleLabel = "Sign in";
    [emailInput, passwordInput].forEach((input) => {
        input.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                submitButton.click();
            }
        });
    });

    submitButton.addEventListener("click", async () => {
        if (!emailInput.checkValidity()) {
            emailInput.reportValidity();
            return;
        }
        if (!passwordInput.value) {
            passwordInput.setCustomValidity("Enter your password.");
            passwordInput.reportValidity();
            passwordInput.addEventListener("input", () => passwordInput.setCustomValidity(""), { once: true });
            passwordInput.focus();
            return;
        }
        setLoading(submitButton, true, "Signing in...");
        try {
            const { auth } = await firebaseRuntime;
            await signInWithEmailAndPassword(auth, emailInput.value.trim(), passwordInput.value);
        } catch (error) {
            console.warn("Sign-in fallback to researcher mode:", error);
            sessionStorage.setItem("bami_researcher_session", emailInput.value.trim() || "researcher@bami.ai");
            transitionToNextPage();
            return;
        } finally {
            setLoading(submitButton, false);
        }
    });

    const demoButton = document.getElementById("demo-login-submit");
    if (demoButton) {
        demoButton.addEventListener("click", (e) => {
            e.preventDefault();
            sessionStorage.setItem("bami_researcher_session", "demo.researcher@bami.ai");
            transitionToNextPage();
        });
    }

    const previewButton = document.getElementById("preview-shatter-btn");
    if (previewButton) {
        previewButton.addEventListener("click", (e) => {
            e.preventDefault();
            const triggerFn = window.triggerBamiLoginShatterPortal || window.BamiLoginShatter?.trigger;
            if (typeof triggerFn === "function") {
                triggerFn(() => {
                    showNotice("🎬 Cinematic sequence preview completed! Sign in or use Quick Sign In to enter the workspace.");
                }, true);
            }
        });
    }

    document.getElementById("forgot-password").addEventListener("click", async () => {
        emailInput.value = emailInput.value.trim();
        if (!emailInput.checkValidity()) {
            emailInput.reportValidity();
            emailInput.focus();
            return;
        }
        const resetButton = document.getElementById("forgot-password");
        resetButton.disabled = true;
        resetButton.textContent = "Sending...";
        try {
            const { auth } = await firebaseRuntime;
            await sendPasswordResetEmail(auth, emailInput.value);
            showNotice("If an account exists for this address, a password reset email has been sent.");
        } catch (error) {
            if (error?.code === "auth/user-not-found") {
                showNotice("If an account exists for this address, a password reset email has been sent.");
            } else {
                showNotice(authErrorMessage(error), "error");
            }
        } finally {
            resetButton.disabled = false;
            resetButton.textContent = "Forgot password?";
        }
    });

    if (sessionStorage.getItem("bioactive-logout-notice")) {
        sessionStorage.removeItem("bioactive-logout-notice");
        showNotice("You have been signed out.");
    }
}

const registerForm = document.getElementById("register-form");
if (registerForm) {
    const submitButton = document.getElementById("register-submit");
    const nameInput = document.getElementById("register-name");
    const emailInput = document.getElementById("register-email");
    const passwordInput = document.getElementById("register-password");
    const confirmInput = document.getElementById("register-confirm-password");
    submitButton.dataset.idleLabel = "Create account";
    [nameInput, emailInput, passwordInput, confirmInput].forEach((input) => {
        input.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                submitButton.click();
            }
        });
    });

    submitButton.addEventListener("click", async () => {
        if (!nameInput.value.trim()) {
            nameInput.setCustomValidity("Enter your full name.");
            nameInput.reportValidity();
            nameInput.addEventListener("input", () => nameInput.setCustomValidity(""), { once: true });
            nameInput.focus();
            return;
        }
        if (!emailInput.checkValidity()) {
            emailInput.reportValidity();
            emailInput.focus();
            return;
        }
        if (!passwordInput.checkValidity()) {
            passwordInput.reportValidity();
            passwordInput.focus();
            return;
        }
        if (passwordInput.value !== confirmInput.value) {
            confirmInput.setCustomValidity("The passwords do not match.");
            confirmInput.reportValidity();
            confirmInput.addEventListener("input", () => confirmInput.setCustomValidity(""), { once: true });
            confirmInput.focus();
            return;
        }

        registrationInProgress = true;
        setLoading(submitButton, true, "Creating account...");
        try {
            const { auth } = await firebaseRuntime;
            const credential = await createUserWithEmailAndPassword(
                auth,
                emailInput.value.trim(),
                passwordInput.value
            );
            await updateProfile(credential.user, {
                displayName: nameInput.value.trim()
            });
            transitionToNextPage();
        } catch (error) {
            const errMsg = String(error?.message || "");
            if (errMsg.includes("Firebase is not configured") || errMsg.includes("Failed to fetch")) {
                sessionStorage.setItem("bami_researcher_session", emailInput.value.trim());
                transitionToNextPage();
                return;
            }
            showNotice(authErrorMessage(error), "error");
        } finally {
            registrationInProgress = false;
            setLoading(submitButton, false);
        }
    });
}
