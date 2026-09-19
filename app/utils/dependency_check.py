"""Resolve declared dependencies, including versions and optional voice extras."""
import shutil
import logging
import os
import time
import subprocess
import sys
from pathlib import Path

from app.utils.console_style import Colors, draw_progress_bar, get_console_panel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements_for_discordBot.txt"
logger = logging.getLogger(__name__)


def show_progress(current, message, *, failed=False, previous=None):
    panel = get_console_panel()
    interactive = panel.interactive
    target = int(current / 3 * 100)
    start = int(previous / 3 * 100) if previous is not None else target
    # Animate completed work only; redirected logs stay immediate and concise.
    steps = range(start + 1, target + 1) if interactive and start < target else [target]
    for percent in steps:
        bar_width = max(1, panel.width - 6 - 5 - 32)
        bar = draw_progress_bar(percent, 100, width=bar_width, use_color=False)
        panel.write(['', f'{bar}  ·  {message}', ''],
                    [None, Colors.RED if failed else Colors.MAGENTA, None], progress=True)
        if interactive and start < target:
            time.sleep(0.01)
    if failed or current == 3:
        panel.progress = False


def check_dependencies() -> bool:
    if not REQUIREMENTS_FILE.is_file():
        logger.error("Missing requirements: %s", REQUIREMENTS_FILE)
        return False
    # pip show cannot validate version constraints or dependencies of extras.
    logger.info("Checking Python dependencies with %s", sys.executable)
    show_progress(0, "Resolving Python packages...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install",
            "--disable-pip-version-check", "-r", str(REQUIREMENTS_FILE),
        ], cwd=PROJECT_ROOT, capture_output=True, text=True, errors="replace")
    except OSError as exc:
        show_progress(0, "Package installation failed", failed=True)
        logger.error("Could not start dependency installation: %s", exc)
        return False
    if result.returncode:
        show_progress(0, "Package installation failed", failed=True)
        logger.error("Dependency installation failed (exit code %s).", result.returncode)
        logger.error("%s", result.stderr or result.stdout)
        return False
    show_progress(1, "Checking FFmpeg...", previous=0)
    if shutil.which("ffmpeg") is None:
        show_progress(1, "FFmpeg missing", failed=True)
        logger.error("Install FFmpeg and add its bin directory to PATH.")
        return False
    sound = PROJECT_ROOT / "sounds" / "nokia-tune-1600-36527.mp3"
    show_progress(2, "Checking entrance sound...", previous=1)
    if not sound.is_file():
        show_progress(2, "Entrance sound missing", failed=True)
        logger.error("Missing entrance sound: %s", sound)
        return False
    show_progress(3, "All dependencies ready", previous=2)
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    sys.exit(0 if check_dependencies() else 1)
