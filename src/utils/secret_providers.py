"""
Secret provider abstraction for Grekko.

- SecretProvider ABC: CRUD + health_check
- DotEnvProvider: get() via python-dotenv
- VaultProvider, AWSParameterStoreProvider: stubs
- get_secret() helper
- Hot-reload via watchdog
"""

import os
from abc import ABC, abstractmethod
from typing import Optional
from threading import Thread, Lock

from dotenv import dotenv_values, load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Abstract Base ---

class SecretProvider(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass

# --- DotEnvProvider ---

class DotEnvProvider(SecretProvider):
    """
    Loads secrets from .env file(s) and environment variables.
    Supports hot-reload via Watchdog.
    """
    def __init__(self, dotenv_path: Optional[str] = None):
        self.dotenv_path = dotenv_path or self._find_dotenv()
        self._lock = Lock()
        self._secrets = self._load()
        self._start_watcher()

    def _find_dotenv(self) -> str:
        # Search for .env in project root
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        dotenv_file = os.path.join(root, ".env")
        return dotenv_file if os.path.isfile(dotenv_file) else ""

    def _load(self):
        if self.dotenv_path and os.path.isfile(self.dotenv_path):
            load_dotenv(self.dotenv_path, override=True)
            return dotenv_values(self.dotenv_path)
        return {}

    def get(self, key: str) -> Optional[str]:
        # Prefer env var, fallback to loaded .env
        with self._lock:
            return os.environ.get(key) or self._secrets.get(key)

    def set(self, key: str, value: str) -> None:
        raise NotImplementedError("DotEnvProvider does not support setting secrets at runtime.")

    def delete(self, key: str) -> None:
        raise NotImplementedError("DotEnvProvider does not support deleting secrets at runtime.")

    def health_check(self) -> bool:
        return bool(self._secrets)

    def _start_watcher(self):
        if not self.dotenv_path or not os.path.isfile(self.dotenv_path):
            return
        event_handler = _DotEnvReloadHandler(self)
        observer = Observer()
        observer.schedule(event_handler, os.path.dirname(self.dotenv_path), recursive=False)
        t = Thread(target=observer.start, daemon=True)
        t.start()

    def _reload(self):
        with self._lock:
            self._secrets = self._load()

class _DotEnvReloadHandler(FileSystemEventHandler):
    def __init__(self, provider: DotEnvProvider):
        self.provider = provider

    def on_modified(self, event):
        if event.src_path == self.provider.dotenv_path:
            self.provider._reload()

# --- VaultProvider Stub ---

class VaultProvider(SecretProvider):
    def get(self, key: str) -> Optional[str]:
        raise NotImplementedError("VaultProvider is not implemented yet.")

    def set(self, key: str, value: str) -> None:
        raise NotImplementedError("VaultProvider is not implemented yet.")

    def delete(self, key: str) -> None:
        raise NotImplementedError("VaultProvider is not implemented yet.")

    def health_check(self) -> bool:
        raise NotImplementedError("VaultProvider is not implemented yet.")

# --- AWSParameterStoreProvider Stub ---

class AWSParameterStoreProvider(SecretProvider):
    def get(self, key: str) -> Optional[str]:
        raise NotImplementedError("AWSParameterStoreProvider is not implemented yet.")

    def set(self, key: str, value: str) -> None:
        raise NotImplementedError("AWSParameterStoreProvider is not implemented yet.")

    def delete(self, key: str) -> None:
        raise NotImplementedError("AWSParameterStoreProvider is not implemented yet.")

    def health_check(self) -> bool:
        raise NotImplementedError("AWSParameterStoreProvider is not implemented yet.")

# --- Helper: get_secret ---

_active_provider: SecretProvider = DotEnvProvider()

def get_secret(key: str) -> Optional[str]:
    return _active_provider.get(key)