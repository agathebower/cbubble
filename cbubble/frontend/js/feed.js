const CATEGORY_ICONS = { cyber: "🔐", ai: "🤖", dev: "🛠️", offensive: "🕵️", threat_intel: "📡" };
// VALID_ABSTRACT_STATUSES and safeStatus() are defined in popup.js (loaded after this file)

const Feed = {
    observer: null,
    async loadPage() {
        const s = App.state;
        if (s.loading || !s.hasMore) return;
        s.loading = true;
        const loader = document.getElementById("loader");
        const empty = document.getElementById("empty-state");
        loader.classList.remove("hidden"); empty.classList.add("hidden");
        try {
            let url = `/api/stories?page=${s.page}&limit=20`;
            if (s.category) url += `&category=${encodeURIComponent(s.category)}`;
            const resp = await fetch(url);
            const data = await resp.json();
            const stories = data.stories || [];
            if (stories.length === 0 && s.page === 1) empty.classList.remove("hidden");
            if (stories.length < 20) s.hasMore = false;
            stories.forEach(story => { s.stories.push(story); this.renderTile(story); });
            s.page++;
        } catch (e) { console.error("Failed to load stories:", e); }
        finally { s.loading = false; loader.classList.toggle("hidden", !s.hasMore); this.observeScroll(); }
    },
    renderTile(story) {
        const feed = document.getElementById("feed");
        const tile = document.createElement("article");
        tile.className = "tile";
        tile.dataset.id = story.id;
        tile.setAttribute("role", "button");
        tile.setAttribute("tabindex", "0");

        const icon = CATEGORY_ICONS[story.category] || "📰";
        const timeAgo = this.timeAgo(story.published_at || story.fetched_at);

        // Safe status class: safeStatus() is defined in popup.js
        const status = safeStatus(story.abstract_status);

        // Build structure with DOM methods — no innerHTML with untrusted data
        let imageEl;
        if (story.image_url && this.isSafeUrl(story.image_url)) {
            imageEl = document.createElement("img");
            imageEl.className = "tile-image";
            imageEl.src = story.image_url;
            imageEl.alt = "";
            imageEl.loading = "lazy";
            imageEl.onerror = function () {
                const placeholder = document.createElement("div");
                placeholder.className = "tile-image-placeholder";
                placeholder.textContent = icon;
                this.replaceWith(placeholder);
            };
        } else {
            imageEl = document.createElement("div");
            imageEl.className = "tile-image-placeholder";
            imageEl.textContent = icon;
        }

        const body = document.createElement("div");
        body.className = "tile-body";

        const meta = document.createElement("div");
        meta.className = "tile-meta";

        const sourceSpan = document.createElement("span");
        sourceSpan.className = "tile-source";
        sourceSpan.textContent = story.source_name;

        const timeSpan = document.createElement("span");
        timeSpan.className = "tile-time";
        timeSpan.textContent = timeAgo;

        const catSpan = document.createElement("span");
        catSpan.className = "tile-category";
        catSpan.textContent = story.category.replace("_", " ");

        meta.append(sourceSpan, timeSpan, catSpan);

        const titleEl = document.createElement("h3");
        titleEl.className = "tile-title";
        titleEl.textContent = story.title;

        const statusDiv = document.createElement("div");
        statusDiv.className = "tile-status";

        const dot = document.createElement("span");
        dot.className = `status-dot ${status}`;

        const label = document.createElement("span");
        label.className = "status-label";
        label.textContent = status;

        statusDiv.append(dot, label);
        body.append(meta, titleEl, statusDiv);
        tile.append(imageEl, body);

        tile.addEventListener("click", (e) => { e.preventDefault(); Popup.open(story); });
        // iOS Safari fallback: touchend fires more reliably than click on non-interactive elements
        let touchMoved = false;
        tile.addEventListener("touchstart", () => { touchMoved = false; }, { passive: true });
        tile.addEventListener("touchmove", () => { touchMoved = true; }, { passive: true });
        tile.addEventListener("touchend", (e) => { if (!touchMoved) { e.preventDefault(); Popup.open(story); } });
        feed.appendChild(tile);
    },
    isSafeUrl(url) {
        try {
            const u = new URL(url);
            return u.protocol === "https:" || u.protocol === "http:";
        } catch { return false; }
    },
    observeScroll() {
        if (this.observer) this.observer.disconnect();
        const loader = document.getElementById("loader");
        if (!App.state.hasMore) return;
        this.observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) this.loadPage();
        }, { rootMargin: "300px" });
        this.observer.observe(loader);
    },
    timeAgo(dateStr) {
        if (!dateStr) return "";
        try {
            const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
            if (diff < 60) return "just now";
            if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
            if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
            if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
            return new Date(dateStr).toLocaleDateString();
        } catch { return ""; }
    },
};
