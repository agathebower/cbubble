"""Abstract generation and verification engine."""

import re
import logging
from ..llm.manager import LLMManager
from ..llm.base import LLMResponse

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

    async def _call_abstract(self, system_prompt, user_prompt) -> LLMResponse:
        provider = self.llm.abstract_provider
        if not provider:
            return LLMResponse(text="", provider="none", model="none",
                               success=False, error="No abstract provider configured")
        return await provider.complete(system_prompt, user_prompt)

    async def _call_validate(self, system_prompt, user_prompt) -> LLMResponse:
        provider = self.llm.validate_provider
        if not provider:
            return LLMResponse(text="", provider="none", model="none",
                               success=False, error="No validate provider configured")
        return await provider.complete(system_prompt, user_prompt)

    @staticmethod
    def _sanitize_input(text: str, max_len: int) -> str:
        """Remove control characters and limit length to prevent prompt injection."""
        sanitized = re.sub(r"[\r\n\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
        return sanitized[:max_len]

    async def generate(self, title, content) -> dict:
        safe_title = self._sanitize_input(title, 300)
        safe_content = self._sanitize_input(content, 8000)

        # Step 1: Summarize (using abstract key)
        sum_result = await self._call_abstract(
            system_prompt=SUMMARIZE_SYSTEM.format(max_sentences=self.max_sentences),
            user_prompt=SUMMARIZE_USER.format(title=safe_title, content=safe_content),
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

        # Step 2: Verify (using validate key)
        ver_result = await self._call_validate(
            system_prompt=VERIFY_SYSTEM,
            user_prompt=VERIFY_USER.format(
                title=safe_title, content=safe_content, abstract=abstract_text
            ),
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
