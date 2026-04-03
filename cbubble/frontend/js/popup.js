const Popup = {
    overlay: null, currentStory: null,
    init() {
        this.overlay = document.getElementById("popup-overlay");
        this.overlay.querySelector(".popup-close").addEventListener("click", () => this.close());
        this.overlay.addEventListener("click", (e) => { if (e.target === this.overlay) this.close(); });
        document.addEventListener("keydown", (e) => { if (e.key === "Escape") this.close(); });
    },
    async open(story) {
        this.currentStory = story;
        const o = this.overlay;
        o.querySelector(".popup-source").textContent = story.source_name;
        o.querySelector(".popup-title").textContent = story.title;
        o.querySelector(".popup-link").href = story.url;
        const badge = o.querySelector(".popup-badge");
        badge.textContent = story.abstract_status;
        badge.className = `popup-badge ${story.abstract_status}`;
        const textEl = o.querySelector(".popup-text");
        const loadingEl = o.querySelector(".popup-loading");
        const noteEl = o.querySelector(".popup-verification-note");
        noteEl.classList.add("hidden");
        if (story.abstract && story.abstract_status !== "pending") {
            loadingEl.classList.add("hidden");
            textEl.textContent = story.abstract; textEl.classList.remove("hidden");
        } else {
            loadingEl.classList.remove("hidden"); textEl.classList.add("hidden");
            await this.fetchDetail(story.id, textEl, loadingEl, badge, noteEl);
        }
        if (story.verification_note && story.abstract_status === "flagged") {
            noteEl.querySelector("small").textContent = `⚠️ ${story.verification_note}`;
            noteEl.classList.remove("hidden");
        }
        o.classList.remove("hidden"); document.body.style.overflow = "hidden";
    },
    async fetchDetail(storyId, textEl, loadingEl, badge, noteEl) {
        try {
            const resp = await fetch(`/api/stories/${storyId}`);
            const d = await resp.json();
            if (d.abstract) {
                textEl.textContent = d.abstract; textEl.classList.remove("hidden");
                loadingEl.classList.add("hidden");
                badge.textContent = d.abstract_status; badge.className = `popup-badge ${d.abstract_status}`;
                if (d.verification_note && d.abstract_status === "flagged") {
                    noteEl.querySelector("small").textContent = `⚠️ ${d.verification_note}`;
                    noteEl.classList.remove("hidden");
                }
            } else { loadingEl.textContent = "Abstract not yet available. Check back soon."; }
        } catch (e) { loadingEl.textContent = "Failed to load abstract."; console.error(e); }
    },
    close() { this.overlay.classList.add("hidden"); document.body.style.overflow = ""; this.currentStory = null; },
};
document.addEventListener("DOMContentLoaded", () => Popup.init());
