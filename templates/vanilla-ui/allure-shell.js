(function () {
  const RESIZE_MESSAGE = "allure-shell:resize";
  const RESPONSIVE_BREAKPOINT_PX = 768;
  const LAYOUT_SYNC_STYLE_ID = "shell-layout-sync";
  const NARROW_DASHBOARD_LAYOUT_CSS = `
[class*="styles_grid__"] {
  grid-template-columns: 1fr !important;
  width: 100% !important;
}
[class*="styles_grid-item__"] {
  grid-template-columns: 1fr !important;
  width: 100% !important;
}
[class*="styles_widget__"] {
  width: 100% !important;
  max-width: 100% !important;
}
`;
  const BASE_SCRIPT_RE =
    /<script>\s*const \{ origin, pathname \} = window\.location;[\s\S]*?appendChild\(baseEl\);\s*<\/script>\s*/m;

  function measureDocument(doc) {
    if (!doc) return 0;
    return Math.max(
      doc.documentElement?.scrollHeight || 0,
      doc.body?.scrollHeight || 0,
      doc.documentElement?.offsetHeight || 0
    );
  }

  function measureFrame(frame) {
    try {
      const doc = frame.contentDocument || frame.contentWindow?.document;
      return measureDocument(doc);
    } catch {
      return 0;
    }
  }

  function notifyParentResize() {
    if (window.parent === window) return;
    window.parent.postMessage(
      { type: RESIZE_MESSAGE, height: measureDocument(document) },
      "*"
    );
  }

  function resizeFrame(frame) {
    const height = measureFrame(frame);
    if (height > 0) {
      frame.style.height = `${height}px`;
      frame.style.minHeight = "0";
    }
    notifyParentResize();
  }

  function getDashboardDocument(frame) {
    if (!frame) return null;
    try {
      return frame.contentDocument || frame.contentWindow?.document || null;
    } catch {
      return null;
    }
  }

  function readStoredTheme(rawValue) {
    if (!rawValue) return null;
    try {
      return JSON.parse(rawValue);
    } catch {
      return rawValue.replace(/^"|"$/g, "");
    }
  }

  function updateMetricsPanel(theme) {
    const img = document.getElementById("metrics-panel-img");
    if (!img) return;

    const normalized = theme === "dark" ? "dark" : "light";
    const nextSrc =
      img.dataset[normalized === "dark" ? "srcDark" : "srcLight"] ||
      img.getAttribute("src")?.replace(/-dark(?=\.svg$)/, "") ||
      "";
    const resolvedSrc =
      normalized === "dark" && nextSrc.endsWith(".svg") && !nextSrc.endsWith("-dark.svg")
        ? nextSrc.replace(/\.svg$/, "-dark.svg")
        : nextSrc;

    if (resolvedSrc && img.getAttribute("src") !== resolvedSrc) {
      img.setAttribute("src", resolvedSrc);
    }
  }

  function applySiteTheme(theme) {
    const normalized = theme === "dark" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", normalized);
    updateMetricsPanel(normalized);
    return normalized;
  }

  function initSiteTheme() {
    applySiteTheme(localStorage.getItem("site-theme") === "dark" ? "dark" : "light");
  }

  function getDashboardTheme(frame) {
    const doc = getDashboardDocument(frame);
    if (doc) {
      const stored = readStoredTheme(doc.defaultView?.localStorage?.getItem("theme"));
      if (stored === "dark" || stored === "light") {
        return stored;
      }
      const attrTheme = doc.documentElement.getAttribute("data-theme");
      if (attrTheme === "dark" || attrTheme === "light") {
        return attrTheme;
      }
    }

    const siteTheme = localStorage.getItem("site-theme");
    return siteTheme === "dark" ? "dark" : "light";
  }

  function applyDashboardTheme(frame, theme) {
    const normalized = theme === "dark" ? "dark" : "light";
    localStorage.setItem("site-theme", normalized);
    applySiteTheme(normalized);

    const doc = getDashboardDocument(frame);
    if (doc) {
      doc.documentElement.setAttribute("data-theme", normalized);
      doc.defaultView?.localStorage?.setItem("theme", JSON.stringify(normalized));
    }

    window.dispatchEvent(
      new CustomEvent("dashboard-theme-change", { detail: { theme: normalized } })
    );
    return normalized;
  }

  function toggleDashboardTheme(frame) {
    const nextTheme = getDashboardTheme(frame) === "dark" ? "light" : "dark";
    return applyDashboardTheme(frame, nextTheme);
  }

  function isNarrowShellLayout() {
    return window.matchMedia(`(max-width: ${RESPONSIVE_BREAKPOINT_PX}px)`).matches;
  }

  function syncShellLayoutAttribute() {
    document.documentElement.dataset.shellLayout = isNarrowShellLayout() ? "narrow" : "wide";
  }

  function applyDashboardLayout(frame) {
    const doc = getDashboardDocument(frame);
    if (!doc) return;

    const narrow = isNarrowShellLayout();
    doc.documentElement.dataset.shellLayout = narrow ? "narrow" : "wide";

    let style = doc.getElementById(LAYOUT_SYNC_STYLE_ID);
    if (!style) {
      style = doc.createElement("style");
      style.id = LAYOUT_SYNC_STYLE_ID;
      doc.head.appendChild(style);
    }
    style.textContent = narrow ? NARROW_DASHBOARD_LAYOUT_CSS : "";
    resizeFrame(frame);
  }

  function syncDashboardLayouts() {
    document.querySelectorAll("iframe.dashboard-frame").forEach(applyDashboardLayout);
  }

  function getOverridesUrl() {
    const shellScript = document.querySelector('script[src*="allure-shell.js"]');
    if (shellScript?.src) {
      return new URL("dashboard-overrides.css", shellScript.src).href;
    }
    return new URL("dashboard-overrides.css", document.baseURI).href;
  }

  function prepareDashboardHtml(html, dashboardUrl, overridesUrl) {
    const dashboardBase = new URL("./", dashboardUrl).href;
    let patched = html.replace(BASE_SCRIPT_RE, "");

    if (!patched.includes("dashboard-overrides")) {
      const overrideTag = `<link rel="stylesheet" type="text/css" href="${overridesUrl}" data-dashboard-overrides>`;
      patched = patched.replace("</head>", `    ${overrideTag}\n</head>`);
    }

    if (!/<base\s/i.test(patched)) {
      patched = patched.replace("<head>", `<head>\n    <base href="${dashboardBase}">`);
    }

    return patched;
  }

  async function loadDashboardFrame(frame, dashboardUrl) {
    const absoluteDashboardUrl = new URL(dashboardUrl, document.baseURI).href;
    const overridesUrl = getOverridesUrl();

    frame.dataset.dashboardUrl = absoluteDashboardUrl;

    try {
      const response = await fetch(absoluteDashboardUrl, { cache: "no-cache" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const html = await response.text();
      frame.removeAttribute("src");
      frame.srcdoc = prepareDashboardHtml(html, absoluteDashboardUrl, overridesUrl);
    } catch {
      frame.removeAttribute("srcdoc");
      frame.src = absoluteDashboardUrl;
    }
  }

  function setupFrame(frame) {
    frame.setAttribute("scrolling", "no");

    const onLoad = () => {
      applyDashboardTheme(frame, getDashboardTheme(frame));
      applyDashboardLayout(frame);
      resizeFrame(frame);
      [300, 800, 1500, 3000].forEach((delay) => {
        window.setTimeout(() => resizeFrame(frame), delay);
      });
    };

    frame.addEventListener("load", onLoad);
    try {
      if (frame.contentDocument?.readyState === "complete") {
        onLoad();
      }
    } catch {
      // ignore cross-origin access errors
    }
  }

  function initDashboardFrames() {
    document.querySelectorAll("iframe.dashboard-frame").forEach((frame) => {
      if (frame.dataset.dashboardReady === "true") {
        setupFrame(frame);
        return;
      }

      const dashboardUrl = frame.dataset.dashboardUrl || frame.getAttribute("src");
      if (dashboardUrl) {
        loadDashboardFrame(frame, dashboardUrl).finally(() => {
          frame.dataset.dashboardReady = "true";
          setupFrame(frame);
        });
        return;
      }
      setupFrame(frame);
    });
    notifyParentResize();
  }

  window.addEventListener("message", (event) => {
    if (event.data?.type !== RESIZE_MESSAGE) return;

    document.querySelectorAll("iframe.dashboard-frame").forEach((frame) => {
      try {
        if (frame.contentWindow === event.source) {
          const height = event.data.height;
          if (height > 0) {
            frame.style.height = `${height}px`;
            frame.style.minHeight = "0";
          }
        }
      } catch {
        // ignore
      }
    });

    notifyParentResize();
  });

  function getPageLang() {
    return new URLSearchParams(window.location.search).has("ru") ? "ru" : "en";
  }

  function buildLangUrl(lang) {
    const url = new URL(window.location.href);
    url.searchParams.delete("ru");
    if (lang === "ru") {
      url.searchParams.set("ru", "");
    }
    return `${url.pathname}${url.search}${url.hash}`;
  }

  function resolveSiteTheme(getSiteTheme) {
    if (typeof getSiteTheme === "function") {
      return getSiteTheme();
    }
    const dashboardFrame = document.getElementById("dashboard-frame");
    if (dashboardFrame) {
      return getDashboardTheme(dashboardFrame);
    }
    return localStorage.getItem("site-theme") === "dark" ? "dark" : "light";
  }

  function updateThemeToggle(t, theme) {
    const toggle = document.getElementById("theme-toggle");
    const icon = toggle?.querySelector(".theme-icon");
    if (!toggle || !icon) return;

    const isDark = theme === "dark";
    icon.innerHTML = isDark
      ? '<circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="1.6"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"></path>'
      : '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"></path>';
    toggle.setAttribute("aria-label", isDark ? t.themeLight : t.themeDark);
  }

  function closeLangMenu() {
    const toggle = document.getElementById("lang-toggle");
    const menu = document.getElementById("lang-menu");
    if (!toggle || !menu) return;
    menu.classList.remove("is-open");
    menu.setAttribute("aria-hidden", "true");
    toggle.setAttribute("aria-expanded", "false");
  }

  function applyHeaderI18n(t, langQuery) {
    const burger = document.querySelector(".burger-menu");
    if (burger && t.navMenu) burger.setAttribute("aria-label", t.navMenu);

    const nav = document.querySelector(".nav");
    if (nav && t.navMain) nav.setAttribute("aria-label", t.navMain);

    const navLinks = {
      "clubs-link": { href: "text-box.html", text: t.navTextBox },
      "create-club-link": { href: "automation-practice-form.html", text: t.navRegistration },
      "login-link": { href: "login.html", text: t.navLogin },
      "sandbox-link": { href: "sandbox.html", text: t.navSandbox },
      "drawer-clubs-link": { href: "text-box.html", text: t.navTextBox },
      "drawer-create-club-link": { href: "automation-practice-form.html", text: t.navRegistration },
      "drawer-login-link": { href: "login.html", text: t.navLogin },
      "drawer-sandbox-link": { href: "sandbox.html", text: t.navSandbox },
    };

    Object.entries(navLinks).forEach(([testId, { href, text }]) => {
      if (!text) return;
      const link = document.querySelector(`[data-testid="${testId}"]`);
      if (!link) return;
      link.href = href + langQuery;
      link.textContent = text;
    });

    const formsText = t.navForms || "Forms";
    const formsLink = document.querySelector('[data-testid="forms-link"]');
    if (formsLink) {
      formsLink.href = "index.html" + langQuery;
      formsLink.textContent = formsText;
    }

    const drawerFormsLink = document.querySelector('[data-testid="drawer-forms-link"]');
    if (drawerFormsLink) {
      drawerFormsLink.href = "index.html" + langQuery;
      drawerFormsLink.textContent = formsText;
    }

    const githubLink = document.querySelector('[data-testid="github-link"]');
    if (githubLink && t.navGithub) githubLink.setAttribute("aria-label", t.navGithub);

    const githubIoLink = document.querySelector('[data-testid="github-io-link"]');
    if (githubIoLink && t.navGithubPages) githubIoLink.setAttribute("aria-label", t.navGithubPages);

    const langLabel = document.getElementById("lang-label");
    if (langLabel) {
      langLabel.textContent = getPageLang() === "ru" ? t.langRu : t.langEng;
    }

    document.querySelectorAll("#lang-menu [data-lang]").forEach((option) => {
      const optionLang = option.getAttribute("data-lang");
      const isActive = optionLang === getPageLang();
      option.setAttribute("aria-selected", isActive ? "true" : "false");
      option.textContent = optionLang === "ru" ? t.langRu : t.langEng;
      option.href = buildLangUrl(optionLang);
    });
  }

  function setActiveNavLink() {
    const currentPath = window.location.pathname.split("/").pop() || "index.html";
    document
      .querySelectorAll(
        ".header-left .form-nav-home, .header-left .form-nav .nav-link, .nav-drawer-links .nav-link"
      )
      .forEach((link) => {
        const href = link.getAttribute("href").split("?")[0];
        const isActive = href === currentPath;
        link.classList.toggle("active", isActive);
        if (isActive) {
          link.setAttribute("aria-current", "page");
        } else {
          link.removeAttribute("aria-current");
        }
      });
  }

  function initHeaderTools(getSiteTheme) {
    const langToggle = document.getElementById("lang-toggle");
    const langMenu = document.getElementById("lang-menu");
    const themeToggle = document.getElementById("theme-toggle");
    const dashboardFrame = document.getElementById("dashboard-frame");

    if (langToggle && langMenu) {
      langToggle.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const isOpen = !langMenu.classList.contains("is-open");
        langMenu.classList.toggle("is-open", isOpen);
        langMenu.setAttribute("aria-hidden", isOpen ? "false" : "true");
        langToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
      });

      document.addEventListener("click", (event) => {
        if (!langToggle.contains(event.target) && !langMenu.contains(event.target)) {
          closeLangMenu();
        }
      });

      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeLangMenu();
      });
    }

    if (themeToggle) {
      themeToggle.addEventListener("click", () => {
        const nextTheme = dashboardFrame
          ? toggleDashboardTheme(dashboardFrame)
          : (() => {
              const theme = localStorage.getItem("site-theme") === "dark" ? "light" : "dark";
              applySiteTheme(theme);
              window.dispatchEvent(
                new CustomEvent("dashboard-theme-change", { detail: { theme } })
              );
              return theme;
            })();
        const lang = getPageLang();
        const translations = window.__demoHeaderI18n?.[lang];
        if (translations) updateThemeToggle(translations, nextTheme);
      });
    }

    window.addEventListener("dashboard-theme-change", (event) => {
      const lang = getPageLang();
      const translations = window.__demoHeaderI18n?.[lang];
      if (translations) {
        updateThemeToggle(translations, event.detail?.theme || resolveSiteTheme(getSiteTheme));
      }
    });
  }

  function initBurgerMenu() {
    const burger = document.querySelector(".burger-menu");
    const nav = document.querySelector(".nav");
    const overlay = document.querySelector(".nav-overlay");
    const links = document.querySelectorAll(".nav-link");

    function closeMenu() {
      if (!burger || !nav || !overlay) return;
      burger.classList.remove("active");
      nav.classList.remove("active");
      overlay.classList.remove("active");
      burger.setAttribute("aria-expanded", "false");
      closeLangMenu();
    }

    if (burger && nav && overlay) {
      burger.addEventListener("click", () => {
        const isOpen = !burger.classList.contains("active");
        burger.classList.toggle("active", isOpen);
        nav.classList.toggle("active", isOpen);
        overlay.classList.toggle("active", isOpen);
        burger.setAttribute("aria-expanded", isOpen ? "true" : "false");
      });

      overlay.addEventListener("click", closeMenu);
      window.matchMedia(`(max-width: ${RESPONSIVE_BREAKPOINT_PX}px)`).addEventListener("change", closeMenu);
    }

    links.forEach((link) => {
      link.addEventListener("click", closeMenu);
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeMenu();
    });
  }

  function initDemoHeader({ i18n, applyPage, getSiteTheme } = {}) {
    if (!i18n) return;

    window.__demoHeaderI18n = i18n;
    const lang = getPageLang();
    const langQuery = lang === "ru" ? "?ru" : "";
    const t = i18n[lang] || i18n.en;

    function applyAll() {
      document.documentElement.lang = lang;
      if (t.pageTitle) document.title = t.pageTitle;
      applyHeaderI18n(t, langQuery);
      applyPage?.(t, lang, langQuery);
      updateThemeToggle(t, resolveSiteTheme(getSiteTheme));
    }

    applyAll();
    initHeaderTools(getSiteTheme);
    setActiveNavLink();

    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", initBurgerMenu);
    } else {
      initBurgerMenu();
    }
  }

  initSiteTheme();
  syncShellLayoutAttribute();

  window.AllureShell = {
    loadDashboardFrame,
    resizeFrame,
    applySiteTheme,
    applyDashboardTheme,
    getDashboardTheme,
    toggleDashboardTheme,
    responsiveBreakpointPx: RESPONSIVE_BREAKPOINT_PX,
    isNarrowShellLayout,
    syncShellLayoutAttribute,
    syncDashboardLayouts,
    initDemoHeader,
    buildLangUrl,
    getPageLang,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDashboardFrames);
  } else {
    initDashboardFrames();
  }

  window.addEventListener("resize", () => {
    syncShellLayoutAttribute();
    syncDashboardLayouts();
    document.querySelectorAll("iframe.dashboard-frame").forEach(resizeFrame);
    notifyParentResize();
  });
})();
