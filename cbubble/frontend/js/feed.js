const CATEGORY_ICONS = { cyber: "🔐", ai: "🤖", dev: "🛠️", offensive: "🕵️", threat_intel: "📡" };

const SOURCE_FAVICONS = {
    "The Hacker News":       "thehackernews.com",
    "BleepingComputer":      "bleepingcomputer.com",
    "Dark Reading":          "darkreading.com",
    "SecurityWeek":          "securityweek.com",
    "Cybersecurity Dive":    "cybersecuritydive.com",
    "Simon Willison's Blog": "simonwillison.net",
    "Hugging Face Blog":     "huggingface.co",
    "LWN.net":               "lwn.net",
    "Lobsters":              "lobste.rs",
    "Hacker News":           "news.ycombinator.com",
    "PortSwigger Research":  "portswigger.net",
    "VulDB":                 "vuldb.com",
    "Exploit Database":      "exploit-db.com",
    "Krebs on Security":     "krebsonsecurity.com",
    "Recorded Future Blog":  "recordedfuture.com",
    "TLDR":                  "tldr.tech",
    "TLDR AI":               "tldr.tech",
    "TLDR DevOps":           "tldr.tech",
};
// safeStatus() is defined in popup.js (loaded after this file)

const LastVisit = {
    key: "cbubble_last_visit",
    timestamp: null,
    init() {
        this.timestamp = localStorage.getItem(this.key);
        window.addEventListener("pagehide", () => {
            localStorage.setItem(this.key, new Date().toISOString());
        });
    },
    isNew(fetchedAt) {
        if (!this.timestamp || !fetchedAt) return false;
        return new Date(fetchedAt) > new Date(this.timestamp);
    },
};

