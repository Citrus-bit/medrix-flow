"""Memory storage providers."""

import abc
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from medrix_flow.config.agents_config import AGENT_NAME_PATTERN
from medrix_flow.config.memory_config import get_memory_config
from medrix_flow.config.paths import get_paths

logger = logging.getLogger(__name__)


def create_empty_memory() -> dict[str, Any]:
    return {
        "version": "1.0",
        "lastUpdated": datetime.utcnow().isoformat() + "Z",
        "user": {
            "workContext": {"summary": "", "updatedAt": ""},
            "personalContext": {"summary": "", "updatedAt": ""},
            "topOfMind": {"summary": "", "updatedAt": ""},
        },
        "history": {
            "recentMonths": {"summary": "", "updatedAt": ""},
            "earlierContext": {"summary": "", "updatedAt": ""},
            "longTermBackground": {"summary": "", "updatedAt": ""},
        },
        "facts": [],
    }


class MemoryStorage(abc.ABC):
    @abc.abstractmethod
    def load(self, agent_name: str | None = None, thread_id: str | None = None) -> dict[str, Any]:
        pass

    @abc.abstractmethod
    def reload(self, agent_name: str | None = None, thread_id: str | None = None) -> dict[str, Any]:
        pass

    @abc.abstractmethod
    def save(self, memory_data: dict[str, Any], agent_name: str | None = None, thread_id: str | None = None) -> bool:
        pass


class FileMemoryStorage(MemoryStorage):
    def __init__(self):
        self._memory_cache: dict[tuple[str, str | None], tuple[dict[str, Any], float | None]] = {}

    def _validate_agent_name(self, agent_name: str) -> None:
        if not agent_name:
            raise ValueError("Agent name must be a non-empty string.")
        if not AGENT_NAME_PATTERN.match(agent_name):
            raise ValueError(f"Invalid agent name {agent_name!r}: names must match {AGENT_NAME_PATTERN.pattern}")

    def _cache_key(self, agent_name: str | None = None, thread_id: str | None = None) -> tuple[str, str | None]:
        if thread_id is not None:
            return ("thread", thread_id)
        if agent_name is not None:
            return ("agent", agent_name)
        return ("global", None)

    def _get_memory_file_path(self, agent_name: str | None = None, thread_id: str | None = None) -> Path:
        if thread_id is not None:
            return get_paths().thread_memory_file(thread_id)

        if agent_name is not None:
            self._validate_agent_name(agent_name)
            return get_paths().agent_memory_file(agent_name)

        config = get_memory_config()
        if config.storage_path:
            p = Path(config.storage_path)
            return p if p.is_absolute() else get_paths().base_dir / p
        return get_paths().memory_file

    def _load_memory_from_file(self, agent_name: str | None = None, thread_id: str | None = None) -> dict[str, Any]:
        file_path = self._get_memory_file_path(agent_name, thread_id)

        if not file_path.exists():
            return create_empty_memory()

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load memory file: %s", e)
            return create_empty_memory()

    def load(self, agent_name: str | None = None, thread_id: str | None = None) -> dict[str, Any]:
        file_path = self._get_memory_file_path(agent_name, thread_id)
        cache_key = self._cache_key(agent_name, thread_id)

        try:
            current_mtime = file_path.stat().st_mtime if file_path.exists() else None
        except OSError:
            current_mtime = None

        cached = self._memory_cache.get(cache_key)

        if cached is None or cached[1] != current_mtime:
            memory_data = self._load_memory_from_file(agent_name, thread_id)
            self._memory_cache[cache_key] = (memory_data, current_mtime)
            return memory_data

        return cached[0]

    def reload(self, agent_name: str | None = None, thread_id: str | None = None) -> dict[str, Any]:
        file_path = self._get_memory_file_path(agent_name, thread_id)
        cache_key = self._cache_key(agent_name, thread_id)
        memory_data = self._load_memory_from_file(agent_name, thread_id)

        try:
            mtime = file_path.stat().st_mtime if file_path.exists() else None
        except OSError:
            mtime = None

        self._memory_cache[cache_key] = (memory_data, mtime)
        return memory_data

    def save(self, memory_data: dict[str, Any], agent_name: str | None = None, thread_id: str | None = None) -> bool:
        file_path = self._get_memory_file_path(agent_name, thread_id)
        cache_key = self._cache_key(agent_name, thread_id)

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            memory_data["lastUpdated"] = datetime.utcnow().isoformat() + "Z"

            temp_path = file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)

            temp_path.replace(file_path)

            try:
                mtime = file_path.stat().st_mtime
            except OSError:
                mtime = None

            self._memory_cache[cache_key] = (memory_data, mtime)
            logger.info("Memory saved to %s", file_path)
            return True
        except OSError as e:
            logger.error("Failed to save memory file: %s", e)
            return False


_storage_instance: MemoryStorage | None = None
_storage_lock = threading.Lock()


def get_memory_storage() -> MemoryStorage:
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    with _storage_lock:
        if _storage_instance is not None:
            return _storage_instance

        config = get_memory_config()
        storage_class_path = config.storage_class

        try:
            module_path, class_name = storage_class_path.rsplit(".", 1)
            import importlib

            module = importlib.import_module(module_path)
            storage_class = getattr(module, class_name)

            if not isinstance(storage_class, type):
                raise TypeError(f"Configured memory storage '{storage_class_path}' is not a class: {storage_class!r}")
            if not issubclass(storage_class, MemoryStorage):
                raise TypeError(f"Configured memory storage '{storage_class_path}' is not a subclass of MemoryStorage")

            _storage_instance = storage_class()
        except Exception as e:
            logger.error(
                "Failed to load memory storage %s, falling back to FileMemoryStorage: %s",
                storage_class_path,
                e,
            )
            _storage_instance = FileMemoryStorage()

    return _storage_instance
