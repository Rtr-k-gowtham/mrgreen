"""
MR.GREEN — Sentence & Chunk Streaming Buffer

Buffers LLM delta tokens and yields complete sentences as soon as punctuation
boundaries are encountered, minimizing first-audio latency for TTS.
"""

import re
from typing import Generator

# Sentence terminating punctuation for English and Indic/Tamil texts
SENTENCE_END_REGEX = re.compile(r"([.!?;\n।]+(?:\s+|$))")


class SentenceBuffer:
    """
    Accumulates streaming LLM text deltas and yields complete sentences
    for low-latency pipelined Text-to-Speech synthesis.
    """

    def __init__(self, min_chunk_chars: int = 15, max_chunk_chars: int = 180) -> None:
        self.min_chunk_chars = min_chunk_chars
        self.max_chunk_chars = max_chunk_chars
        self._buffer: str = ""

    def add_delta(self, delta: str) -> list[str]:
        """
        Add a text delta from the LLM stream.
        Returns a list of complete sentences ready for TTS synthesis.
        """
        self._buffer += delta
        ready_sentences: list[str] = []

        # Check if punctuation boundary is reached
        parts = SENTENCE_END_REGEX.split(self._buffer)
        if len(parts) > 1:
            # We have at least one delimiter
            # parts will alternate: [text1, delim1, text2, delim2, ... trailing]
            combined = ""
            for i in range(0, len(parts) - 1, 2):
                sentence = (parts[i] + parts[i + 1]).strip()
                if sentence:
                    if len(combined) + len(sentence) < self.min_chunk_chars and i + 2 < len(parts) - 1:
                        combined += " " + sentence
                    else:
                        ready_sentences.append((combined + " " + sentence).strip())
                        combined = ""

            # The remainder becomes the new buffer
            self._buffer = (combined + " " + parts[-1]).strip()
        elif len(self._buffer) >= self.max_chunk_chars:
            # Prevent buffer from growing too long without punctuation (e.g. lists or commas)
            # Find last space or comma
            split_idx = max(self._buffer.rfind(" "), self._buffer.rfind(","))
            if split_idx > self.min_chunk_chars:
                ready_sentences.append(self._buffer[:split_idx].strip())
                self._buffer = self._buffer[split_idx + 1:].strip()

        return ready_sentences

    def flush(self) -> list[str]:
        """Flush any remaining text in the buffer when LLM stream finishes."""
        remaining = self._buffer.strip()
        self._buffer = ""
        if remaining:
            return [remaining]
        return []
