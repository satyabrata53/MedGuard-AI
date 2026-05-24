import os
import warnings

import httpx

from app.config import load_environment
from app.utils.logger import get_logger

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        import google.generativeai as genai
except Exception:  # pragma: no cover - deterministic local fallback
    genai = None

from app.llm.prompts import GENERIC_SYSTEM_PROMPT, SAFE_SYSTEM_PROMPT, patient_context


logger = get_logger(__name__)


class GeminiClient:
    def __init__(self) -> None:
        load_environment()
        self.provider = os.getenv("LLM_PROVIDER", "groq").lower()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        if self.provider == "groq" and self.groq_api_key:
            self.model_name = self.groq_model
            self.enabled = True
        elif self.gemini_api_key and genai:
            self.provider = "gemini"
            self.model_name = self.gemini_model
            self.enabled = True
            genai.configure(api_key=self.gemini_api_key)
        else:
            self.model_name = self.groq_model if self.provider == "groq" else self.gemini_model
            self.enabled = False

    def generate_generic(self, patient: dict, query: str) -> str:
        fallback = (
            "Generic AI draft: consider the requested medication in the clinical context, "
            "but this response has not received deterministic MedGuard safety constraints."
        )
        return self._generate(GENERIC_SYSTEM_PROMPT, f"{patient_context(patient)}\n\nDoctor query: {query}", fallback)

    def generate_safe(self, patient: dict, query: str, constraints: str) -> str:
        fallback = (
            "MedGuard constrained response: follow the deterministic safety constraints. "
            f"{constraints}"
        )
        prompt = f"{patient_context(patient)}\n\nDoctor query: {query}\n\nDeterministic safety constraints:\n{constraints}"
        return self._generate(f"{SAFE_SYSTEM_PROMPT}\n\n{constraints}", prompt, fallback)

    def clarify_drug_name(self, raw_input: str, candidates: list[str]) -> str:
        if not self.enabled:
            return f"Did you mean {candidates[0]}?" if candidates else "Please clarify the medication name."
        system = "You only ask medication-name clarification questions. Do not make safety decisions. You must include every candidate name exactly as provided."
        fallback = "Did you mean one of these validated medications?\n" + "\n".join(f"- {candidate}" for candidate in candidates)
        return self._generate(system, f"Input: {raw_input}\nCandidates: {candidates}\nAsk one short clarification question listing every candidate exactly.", fallback)

    def _generate(self, system_prompt: str, user_prompt: str, fallback: str) -> str:
        if not self.enabled:
            return fallback
        if self.provider == "groq":
            return self._generate_groq(system_prompt, user_prompt, fallback)
        return self._generate_gemini(system_prompt, user_prompt, fallback)

    def _generate_groq(self, system_prompt: str, user_prompt: str, fallback: str) -> str:
        try:
            response = httpx.post(
                f"{self.groq_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.groq_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 700,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return (data["choices"][0]["message"]["content"] or fallback).strip()
        except Exception as exc:
            logger.warning("Groq generation failed; using deterministic fallback. Error: %s", exc)
            return fallback

    def _generate_gemini(self, system_prompt: str, user_prompt: str, fallback: str) -> str:
        try:
            model = genai.GenerativeModel(self.gemini_model, system_instruction=system_prompt)
            response = model.generate_content(user_prompt)
            return (response.text or fallback).strip()
        except Exception as exc:
            logger.warning("Gemini generation failed; using deterministic fallback. Error: %s", exc)
            return fallback
