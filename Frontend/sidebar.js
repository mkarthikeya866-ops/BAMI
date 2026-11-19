/* =========================================================
   BAMI UNIFIED WORKSPACE SIDEBAR CONTROLLER
   Pure Vanilla JavaScript
   Manages persistent collapsible sidebar, active item highlighting,
   mobile off-canvas drawer, tooltips, and authentication state.
   ========================================================= */

(function () {
    'use strict';

    const STORAGE_KEY = 'bami_sidebar_collapsed';

    // Navigation items schema
    const NAV_SECTIONS = [
        {
            title: "DISCOVERY & GUIDE",
            items: [
                {
                    id: "home",
                    label: "Beginner's Guide",
                    desc: "Drug dictionary & workflow",
                    icon: "📖",
                    href: "home.html",
                    badge: "GUIDE"
                }
            ]
        },
        {
            title: "BIOACTIVITY MODELS",
            items: [
                {
                    id: "predict",
                    label: "Single Prediction",
                    desc: "COX-2 & EGFR XGBoost inference",
                    icon: "⚡",
                    href: "index.html#prediction",
                    badge: "XGB"
                },
                {
                    id: "batch",
                    label: "Batch Screening",
                    desc: "High-throughput library screening",
                    icon: "📊",
                    href: "index.html#batch-screening",
                    badge: "BATCH"
                }
            ]
        },
        {
            title: "STRUCTURAL CHEMISTRY",
            items: [
                {
                    id: "docking",
                    label: "Molecular Docking",
                    desc: "AutoDock Vina & 3D pose",
                    icon: "🔬",
                    href: "docking.html",
                    badge: "VINA"
                },
                {
                    id: "drug-likeness",
                    label: "Drug-Likeness",
                    desc: "Lipinski Rule of 5 analysis",
                    icon: "💊",
                    href: "drug-likeness.html",
                    badge: "Ro5"
                },
                {
                    id: "scaffold",
                    label: "Scaffold Analysis",
                    desc: "Bemis-Murcko core & SAR",
                    icon: "🧬",
                    href: "scaffold-analysis.html",
                    badge: "SAR"
                }
            ]
        },
        {
            title: "PHARMACOKINETICS",
            items: [
                {
                    id: "admet",
                    label: "ADMET Profiling",
                    desc: "10 ML absorption & toxicity endpoints",
                    icon: "🧪",
                    href: "admet.html",
                    badge: "10 ML"
                }
            ]
        },
        {
            title: "WORKSPACE",
            items: [
                {
                    id: "history",
                    label: "Prediction History",
                    desc: "50 recent screening leads",
                    icon: "🕒",
                    href: "history.html",
                    badge: "50"
                }
            ]
        }
    ];

    /**
     * Determine active item from current path and hash
     */
    function getActiveItemId() {
        const path = window.location.pathname.toLowerCase();
        const hash = window.location.hash.toLowerCase();

        if (path.endsWith('home.html')) return 'home';
        if (path.endsWith('docking.html') || hash.includes('docking')) return 'docking';
        if (path.endsWith('drug-likeness.html')) return 'drug-likeness';
        if (path.endsWith('scaffold-analysis.html')) return 'scaffold';
        if (path.endsWith('admet.html')) return 'admet';
        if (path.endsWith('history.html')) return 'history';

        if (path.endsWith('index.html') || path.endsWith('/') || path === '') {
            if (hash.includes('batch')) return 'batch';
            return 'predict';
        }

        return 'predict';
    }

    /**
     * Get title for the current page
     */
    function getCurrentPageTitle(activeId) {
        for (const sec of NAV_SECTIONS) {
            for (const it of sec.items) {
                if (it.id === activeId) return it.label;
            }
        }
        return 'Molecular Workspace';
    }

    /**
     * Build Sidebar HTML
     */
    function buildSidebarHtml(activeId) {
        let navHtml = '';

        NAV_SECTIONS.forEach((section) => {
            navHtml += `
            <div class="sidebar-group">
                <div class="sidebar-category-title">${section.title}</div>
            `;

            section.items.forEach((item) => {
                const isActive = item.id === activeId;
                const activeClass = isActive ? ' active' : '';
                const ariaCurrent = isActive ? ' aria-current="page"' : '';

                navHtml += `
                <a href="${item.href}" class="sidebar-nav-item${activeClass}" data-id="${item.id}" data-tooltip="${item.label}"${ariaCurrent}>
                    <span class="sidebar-item-icon" aria-hidden="true">${item.icon}</span>
                    <div class="sidebar-item-body">
                        <span class="sidebar-nav-label">${item.label}</span>
                        <span class="sidebar-nav-desc">${item.desc}</span>
                    </div>
                    ${item.badge ? `<span class="sidebar-nav-badge">${item.badge}</span>` : ''}
                </a>
                `;
            });

            navHtml += `</div>`;
        });

        return `
        <aside id="bami-sidebar" class="bami-sidebar" aria-label="Application Navigation">
            <div class="sidebar-header">
                <a href="home.html" class="sidebar-brand">
                    <span class="sidebar-brand-icon" aria-hidden="true">✦</span>
                    <div class="sidebar-brand-text">
                        <span class="sidebar-brand-name">BAMI</span>
                        <span class="sidebar-brand-subtitle">Bioactive Molecule Intel</span>
                    </div>
                </a>
                <button type="button" id="sidebar-collapse-toggle" class="sidebar-toggle-btn" aria-label="Toggle Sidebar" title="Collapse / Expand Sidebar ([)">
                    <span class="sidebar-toggle-icon" aria-hidden="true">◀</span>
                </button>
            </div>

            <nav class="sidebar-nav-container">
                ${navHtml}
            </nav>

            <div class="sidebar-footer">
                <div class="sidebar-status-indicator" title="FastAPI Inference Engine is active on port 8000">
                    <span class="sidebar-status-dot" aria-hidden="true"></span>
                    <span class="sidebar-status-text">Backend Active :8000</span>
                </div>

                <div class="sidebar-auth-panel" data-auth-user-container hidden>
                    <div class="sidebar-user-info">
                        <div class="sidebar-user-avatar" aria-hidden="true">👤</div>
                        <span class="sidebar-user-email" data-auth-user>Researcher</span>
                    </div>
                    <button type="button" class="sidebar-auth-btn" data-auth-logout title="Sign out of BAMI">
                        Sign out
                    </button>
                </div>

                <div class="sidebar-auth-panel" data-auth-guest-container>
                    <div class="sidebar-user-info">
                        <div class="sidebar-user-avatar" style="background: rgba(255,255,255,0.1);" aria-hidden="true">✦</div>
                        <span class="sidebar-user-email" style="color: #BFAEE0;">Guest Session</span>
                    </div>
                    <a href="login.html" class="sidebar-auth-btn" title="Sign in to your account">
                        Sign in
                    </a>
                </div>
            </div>
        </aside>
        <div id="bami-sidebar-backdrop" class="bami-sidebar-backdrop" aria-hidden="true"></div>
        `;
    }

    /**
     * Build Topbar HTML
     */
    function buildTopbarHtml(activeId) {
        const pageTitle = getCurrentPageTitle(activeId);

        return `
        <header class="app-topbar">
            <div class="topbar-left">
                <button type="button" id="mobile-sidebar-toggle" class="mobile-menu-btn" aria-label="Open Navigation Menu">
                    ☰
                </button>
                <button type="button" id="topbar-sidebar-toggle" class="topbar-toggle-btn" aria-label="Toggle Sidebar Rail" title="Collapse / Expand Sidebar">
                    «
                </button>
                <div class="topbar-breadcrumb">
                    <a href="home.html" class="topbar-breadcrumb-brand">BAMI</a>
                    <span class="topbar-breadcrumb-sep">/</span>
                    <span class="topbar-breadcrumb-current">${pageTitle}</span>
                </div>
            </div>

            <div class="topbar-right">
                <div class="topbar-chips">
                    <span class="topbar-chip topbar-chip-cox2" title="COX-2 Bioactivity Model: Final XGBoost with Morgan Fingerprints">
                        <span class="topbar-chip-dot"></span> COX-2 (XGB)
                    </span>
                    <span class="topbar-chip topbar-chip-egfr" title="EGFR Bioactivity Model: Tuned XGBoost with Calibrated Probability">
                        <span class="topbar-chip-dot"></span> EGFR (XGB)
                    </span>
                </div>
                <a href="home.html" class="topbar-action-btn" title="View beginner-friendly dictionary and computational drug discovery guide">
                    ✦ Guide
                </a>
            </div>
        </header>
        `;
    }

    /**
     * Initialize the Sidebar in the DOM
     */
    function initSidebar() {
        const layoutRoot = document.getElementById('bami-layout');
        if (!layoutRoot) return;

        const activeId = getActiveItemId();

        // Check stored collapsed state
        const isCollapsed = localStorage.getItem(STORAGE_KEY) === '1';
        if (isCollapsed) {
            layoutRoot.classList.add('sidebar-collapsed');
        }

        // 1. Inject Sidebar markup
        const sidebarPlaceholder = document.getElementById('bami-sidebar-placeholder');
        if (sidebarPlaceholder) {
            sidebarPlaceholder.outerHTML = buildSidebarHtml(activeId);
        }

        // 2. Inject Topbar markup
        const topbarPlaceholder = document.getElementById('bami-topbar-placeholder');
        if (topbarPlaceholder) {
            topbarPlaceholder.outerHTML = buildTopbarHtml(activeId);
        }

        // 3. Attach Event Listeners
        const sidebarCollapseBtn = document.getElementById('sidebar-collapse-toggle');
        const topbarCollapseBtn = document.getElementById('topbar-sidebar-toggle');
        const mobileToggleBtn = document.getElementById('mobile-sidebar-toggle');
        const backdrop = document.getElementById('bami-sidebar-backdrop');

        function toggleSidebarCollapse() {
            const willCollapse = !layoutRoot.classList.contains('sidebar-collapsed');
            layoutRoot.classList.toggle('sidebar-collapsed', willCollapse);
            localStorage.setItem(STORAGE_KEY, willCollapse ? '1' : '0');

            if (topbarCollapseBtn) {
                topbarCollapseBtn.textContent = willCollapse ? '»' : '«';
            }
        }

        if (sidebarCollapseBtn) {
            sidebarCollapseBtn.addEventListener('click', toggleSidebarCollapse);
        }
        if (topbarCollapseBtn) {
            topbarCollapseBtn.addEventListener('click', toggleSidebarCollapse);
            topbarCollapseBtn.textContent = isCollapsed ? '»' : '«';
        }

        // Mobile drawer toggling
        if (mobileToggleBtn) {
            mobileToggleBtn.addEventListener('click', function () {
                layoutRoot.classList.toggle('mobile-menu-open');
            });
        }
        if (backdrop) {
            backdrop.addEventListener('click', function () {
                layoutRoot.classList.remove('mobile-menu-open');
            });
        }

        // Close mobile drawer when clicking a nav item
        document.querySelectorAll('.sidebar-nav-item').forEach((item) => {
            item.addEventListener('click', function () {
                layoutRoot.classList.remove('mobile-menu-open');

                // If navigating to an in-page hash on the current page
                const href = item.getAttribute('href') || '';
                if (href.includes('#')) {
                    const hashPart = href.substring(href.indexOf('#'));
                    const targetEl = document.querySelector(hashPart);
                    if (targetEl) {
                        targetEl.scrollIntoView({ behavior: 'smooth' });
                        // Update active state
                        document.querySelectorAll('.sidebar-nav-item').forEach((n) => n.classList.remove('active'));
                        item.classList.add('active');
                    }
                }
            });
        });

        // Keyboard shortcut: [ toggles sidebar collapse
        document.addEventListener('keydown', function (e) {
            if (e.key === '[' && !['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) {
                e.preventDefault();
                toggleSidebarCollapse();
            }
            if (e.key === 'Escape' && layoutRoot.classList.contains('mobile-menu-open')) {
                layoutRoot.classList.remove('mobile-menu-open');
            }
        });

        // Sync researcher session if active
        try {
            const researcherSession = sessionStorage.getItem("bami_researcher_session");
            if (researcherSession) {
                document.querySelectorAll("[data-auth-user]").forEach((element) => {
                    element.textContent = researcherSession;
                    element.closest("[data-auth-user-container]")?.removeAttribute("hidden");
                });
                document.querySelectorAll("[data-auth-guest-container]").forEach((el) => {
                    el.style.display = "none";
                });
                document.querySelectorAll("[data-auth-logout]").forEach((btn) => {
                    btn.addEventListener("click", () => {
                        sessionStorage.removeItem("bami_researcher_session");
                        window.location.replace("login.html");
                    }, { once: true });
                });
            }
        } catch (_) {}

        // Watch for hash changes (e.g., #prediction vs #batch-screening)
        window.addEventListener('hashchange', function () {
            const newActiveId = getActiveItemId();
            document.querySelectorAll('.sidebar-nav-item').forEach((item) => {
                const match = item.dataset.id === newActiveId;
                item.classList.toggle('active', match);
                if (match) item.setAttribute('aria-current', 'page');
                else item.removeAttribute('aria-current');
            });
            const breadcrumbCurrent = document.querySelector('.topbar-breadcrumb-current');
            if (breadcrumbCurrent) {
                breadcrumbCurrent.textContent = getCurrentPageTitle(newActiveId);
            }
        });
    }

    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSidebar);
    } else {
        initSidebar();
    }
})();