const Feed = {
    observer: null,
    async loadPage() {
        if (!LastVisit.timestamp) LastVisit.init();
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
        if (s.search) this.applySearch();
    },
    renderBookmarks() {
        const feed = document.getElementById("feed");
        feed.innerHTML = "";
        const list = Bookmarks.get();
        const empty = document.getElementById("empty-state");
        if (list.length === 0) {
            empty.querySelector("p").textContent = "No saved stories yet.";
            empty.classList.remove("hidden");
        } else {
            empty.classList.add("hidden");
            list.slice().reverse().forEach(story => this.renderTile(story));
        }
        document.getElementById("loader").classList.add("hidden");
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
        const status = safeStatus(story.abstract_status);

        const faviconDomain = SOURCE_FAVICONS[story.source_name];
        const faviconUrl = faviconDomain
            ? `https://www.google.com/s2/favicons?domain=${faviconDomain}&sz=64`
            : null;

        let imageEl;
        if (story.image_url && this.isSafeUrl(story.image_url)) {
            imageEl = document.createElement("img");
            imageEl.className = "tile-image";
            imageEl.src = story.image_url;
            imageEl.alt = "";
            imageEl.loading = "lazy";
            imageEl.onerror = function () {
                if (faviconUrl) {
                    const wrapper = document.createElement("div");
                    wrapper.className = "tile-image-placeholder";
                    const fav = document.createElement("img");
                    fav.src = faviconUrl;
                    fav.className = "tile-favicon";
                    fav.alt = "";
                    wrapper.appendChild(fav);
                    this.replaceWith(wrapper);
                } else {
                    const placeholder = document.createElement("div");
                    placeholder.className = "tile-image-placeholder";
                    placeholder.textContent = icon;
                    this.replaceWith(placeholder);
                }
            };
        } else if (faviconUrl) {
            imageEl = document.createElement("div");
            imageEl.className = "tile-image-placeholder";
            const fav = document.createElement("img");
            fav.src = faviconUrl;
            fav.className = "tile-favicon";
            fav.alt = "";
            imageEl.appendChild(fav);
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

        if (LastVisit.isNew(story.fetched_at)) {
            const badge = document.createElement("span");
            badge.className = "badge-new";
            badge.textContent = "NEW";
            titleEl.appendChild(badge);
        }

        const statusDiv = document.createElement("div");
        statusDiv.className = "tile-status";

        const dot = document.createElement("span");
        dot.className = `status-dot ${status}`;

        const label = document.createElement("span");
        label.className = "status-label";
        label.textContent = status;

        const bookmarkBtn = document.createElement("button");
        const isSaved = Bookmarks.has(story.id);
        bookmarkBtn.className = `tile-bookmark${isSaved ? " saved" : ""}`;
        bookmarkBtn.textContent = isSaved ? "★" : "☆";
        bookmarkBtn.title = isSaved ? "Remove bookmark" : "Save for later";
        bookmarkBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            const saved = Bookmarks.toggle(story);
            bookmarkBtn.textContent = saved ? "★" : "☆";
            bookmarkBtn.classList.toggle("saved", saved);
            bookmarkBtn.title = saved ? "Remove bookmark" : "Save for later";
            const popupBtn = document.getElementById("btn-popup-bookmark");
            if (popupBtn && Popup.currentStory?.id === story.id) {
                popupBtn.textContent = saved ? "★ Saved" : "🔖 Save";
                popupBtn.classList.toggle("saved", saved);
            }
        });

        const abstractMissing = !story.abstract ||
            story.abstract.trim() === "" ||
            story.abstract.startsWith("Abstract not yet available");

        const skipBtn = document.createElement("button");
        skipBtn.className = "tile-skip";
        skipBtn.textContent = "✕";
        skipBtn.title = "Skip this story";
        skipBtn.addEventListener("click", async (e) => {
            e.stopPropagation();
            skipBtn.disabled = true;
            try {
                const resp = await fetch(`/api/stories/${story.id}/skip`, { method: "POST" });
                if (resp.ok) {
                    tile.style.transition = "opacity 0.25s";
                    tile.style.opacity = "0";
                    setTimeout(() => tile.remove(), 250);
                } else {
                    skipBtn.disabled = false;
                }
            } catch {
                skipBtn.disabled = false;
            }
        });

        if (status === "pending") {
            const priorityBtn = document.createElement("button");
            priorityBtn.className = "tile-prioritize";
            priorityBtn.textContent = "⚡";
            priorityBtn.title = "Generate abstract next";
            priorityBtn.addEventListener("click", async (e) => {
                e.stopPropagation();
                priorityBtn.disabled = true;
                priorityBtn.title = "Queued";
                try {
                    const resp = await fetch(`/api/stories/${story.id}/prioritize`, { method: "POST" });
                    if (resp.ok) {
                        label.textContent = "next ⚡";
                    } else {
                        priorityBtn.disabled = false;
                    }
                } catch {
                    priorityBtn.disabled = false;
                }
            });
            statusDiv.append(dot, label, bookmarkBtn, priorityBtn, skipBtn);
        } else if (abstractMissing && (status === "error" || status === "skipped")) {
            const reprocessBtn = document.createElement("button");
            reprocessBtn.className = "tile-prioritize";
            reprocessBtn.textContent = "⚡";
            reprocessBtn.title = "Retry abstract generation";
            reprocessBtn.addEventListener("click", async (e) => {
                e.stopPropagation();
                reprocessBtn.disabled = true;
                reprocessBtn.textContent = "⏳";
                try {
                    const resp = await fetch(`/api/stories/${story.id}/reprocess`, { method: "POST" });
                    if (resp.ok) {
                        story.abstract_status = "pending";
                        label.textContent = "next ⚡";
                        dot.className = "status-dot pending";
                        setTimeout(() => App.refresh(), 3000);
                    } else {
                        reprocessBtn.disabled = false;
                        reprocessBtn.textContent = "⚡";
                    }
                } catch {
                    reprocessBtn.disabled = false;
                    reprocessBtn.textContent = "⚡";
                }
            });
            if (status === "skipped") {
                statusDiv.append(dot, label, bookmarkBtn, reprocessBtn);
            } else {
                statusDiv.append(dot, label, bookmarkBtn, reprocessBtn, skipBtn);
            }
        } else {
            if (status !== "skipped") {
                statusDiv.append(dot, label, bookmarkBtn, skipBtn);
            } else {
                statusDiv.append(dot, label, bookmarkBtn);
            }
        }
        body.append(meta, titleEl, statusDiv);
        tile.append(imageEl, body);

        tile.addEventListener("click", (e) => { e.preventDefault(); Popup.open(story); });
        let touchMoved = false;
        tile.addEventListener("touchstart", () => { touchMoved = false; }, { passive: true });
        tile.addEventListener("touchmove", () => { touchMoved = true; }, { passive: true });
        tile.addEventListener("touchend", (e) => { if (!touchMoved) { e.preventDefault(); Popup.open(story); } });
        feed.appendChild(tile);
    },
    applySearch() {
        const term = App.state.search;
        document.querySelectorAll(".tile").forEach(tile => {
            if (!term) { tile.hidden = false; return; }
            const id = parseInt(tile.dataset.id);
            const story = App.state.stories.find(s => s.id === id);
            if (!story) { tile.hidden = false; return; }
            tile.hidden = !(
                story.title.toLowerCase().includes(term) ||
                story.source_name.toLowerCase().includes(term) ||
                story.category.toLowerCase().includes(term)
            );
        });
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
        if (!App.state.hasMore || App.state.category === "bookmarks") return;
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
