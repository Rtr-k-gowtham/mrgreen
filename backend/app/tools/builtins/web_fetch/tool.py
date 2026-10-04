"""
MR.GREEN — Web Fetch Tool

Fetches public web content with strict SSRF protection, size caps, and text extraction.
Blocks localhost, private networks, cloud metadata endpoints, and non-http(s) schemes.
"""

import re
from typing import Any
import httpx

from app.sandbox.security import is_safe_url
from app.tools.base import BaseTool, ToolResult

MAX_RESPONSE_BYTES = 500_000  # 500 KB limit
FETCH_TIMEOUT_SECONDS = 15


def _strip_html(html: str) -> str:
    """Extract clean readable text from HTML markup without heavy third-party parsers."""
    # Remove script and style elements
    clean = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    # Convert paragraph / break tags to newlines
    clean = re.sub(r"<(br|/p|/div|/li|/h[1-6])\s*/?>", "\n", clean, flags=re.IGNORECASE)
    # Remove all remaining HTML tags
    clean = re.sub(r"<[^>]+>", " ", clean)
    # Unescape common entities
    clean = clean.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    # Collapse excess whitespace
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    return "\n".join(lines)


class WebFetchTool(BaseTool):
    """Tool for retrieving public web content safely."""

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "Fetch and extract text content from a public web page with SSRF protection."

    @property
    def category(self) -> str:
        return "network"

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Public HTTP or HTTPS URL to fetch (e.g. 'https://en.wikipedia.org/wiki/PostgreSQL')",
                },
                "max_bytes": {
                    "type": "integer",
                    "description": "Optional maximum content bytes to retrieve (default 200000)",
                },
            },
            "required": ["url"],
        }

    @property
    def permissions(self) -> list[str]:
        return ["network.read"]

    @property
    def risk_level(self) -> str:
        return "medium"

    async def execute(self, **kwargs: Any) -> ToolResult:
        args = kwargs
        if "input" in kwargs and isinstance(kwargs["input"], dict):
            args = kwargs["input"]

        raw_url = args.get("url")
        if not raw_url:
            return ToolResult(success=False, error="Missing required argument 'url'")

        target_url = str(raw_url).strip()
        max_bytes = min(int(args.get("max_bytes", 200_000)), MAX_RESPONSE_BYTES)

        # 1. SSRF Validation
        is_safe, error_reason = is_safe_url(target_url)
        if not is_safe:
            return ToolResult(
                success=False,
                error=f"SSRF Protection blocked request: {error_reason}",
                output={"url": target_url},
            )

        headers = {
            "User-Agent": "MR.GREEN/1.0 (Autonomous Assistant; +https://github.com/Rtr-k-gowtham/mrgreen)",
            "Accept": "text/html,application/xhtml+xml,application/json,text/plain;q=0.9,*/*;q=0.8",
        }

        try:
            async with httpx.AsyncClient(
                timeout=FETCH_TIMEOUT_SECONDS,
                follow_redirects=True,
                max_redirects=3,
            ) as client:
                response = await client.get(target_url, headers=headers)

                # Validate final redirected URL as well to prevent redirect-based SSRF bypass
                final_url = str(response.url)
                if final_url != target_url:
                    safe_redirect, redirect_err = is_safe_url(final_url)
                    if not safe_redirect:
                        return ToolResult(
                            success=False,
                            error=f"Redirect blocked by SSRF Protection: {redirect_err}",
                            output={"url": target_url, "redirected_to": final_url},
                        )

                response.raise_for_status()

                # Read raw bytes with size limit
                content_bytes = response.content[:max_bytes]
                text_content = content_bytes.decode("utf-8", errors="replace")

                content_type = response.headers.get("content-type", "").lower()
                if "html" in content_type:
                    extracted_text = _strip_html(text_content)
                else:
                    extracted_text = text_content

                truncated = len(response.content) > max_bytes

                return ToolResult(
                    success=True,
                    output={
                        "url": target_url,
                        "status_code": response.status_code,
                        "content": extracted_text,
                        "content_length": len(extracted_text),
                        "truncated": truncated,
                    },
                )

        except httpx.HTTPStatusError as e:
            return ToolResult(
                success=False,
                error=f"HTTP Error {e.response.status_code}: {e.response.reason_phrase}",
                output={"url": target_url, "status_code": e.response.status_code},
            )
        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                error=f"Request timed out after {FETCH_TIMEOUT_SECONDS}s",
                output={"url": target_url},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to fetch URL: {str(e)}",
                output={"url": target_url},
            )
