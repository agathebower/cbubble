"""Abstract generation and verification engine."""

import logging
from ..llm.manager import LLMManager

log = logging.getLogger("cbubble.abstracts")

SUMMARIZE_SYSTEM = """You are a precise news summarizer. Given an article's content, produce a concise factual abstract.
Rules:
- Maximum {max_sentences} sentences
- Focus only on verifiable facts, not opinions
- Include: who, what, when, where if available
- No editorializing or speculation
- If the content is too short or unclear, say "INSUFFICIENT_CONTENT"
"""

SUMMARIZE_USER = """Summarize this article into a brief factual abstract:

Title: {title}

Content:
{content}
"""

VERIFY_SYSTEM = """You are a fact-checking assistant. You will receive an original article and a generated abstract.
Your job is to verify the abstract against the original content.

Respond in this exact format:
VERDICT: VERIFIED or FLAGGED
ISSUES: None, or a brief description of any inaccuracies, omissions, or hallucinations found
CORRECTED: Only if FLAGGED, provide a corrected version of the abstract
"""

VERIFY_USER = """Original article title: {title}

Original content:
{content}

---

Generated abstract:
{abstract}

Verify this abstract against the original content.
"""


class AbstractEngine:
    def __init__(self, llm: LLMManager, max_sentences=5):
        self.llm = llm
        self.max_sentences = max_sentences

    async def generate(self, title, content) -> dict:
        # Step 1: Summarize
        sum_result = await self.llm.complete(
            system_prompt=SUMMARIZE_SYSTEM.format(max_sentences=self.max_sentences),
            user_prompt=SUMMARIZE_USER.format(title=title, content=content),
        )
        if not sum_result.success:
            return {"abstract": None, "status": "error",
                    "note": f"Summarization failed: {sum_result.error}",
                    "provider": sum_result.provider}

        abstract_text = sum_result.text.strip()
        if "INSUFFICIENT_CONTENT" in abstract_text:
            return {"abstract": None, "status": "skipped",
                    "note": "Content too short or unclear",
                    "provider": sum_result.provider}

        # Step 2: Verify
        ver_result = await self.llm.complete(
            system_prompt=VERIFY_SYSTEM,
            user_prompt=VERIFY_USER.format(title=title, content=content, abstract=abstract_text),
        )
        if not ver_result.success:
            return {"abstract": abstract_text, "status": "unverified",
                    "note": f"Verification failed: {ver_result.error}",
                    "provider": sum_result.provider}

        ver_text = ver_result.text.strip()
        if "VERDICT: VERIFIED" in ver_text:
            return {"abstract": abstract_text, "status": "verified",
                    "note": None, "provider": sum_result.provider}
        elif "VERDICT: FLAGGED" in ver_text:
            corrected = abstract_text
            if "CORRECTED:" in ver_text:
                corrected_part = ver_text.split("CORRECTED:", 1)[1].strip()
                if corrected_part and len(corrected_part) > 20:
                    corrected = corrected_part
            issues = ""
            if "ISSUES:" in ver_text:
                issues = ver_text.split("ISSUES:", 1)[1].split("CORRECTED:")[0].strip()
            return {"abstract": corrected, "status": "flagged",
                    "note": issues or "Verification flagged issues",
                    "provider": sum_result.provider}
        else:
            return {"abstract": abstract_text, "status": "unverified",
                    "note": "Could not parse verification response",
                    "provider": sum_result.provider}
