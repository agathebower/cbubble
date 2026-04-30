const VALID_ABSTRACT_STATUSES = new Set(["pending", "verified", "unverified", "flagged", "skipped", "error"]);

function safeUrl(url) {
    try {
        const u = new URL(url);
        return (u.protocol === "https:" || u.protocol === "http:") ? url : "#";
    } catch { return "#"; }
}

function safeStatus(status) {
    return VALID_ABSTRACT_STATUSES.has(status) ? status : "pending";
}

const Popup = {
    overlay: null, currentStory: null,
    init() {
        this.overlay = document.getElementById("popup-overlay");
        this.overlay.querySelector(".popup-close").addEventListener("click", () => this.close());
        this.overlay.addEventListener("click", (e) => { if (e.target === this.overlay) this.close(); });
        document.addEventListener("keydown", (e) => { if (e.key === "Escape") this.close(); });

        document.getElementById("btn-popup-bookmark").addEventListener("click", () => {
            if (!this.currentStory) return;
            const saved = Bookmarks.toggle(this.currentStory);
            const btn = document.getElementById("btn-popup-bookmark");
            btn.textContent = saved ? "★ Saved" : "🔖 Save";
            btn.classList.toggle("saved", saved);
            // sync tile bookmark button
            const tile = document.querySelector(`.tile[data-id="${this.currentStory.id}"]`);
            const tileBtn = tile?.querySelector(".tile-bookmark");
            if (tileBtn) {
                tileBtn.textContent = saved ? "★" : "☆";
                tileBtn.classList.toggle("saved", saved);
            }
        });

        document.getElementById("btn-popup-share").addEventListener("click", () => {
            if (!this.currentStory) return;
            const url = safeUrl(this.currentStory.url);
            const title = this.currentStory.title;
            if (navigator.share) {
                navigator.share({ title, url }).catch(() => {});
            } else {
                navigator.clipboard.writeText(url).then(() => {
                    const btn = document.getElementById("btn-popup-share");
                    const orig = btn.textContent;
                    btn.textContent = "✓ Copied!";
                    setTimeout(() => { btn.textContent = orig; }, 2000);
                }).catch(() => {});
            }
        });
    },
    async open(story) {
        this.currentStory = story;
        const o = this.overlay;
        o.querySelector(".popup-source").textContent = story.source_name;
        o.querySelector(".popup-title").textContent = story.title;
        o.querySelector(".popup-link").href = safeUrl(story.url);
        const badge = o.querySelector(".popup-badge");
        const status = safeStatus(story.abstract_status);
        badge.textContent = status;
        badge.className = `popup-badge ${status}`;
        const textEl = o.querySelector(".popup-text");
        const loadingEl = o.querySelector(".popup-loading");
        const noteEl = o.querySelector(".popup-verification-note");
        noteEl.classList.add("hidden");

        // Bookmark button state
        const bookmarkBtn = document.getElementById("btn-popup-bookmark");
        const isSaved = Bookmarks.has(story.id);
        bookmarkBtn.textContent = isSaved ? "★ Saved" : "🔖 Save";
        bookmarkBtn.classList.toggle("saved", isSaved);

        // Show overlay immediately — don't wait for async fetch
        o.classList.remove("hidden"); document.body.style.overflow = "hidden";

        if (story.abstract && story.abstract_status !== "pending") {
            loadingEl.classList.add("hidden");
            textEl.textContent = story.abstract; textEl.classList.remove("hidden");
        } else if (story.abstract_status === "skipped") {
            loadingEl.innerHTML = `No abstract available — not enough content. <button class="retry-btn" data-id="${story.id}">↺ Retry</button>`;
            loadingEl.classList.remove("hidden"); textEl.classList.add("hidden");
            loadingEl.querySelector(".retry-btn").addEventListener("click", async () => {
                const btn = loadingEl.querySelector(".retry-btn");
                btn.disabled = true; btn.textContent = "queuing…";
                const resp = await fetch(`/api/stories/${story.id}/prioritize`, { method: "POST" });
                if (resp.ok) {
                    loadingEl.textContent = "Queued ⚡ — abstract will be generated shortly.";
                    badge.textContent = "pending"; badge.className = "popup-badge pending";
                    if (this.currentStory) this.currentStory.abstract_status = "pending";
                } else {
                    btn.disabled = false; btn.textContent = "↺ Retry";
                }
            });
        } else {
            loadingEl.classList.remove("hidden"); textEl.classList.add("hidden");
            await this.fetchDetail(story.id, textEl, loadingEl, badge, noteEl);
        }
        if (story.verification_note && story.abstract_status === "flagged") {
            noteEl.querySelector("small").textContent = `⚠️ ${story.verification_note}`;
            noteEl.classList.remove("hidden");
        }
    },
    async fetchDetail(storyId, textEl, loadingEl, badge, noteEl) {
        try {
            const resp = await fetch(`/api/stories/${storyId}`);
            const d = await resp.json();
            if (d.abstract) {
                textEl.textContent = d.abstract; textEl.classList.remove("hidden");
                loadingEl.classList.add("hidden");
                const status = safeStatus(d.abstract_status);
                badge.textContent = status;
                badge.className = `popup-badge ${status}`;
                if (this.currentStory) {
                    this.currentStory.abstract = d.abstract;
                    this.currentStory.abstract_status = d.abstract_status;
                }
                if (d.verification_note && d.abstract_status === "flagged") {
                    noteEl.querySelector("small").textContent = `⚠️ ${d.verification_note}`;
                    noteEl.classList.remove("hidden");
                }
            } else {
                const s = d.abstract_status;
                if (s === "skipped") {
                    loadingEl.textContent = "No abstract available — not enough content.";
                } else if (s === "error") {
                    loadingEl.textContent = "Abstract generation failed.";
                } else {
                    loadingEl.textContent = "Abstract not yet available. Check back soon.";
                }
            }
        } catch (e) { loadingEl.textContent = "Failed to load abstract."; console.error(e); }
    },
    close() { this.overlay.classList.add("hidden"); document.body.style.overflow = ""; this.currentStory = null; },
};
document.addEventListener("DOMContentLoaded", () => Popup.init());
