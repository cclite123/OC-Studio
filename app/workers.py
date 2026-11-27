"""Qt worker threads and thread-safe prompt bridge for OC-Studio."""

from __future__ import annotations

import threading
import traceback
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, QThread, Signal

from app.core_adapter import CoreAbortError, PromptRequest


class UiEventRelay(QObject):
    """Receives callbacks from background threads and emits Qt signals on the UI thread."""

    log_received = Signal(str)
    build_progress = Signal(str, list, int, bool)
    download_progress = Signal(int, str, float, float)
    prompt_requested = Signal(object)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._prompt_event = threading.Event()
        self._prompt_answer: str = ""

    def ask_user_blocking(self, req: PromptRequest) -> str:
        """Called on worker thread; blocks until UI thread replies."""
        self._prompt_event.clear()
        self._prompt_answer = req.default_value
        self.prompt_requested.emit(req)
        self._prompt_event.wait()
        return self._prompt_answer

    def submit_prompt_answer(self, answer: str) -> None:
        self._prompt_answer = answer
        self._prompt_event.set()


class TaskWorker(QThread):
    """Generic background thread executing any callable and returning result or error."""

    finished_ok = Signal(object)
    failed = Signal(str, str)  # (title, detail)

    def __init__(
        self,
        fn: Callable[..., Any],
        *args: Any,
        parent: Optional[QObject] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent)
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.finished_ok.emit(result)
        except CoreAbortError as exc:
            self.failed.emit("硬件不兼容或流程中止", str(exc))
        except Exception as exc:
            detail = f"{exc}\n\n{traceback.format_exc()}"
            self.failed.emit("操作执行失败", detail)
