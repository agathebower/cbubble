const CATEGORY_ICONS = { cyber: "🔐", ai: "🤖", dev: "🛠️", offensive: "🕵️", threat_intel: "📡" };
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
            if (s.category) url += `&category=${s.category}`;
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
        tile.className = "tile"; tile.dataset.id = story.id; tile.dataset.url = story.url;
        const icon = CATEGORY_ICONS[story.category] || "📰";
        const timeAgo = this.timeAgo(story.published_at || story.fetched_at);
        let imageHTML = story.image_url
            ? `<img class="tile-image" src="${this.esc(story.image_url)}" alt="" loading="lazy" onerror="this.outerHTML='<div class=\\'tile-image-placeholder\\'>${icon}</div>'">`
            : `<div class="tile-image-placeholder">${icon}</div>`;
        tile.innerHTML = `${imageHTML}
            <div class="tile-body">
                <div class="tile-meta">
                    <span class="tile-source">${this.esc(story.source_name)}</span>
                    <span class="tile-time">${timeAgo}</span>
                    <span class="tile-category">${story.category.replace("_", " ")}</span>
                </div>
                <h3 class="tile-title">${this.esc(story.title)}</h3>
                <div class="tile-status">
                    <span class="status-dot ${story.abstract_status}"></span>
                    <span class="status-label">${story.abstract_status}</span>
                </div>
            </div>`;
        tile.addEventListener("click", (e) => { e.preventDefault(); Popup.open(story); });
        feed.appendChild(tile);
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
    esc(s) { if (!s) return ""; const d = document.createElement("div"); d.textContent = s; return d.innerHTML; },
};
