from __future__ import annotations

import threading
from collections.abc import Callable

import keyboard


class HotkeyManager:
    def __init__(self) -> None:
        self._registered: list[str] = []
        self._lock = threading.Lock()

    def register(self, hotkey: str, callback: Callable[[], None]) -> None:
        with self._lock:
            keyboard.add_hotkey(hotkey, callback)
            self._registered.append(hotkey)

    def unregister_all(self) -> None:
        with self._lock:
            for hotkey in self._registered:
                keyboard.remove_hotkey(hotkey)
            self._registered.clear()

