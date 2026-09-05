"""Model adapter contracts; CCM remains independent of any provider."""

from ccm.adapters.llm import LLMAdapter, ModelAdapter

__all__ = ["LLMAdapter", "ModelAdapter"]
