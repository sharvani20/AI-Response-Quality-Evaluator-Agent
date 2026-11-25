import asyncio
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Universal LLM client supporting Groq and OpenAI providers."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.provider = settings.LLM_PROVIDER.lower()
        self.model = settings.MODEL_NAME
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY_SECONDS
        self._client = None
        self._initialized = True

    def _get_client(self):
        """Lazily initialize the appropriate client."""
        if self._client is not None:
            return self._client

        if self.provider == "openai":
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info(f"OpenAI client initialized with model: {self.model}")
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        else:
            # Default: Groq
            from groq import Groq
            api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
            self._client = Groq(api_key=api_key)
            logger.info(f"Groq client initialized with model: {self.model}")

        return self._client

    def _sync_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Synchronous completion call (works for both providers — same API shape)."""
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    async def chat_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat completion request with retry/backoff logic.

        Returns:
            The assistant's response content as a string.
        """
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._sync_completion,
                    system_prompt,
                    user_prompt,
                )
                return response
            except Exception as e:
                error_str = str(e)
                is_rate_limit = "429" in error_str or "rate_limit" in error_str.lower()
                is_last = attempt == self.max_retries - 1

                if is_last:
                    logger.error(f"LLM call failed after {self.max_retries} attempts: {e}")
                    raise
                else:
                    wait = self.retry_delay * (2 ** attempt) if is_rate_limit else self.retry_delay
                    logger.warning(f"LLM call failed (attempt {attempt + 1}), retrying in {wait}s: {e}")
                    await asyncio.sleep(wait)

    async def parse_json_response(self, system_prompt: str, user_prompt: str) -> dict:
        """Send a request and parse the JSON response.

        Returns:
            Parsed JSON dictionary.
        """
        raw = await self.chat_completion(system_prompt, user_prompt)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON block from response
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(raw[start:end])
                except json.JSONDecodeError:
                    pass
            logger.error(f"Failed to parse JSON: {raw[:300]}")
            raise ValueError("Could not parse LLM response as JSON")


# Singleton instance
groq_client = LLMClient()
