const App = {
    state: { page: 1, loading: false, hasMore: true, category: null, stories: [] },
    async init() {
        await this.loadCategories();
        await Feed.loadPage();
        this.bindEvents();
        this.registerSW();
    },
    bindEvents() {
        document.getElementById("btn-refresh").addEventListener("click", () => this.refresh());
        document.getElementById("btn-retry")?.addEventListener("click", () => this.refresh());
    },
    async loadCategories() {
        try {
            const resp = await fetch("/api/categories");
            const data = await resp.json();
            const nav = document.getElementById("category-tabs");
            data.categories.forEach(cat => {
                const btn = document.createElement("button");
                btn.className = "cat-tab"; btn.dataset.category = cat;
                btn.textContent = cat.replace("_", " ");
                btn.addEventListener("click", () => this.setCategory(cat, btn));
                nav.appendChild(btn);
            });
            nav.querySelector('[data-category="all"]').addEventListener("click", (e) => {
                this.setCategory(null, e.target);
            });
        } catch (e) { console.error("Failed to load categories:", e); }
    },
    setCategory(cat, btn) {
        document.querySelectorAll(".cat-tab").forEach(t => t.classList.remove("active"));
        btn.classList.add("active");
        this.state.category = cat; this.state.page = 1;
        this.state.hasMore = true; this.state.stories = [];
        document.getElementById("feed").innerHTML = "";
        Feed.loadPage();
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
document.addEventListener("DOMContentLoaded", () => App.init());
