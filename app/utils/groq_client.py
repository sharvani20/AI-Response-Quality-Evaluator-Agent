import asyncio
import json
import logging
from groq import Groq, AsyncGroq
from app.config import settings

logger = logging.getLogger(__name__)


class GroqClient:
    """Wrapper around Groq API client with retry logic and JSON parsing."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.MODEL_NAME
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY_SECONDS
        self._initialized = True

    async def chat_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat completion request with retry logic.

        Args:
            system_prompt: The system message setting the agent's role.
            user_prompt: The user message with the evaluation task.

        Returns:
            The assistant's response content as a string.
        """
        for attempt in range(self.max_retries):
            try:
                # Run synchronous Groq client in thread pool
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._sync_completion,
                    system_prompt,
                    user_prompt
                )
                return response
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate_limit" in error_str.lower():
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited (attempt {attempt + 1}/{self.max_retries}). "
                                   f"Waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                elif attempt < self.max_retries - 1:
                    logger.warning(f"API error (attempt {attempt + 1}/{self.max_retries}): {e}")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"API call failed after {self.max_retries} attempts: {e}")
                    raise

    def _sync_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Synchronous completion call."""
        response = self.client.chat.completions.create(
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

    async def parse_json_response(self, system_prompt: str, user_prompt: str) -> dict:
        """Send a request and parse the JSON response.

        Returns:
            Parsed JSON dictionary from the response.
        """
        raw_response = await self.chat_completion(system_prompt, user_prompt)

        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            start = raw_response.find("{")
            end = raw_response.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(raw_response[start:end])
                except json.JSONDecodeError:
                    pass
            logger.error(f"Failed to parse JSON response: {raw_response[:200]}")
            raise ValueError(f"Could not parse LLM response as JSON")


# Singleton instance
groq_client = GroqClient()
