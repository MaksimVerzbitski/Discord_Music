import os
import signal
import subprocess
import sys
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


BOT_MODULE = "app.music_bot"
WATCH_PATH = "app"


class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_bot()

    def start_bot(self):
        self.process = subprocess.Popen(
            [sys.executable, "-m", BOT_MODULE],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            if os.name == "nt"
            else 0,
        )

        print(
            f"[WATCHER] Started PID {self.process.pid}"
        )

    def stop_bot(self):
        if not self.process or self.process.poll() is not None:
            return

        print(
            f"[WATCHER] Stopping PID {self.process.pid}"
        )

        if os.name == "nt":
            self.process.send_signal(
                signal.CTRL_BREAK_EVENT
            )
        else:
            self.process.send_signal(
                signal.SIGINT
            )

        try:
            self.process.wait(timeout=10)

        except subprocess.TimeoutExpired:
            print(
                "[WATCHER] Graceful shutdown timed out. "
                "Killing process."
            )

            self.process.kill()
            self.process.wait()

    def restart_bot(self):
        self.stop_bot()
        self.start_bot()

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".py"):
            print(
                f"[WATCHER] Changed: {event.src_path}"
            )

            self.restart_bot()


if __name__ == "__main__":
    handler = ChangeHandler()

    observer = Observer()
    observer.schedule(
        handler,
        WATCH_PATH,
        recursive=True,
    )
    observer.start()

    print(
        f"[WATCHER] Watching {WATCH_PATH}/"
    )

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print(
            "\n[WATCHER] Shutdown requested."
        )

    finally:
        observer.stop()
        observer.join()

        handler.stop_bot()

        print(
            "[WATCHER] Bot stopped."
        )