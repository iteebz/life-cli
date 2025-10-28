import itertools
import sys
import threading
import time


class Spinner:
    """Simple CLI spinner for async feedback."""

    def __init__(self, persona: str = "roast"):
        self.stop_event = threading.Event()
        self.spinner_frames = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
        self.persona = persona
        self.thread = None

    def _animate(self):
        """Run spinner animation in background thread."""
        actions = {"roast": "roasting", "pepper": "peppering", "kim": "investigating"}
        action = actions.get(self.persona, "thinking")
        while not self.stop_event.is_set():
            frame = next(self.spinner_frames)
            sys.stderr.write(f"\r{frame} {action}... ")
            sys.stderr.flush()
            time.sleep(0.1)
        sys.stderr.write("\r" + " " * 30 + "\r")
        sys.stderr.flush()

    def start(self):
        """Start the spinner."""
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the spinner."""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=0.5)
