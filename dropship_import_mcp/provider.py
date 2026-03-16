from __future__ import annotations

import importlib
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ImportProvider(ABC):
    """Provider contract for scenario-first import workflows."""

    name = "abstract"

    @abstractmethod
    async def get_rule_capabilities(self, target_store: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def prepare_candidate(
        self,
        source_url: str,
        source_hint: str,
        country: str,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def commit_candidate(
        self,
        provider_state: Dict[str, Any],
        draft: Dict[str, Any],
        target_store: Optional[str],
        visibility_mode: str,
        push_options: Dict[str, Any],
    ) -> Dict[str, Any]:
        raise NotImplementedError


def load_provider() -> ImportProvider:
    module_name = os.getenv("IMPORT_PROVIDER_MODULE", "dsers_provider.provider")
    module = importlib.import_module(module_name)
    factory = getattr(module, "build_provider", None)
    if factory is None:
        raise RuntimeError(f"Provider module '{module_name}' does not expose build_provider()")
    provider = factory()
    if not isinstance(provider, ImportProvider):
        raise RuntimeError(f"Provider module '{module_name}' returned an invalid provider instance")
    return provider
