"""Shared console logging, with colors only for interactive terminals."""
import logging
import os
import sys
import shutil
import threading
import atexit


MAX_CONTENT_WIDTH = len(
    '2026-09-19 08:00:21 | INFO     | discord.gateway | Shard ID None has connected to Gateway '
    '(Session ID: c7b07bc5c5db4371a5f156c73200b03e).'
)


def console_width():
    """Fit frames to the terminal, leaving a column to prevent wrapping."""
    columns = shutil.get_terminal_size(fallback=(MAX_CONTENT_WIDTH + 5, 24)).columns
    return max(10, min(MAX_CONTENT_WIDTH, columns - 5))


def fit_text(text, width):
    text = text.expandtabs(4)
    return (text[:width - 3] + '...' if len(text) > width else text).ljust(width)


def framed_lines(lines, *, width=None, styles=None, use_color=False):
    width = console_width() if width is None else width

    def border(text):
        return Colors.color(text, Colors.DIM) if use_color else text

    result = [border('┌' + '─' * (width + 2) + '┐')]
    for index, text in enumerate(lines):
        content = fit_text(text, width)
        style = styles[index] if styles else None
        if use_color and style:
            content = Colors.color(content, style)
        result.append(border('│ ') + content + border(' │'))
    result.append(border('└' + '─' * (width + 2) + '┘'))
    return '\n'.join(result)


class Colors:
    RESET = '\033[0m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    @classmethod
    def color(cls, text: str, style: str) -> str:
        return f'{style}{text}{cls.RESET}'


def draw_progress_bar(current, total, width=30, use_color=True):
    progress = max(0, min(current / total, 1)) if total > 0 else 0
    filled = int(width * progress)
    bar = f"{'█' * filled}{'░' * (width - filled)}  {int(progress * 100):3d}%"
    return Colors.color(bar, Colors.MAGENTA) if use_color else bar


class ConsoleFormatter(logging.Formatter):
    STYLES = {logging.DEBUG: Colors.DIM, logging.INFO: Colors.GREEN,
              logging.WARNING: Colors.YELLOW, logging.ERROR: Colors.RED,
              logging.CRITICAL: Colors.BOLD + Colors.RED}

    def __init__(self, use_color=False):
        super().__init__('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                         datefmt='%Y-%m-%d %H:%M:%S')
        self.use_color = use_color

    def format(self, record):
        message = super().format(record)
        style = self.STYLES.get(record.levelno)
        lines = message.splitlines()
        return framed_lines(lines, styles=[style] * len(lines), use_color=self.use_color)


class ConsolePanel:
    """A growing rectangle shared by log records and the live progress row."""
    def __init__(self, stream):
        self.stream = stream
        self.width = console_width()
        self.interactive = bool(getattr(stream, 'isatty', lambda: False)())
        self.color = self.interactive and 'NO_COLOR' not in os.environ
        self.started = False
        self.progress = False
        self.lock = threading.RLock()

    def write(self, lines, styles=None, *, progress=False):
        with self.lock:
            frame = framed_lines(lines, width=self.width, styles=styles,
                                 use_color=self.color).splitlines()
            if not self.started:
                self.stream.write(frame[0] + '\n')
                self.started = True
            elif self.interactive:
                # Replace the three-row progress block and its bottom border.
                self.stream.write('\033[4A\r' if progress and self.progress else '\033[1A\r')
            self.stream.write('\n'.join(frame[1:-1]) + '\n')
            if self.interactive:
                self.stream.write(frame[-1] + '\n')
            self.stream.flush()
            self.progress = progress

    def close(self):
        if self.started and not self.interactive and not self.stream.closed:
            self.stream.write('└' + '─' * (self.width + 2) + '┘\n')
            self.stream.flush()
        self.started = False


_panel = None


def get_console_panel(stream=None):
    global _panel
    stream = sys.stdout if stream is None else stream
    if _panel is None or _panel.stream is not stream:
        if _panel is not None:
            _panel.close()
        _panel = ConsolePanel(stream)
    return _panel


@atexit.register
def close_console_panel():
    if _panel is not None:
        _panel.close()


class PanelHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            lines = self.format(record).splitlines()
            style = ConsoleFormatter.STYLES.get(record.levelno)
            get_console_panel(self.stream).write(lines, [style] * len(lines))
        except Exception:
            self.handleError(record)


def setup_logging(level=logging.INFO, stream=None):
    stream = sys.stdout if stream is None else stream
    use_color = bool(getattr(stream, 'isatty', lambda: False)()) and 'NO_COLOR' not in os.environ
    handler = PanelHandler(stream)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'))
    handler._music_bot_console = True
    root = logging.getLogger()
    for previous in root.handlers[:]:
        if getattr(previous, '_music_bot_console', False):
            root.removeHandler(previous)
            previous.close()
    root.addHandler(handler)
    root.setLevel(level)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
