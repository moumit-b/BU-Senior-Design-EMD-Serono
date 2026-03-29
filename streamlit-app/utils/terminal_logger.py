"""
Terminal Logger Callback for LangChain LLMs.

Logs model requests, responses, token usage, and timing to the terminal
so you can monitor activity from the Streamlit console.
"""

import time
import sys
from typing import Any, Dict, List, Optional, Union
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult


class TerminalLoggerCallback(BaseCallbackHandler):
    """Logs LLM calls, token usage, and timing to the terminal (stdout)."""

    def __init__(self):
        self._start_time: Optional[float] = None
        self._prompt_preview: str = ""

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        **kwargs: Any,
    ) -> None:
        self._start_time = time.time()
        model = kwargs.get("invocation_params", {}).get("model", "")
        if not model:
            model = serialized.get("kwargs", {}).get("model", "unknown")

        # Extract the last user message as preview
        preview = ""
        if messages and messages[0]:
            last_msg = messages[0][-1]
            content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
            preview = content[:150].replace("\n", " ")
            if len(content) > 150:
                preview += "..."

        self._prompt_preview = preview
        msg_count = len(messages[0]) if messages else 0

        print(flush=True)
        print("=" * 70, flush=True)
        print(f"[LLM REQUEST]  model={model}  messages={msg_count}", flush=True)
        print(f"[PROMPT]       {preview}", flush=True)
        sys.stdout.flush()

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        elapsed = time.time() - self._start_time if self._start_time else 0

        # Extract token usage from response metadata
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        model_used = ""

        if response.generations and response.generations[0]:
            gen = response.generations[0][0]

            # Get response preview
            content = gen.text if hasattr(gen, "text") and gen.text else ""
            if not content and hasattr(gen, "message"):
                content = gen.message.content or ""
            preview = content[:200].replace("\n", " ")
            if len(content) > 200:
                preview += "..."

            # Extract token usage from generation_info or message metadata
            info = getattr(gen, "generation_info", {}) or {}
            msg = getattr(gen, "message", None)
            usage = {}

            if msg:
                # Anthropic puts usage in response_metadata
                meta = getattr(msg, "response_metadata", {}) or {}
                usage = meta.get("usage", {})
                model_used = meta.get("model", "")

                # Also check usage_metadata (LangChain standard)
                usage_meta = getattr(msg, "usage_metadata", {}) or {}
                if usage_meta:
                    input_tokens = usage_meta.get("input_tokens", 0)
                    output_tokens = usage_meta.get("output_tokens", 0)
                    total_tokens = usage_meta.get("total_tokens", 0)

            if not input_tokens and usage:
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                total_tokens = input_tokens + output_tokens

            print(f"[LLM RESPONSE] {elapsed:.1f}s  model={model_used}", flush=True)
            print(f"[TOKENS]       in={input_tokens}  out={output_tokens}  total={total_tokens}", flush=True)
            print(f"[OUTPUT]       {preview}", flush=True)
        else:
            print(f"[LLM RESPONSE] {elapsed:.1f}s  (no generations)", flush=True)

        print("=" * 70, flush=True)
        print(flush=True)
        sys.stdout.flush()
        self._start_time = None

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        elapsed = time.time() - self._start_time if self._start_time else 0
        print(f"[LLM ERROR]    {elapsed:.1f}s  {type(error).__name__}: {error}", flush=True)
        print("=" * 70, flush=True)
        sys.stdout.flush()
        self._start_time = None
