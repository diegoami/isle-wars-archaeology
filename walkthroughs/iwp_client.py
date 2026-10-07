"""iwp_client.py — file-based client for the iwp-poller PowerShell script on Windows.

WSL writes cmd-<uuid>.json to /mnt/c/Temp/iwp-cmd/; the PowerShell poller reads,
executes, writes result-<uuid>.json, and deletes the command. This client
sends one command at a time and waits for its result.
"""
import json
import os
import time
import uuid
from pathlib import Path


CMD_DIR = Path("/mnt/c/Temp/iwp-cmd")
POLL_INTERVAL = 0.1   # seconds
RESULT_TIMEOUT = 30.0 # seconds


class IWPClient:
    def __init__(self, cmd_dir=CMD_DIR, poll=POLL_INTERVAL, timeout=RESULT_TIMEOUT):
        self.cmd_dir = Path(cmd_dir)
        self.poll = poll
        self.timeout = timeout

    def connect(self):
        self.cmd_dir.mkdir(parents=True, exist_ok=True)
        return self

    def close(self):
        pass

    def _send(self, obj):
        cid = uuid.uuid4().hex[:12]
        cmd_path = self.cmd_dir / f"cmd-{cid}.json"
        result_path = self.cmd_dir / f"result-{cid}.json"
        cmd_path.write_text(json.dumps(obj, separators=(",", ":")), encoding="utf-8")
        deadline = time.monotonic() + self.timeout
        while True:
            if result_path.exists():
                text = result_path.read_text(encoding="utf-8-sig")
                try:
                    result_path.unlink()
                except OSError:
                    pass
                resp = json.loads(text)
                if not resp.get("ok"):
                    raise RuntimeError(f"command {obj.get('cmd')!r} failed: {resp.get('error')}")
                return resp
            if time.monotonic() > deadline:
                raise TimeoutError(f"timeout waiting for result of {obj.get('cmd')!r}")
            time.sleep(self.poll)

    def screenshot(self, path):
        path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        return self._send({"cmd": "screenshot", "path": path})

    def click(self, x, y, button="left"):
        return self._send({"cmd": "click", "x": int(x), "y": int(y), "button": button})

    def move(self, x, y):
        return self._send({"cmd": "move", "x": int(x), "y": int(y)})

    def key(self, key):
        return self._send({"cmd": "key", "key": key})

    def wait(self, ms):
        return self._send({"cmd": "wait", "ms": int(ms)})

    def find_window(self, title):
        return self._send({"cmd": "find_window", "title": title})

    def is_window(self, title):
        return self._send({"cmd": "is_window", "title": title})

    def set_focus(self, hwnd):
        return self._send({"cmd": "set_focus", "hwnd": int(hwnd)})

    def set_window_pos(self, hwnd, x, y, w=None, h=None):
        req = {"cmd": "set_window_pos", "hwnd": int(hwnd), "x": int(x), "y": int(y)}
        if w is not None: req["w"] = int(w)
        if h is not None: req["h"] = int(h)
        return self._send(req)

    def list_windows(self):
        return self._send({"cmd": "list_windows"})

    def launch_game(self, path, x=None, y=None, w=None, h=None, args=None):
        req = {"cmd": "launch_game", "path": path}
        if x is not None: req["x"] = int(x)
        if y is not None: req["y"] = int(y)
        if w is not None: req["w"] = int(w)
        if h is not None: req["h"] = int(h)
        if args is not None: req["args"] = args
        return self._send(req)

    def shutdown(self):
        return self._send({"cmd": "shutdown"})

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False
