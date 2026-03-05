from __future__ import annotations
from pathlib import Path
from datetime import datetime

LOG_PATH = Path("data/alerts.log")


def _log(msg: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat(timespec="seconds")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def notify(title: str, message: str) -> None:
    """
    Windows-safe notifications:
    1) try winotify (toast)
    2) fallback: print + log
    Never crashes, never uses plyer.
    """
    title = (title or "")[:64]
    message = (message or "")[:256]

    # 1) Windows toast via winotify
    try:
        from winotify import Notification
        toast = Notification(app_id="AI Job Finder", title=title, msg=message)
        toast.show()
        return
    except Exception as e:
        # 2) fallback: console + file
        msg = f"{title} | {message} (toast failed: {e})"
        print(msg)
        _log(msg)