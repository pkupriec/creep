"""External inference only; the shared adapter owns no tool executor."""

from .ollama import HttpOllamaAdapter

__all__ = ["HttpOllamaAdapter"]
