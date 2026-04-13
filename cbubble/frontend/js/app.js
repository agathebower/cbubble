const App = {
    state: { page: 1, loading: false, hasMore: true, category: null, stories: [], search: "" },
    async init() {
        Theme.init();
        await this.loadCategories();
        await Feed.loadPage();
        this.bindEvents();
        this.registerSW();
    },
    bindEvents() {
        document.getElementById("btn-refresh").addEventListener("click", () => this.refresh());
        document.getElementById("btn-retry")?.addEventListener("click", () => this.refresh());
        document.getElementById("btn-theme").addEventListener("click", () => Theme.toggle());
        document.getElementById("btn-stats").addEventListener("click", () => Stats.open());
        document.getElementById("search-input").addEventListener("input", (e) => {
            this.state.search = e.target.value.trim().toLowerCase();
            Feed.applySearch();
        });
    },
    async loadCategories() {
        try {
            const resp = await fetch("/api/categories");
            const data = await resp.json();
            const nav = document.getElementById("category-tabs");
            const bookmarksTab = document.getElementById("tab-bookmarks");
            data.categories.forEach(cat => {
                const btn = document.createElement("button");
                btn.className = "cat-tab"; btn.dataset.category = cat;
                btn.textContent = cat.replace("_", " ");
                btn.addEventListener("click", () => this.setCategory(cat, btn));
                nav.insertBefore(btn, bookmarksTab);
            });
            nav.querySelector('[data-category="all"]').addEventListener("click", (e) => this.setCategory(null, e.target));
            bookmarksTab.addEventListener("click", () => this.setCategory("bookmarks", bookmarksTab));
        } catch (e) { console.error("Failed to load categories:", e); }
    },
    setCategory(cat, btn) {
        document.querySelectorAll(".cat-tab").forEach(t => t.classList.remove("active"));
        btn.classList.add("active");
        this.state.category = cat; this.state.page = 1;
        this.state.hasMore = true; this.state.stories = [];
        document.getElementById("feed").innerHTML = "";
        if (cat === "bookmarks") { Feed.renderBookmarks(); }
        else { Feed.loadPage(); }
    },
    async refresh() {
        this.state.page = 1; this.state.hasMore = true; this.state.stories = [];
        document.getElementById("feed").innerHTML = "";
        try { await fetch("/api/reload", { method: "POST" }); } catch (_) {}
        await Feed.loadPage();
    },
    registerSW() {
        if ("serviceWorker" in navigator)
            navigator.serviceWorker.register("/sw.js").catch(e => console.warn("SW fail:", e));
    },
};

const Theme = {
    key: "cbubble_theme",
    init() { this.apply(localStorage.getItem(this.key) || "dark"); },
    toggle() {
        const next = (document.documentElement.getAttribute("data-theme") || "dark") === "dark" ? "light" : "dark";
        this.apply(next);
        localStorage.setItem(this.key, next);
    },
    apply(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        document.getElementById("icon-moon")?.classList.toggle("hidden", theme === "light");
        document.getElementById("icon-sun")?.classList.toggle("hidden", theme === "dark");
    },
};

const Bookmarks = {
    key: "cbubble_bookmarks",
    get() { try { return JSON.parse(localStorage.getItem(this.key) || "[]"); } catch { return []; } },
    save(list) { localStorage.setItem(this.key, JSON.stringify(list)); },
    has(id) { return this.get().some(s => s.id === id); },
    toggle(story) {
        const list = this.get();
        const idx = list.findIndex(s => s.id === story.id);
        if (idx >= 0) { list.splice(idx, 1); this.save(list); return false; }
        list.push(story); this.save(list); return true;
    },
};

const Stats = {
    async open() {
        const overlay = document.getElementById("stats-overlay");
        const content = document.getElementById("stats-content");
        overlay.classList.remove("hidden");
        content.textContent = "Loading…";
        overlay.querySelector(".stats-close").onclick = () => overlay.classList.add("hidden");
        overlay.onclick = (e) => { if (e.target === overlay) overlay.classList.add("hidden"); };
        try {
            const data = await fetch("/api/stats").then(r => r.json());
            const fmt = (n) => n.toLocaleString();
            let html = `<div class="stats-section"><div class="stats-section-title">Overview</div>`;
            html += `<div class="stats-row"><span>Total stories</span><strong>${fmt(data.total)}</strong></div>`;
            if (data.latest_fetch) {
                const d = new Date(data.latest_fetch);
                html += `<div class="stats-row"><span>Latest fetch</span><strong>${d.toLocaleString()}</strong></div>`;
            }
            html += `</div><div class="stats-section"><div class="stats-section-title">By status</div>`;
            for (const [status, count] of Object.entries(data.by_status || {})) {
                html += `<div class="stats-row"><span>${status}</span><strong>${fmt(count)}</strong></div>`;
            }
            html += `</div><div class="stats-section"><div class="stats-section-title">By category</div>`;
            for (const [cat, count] of Object.entries(data.by_category || {})) {
                html += `<div class="stats-row"><span>${cat.replace("_", " ")}</span><strong>${fmt(count)}</strong></div>`;
            }
            html += `</div>`;
            content.innerHTML = html;
        } catch (e) { content.textContent = "Failed to load stats."; }
    },
};

document.addEventListener("DOMContentLoaded", () => App.init());
