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
            [
                sys.executable,
                "-m",
                BOT_MODULE,
            ]
        )

        print(
            f"[WATCHER] Started {BOT_MODULE} "
            f"with PID {self.process.pid}"
        )

    def stop_bot(self):
        if (
            self.process
            and self.process.poll() is None
        ):
            print(
                f"[WATCHER] Stopping PID "
                f"{self.process.pid}"
            )

            self.process.terminate()

            try:
                self.process.wait(
                    timeout=10
                )

            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

    def restart_bot(self):
        self.stop_bot()
        self.start_bot()

    def on_modified(self, event):
        if event.is_directory:
            return

        if event.src_path.endswith(".py"):
            print(
                "[WATCHER] Python change detected: "
                f"{event.src_path}"
            )

            self.restart_bot()


if __name__ == "__main__":
    event_handler = ChangeHandler()

    observer = Observer()

    observer.schedule(
        event_handler,
        WATCH_PATH,
        recursive=True,
    )

    observer.start()

    print(
        f"[WATCHER] Watching {WATCH_PATH}/ "
        "for Python changes..."
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

        event_handler.stop_bot()

        print(
            "[WATCHER] Bot process stopped."
        )