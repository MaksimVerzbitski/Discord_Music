import subprocess
import sys
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.utils.dependency_check import check_dependencies


BOT_FILE = "app/music_bot.py"


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, script_name: str):
        self.script_name = script_name
        self.process = None

        self.start_bot()

    def start_bot(self):
        self.process = subprocess.Popen(
            [
                sys.executable,
                self.script_name,
            ]
        )

        print(
            f"[WATCHER] Started {self.script_name} "
            f"with PID {self.process.pid}"
        )

    def restart_bot(self):
        if self.process:
            print("[WATCHER] Restarting bot...")

            self.process.terminate()
            self.process.wait()

        self.start_bot()

    def on_modified(self, event):
        if event.is_directory:
            return

        normalized_path = event.src_path.replace("\\", "/")

        if normalized_path.endswith(self.script_name):
            self.restart_bot()


def main():
    print()
    print("========================================")
    print(" DiscordMusicBot development launcher")
    print("========================================")
    print()

    if not check_dependencies():
        print("[WATCHER] Cannot start bot.")
        sys.exit(1)

    event_handler = ChangeHandler(BOT_FILE)

    observer = Observer()

    observer.schedule(
        event_handler,
        path="app",
        recursive=True,
    )

    observer.start()

    print("[WATCHER] Watching app/ for changes...")
    print()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print()
        print("[WATCHER] Stopping...")

        observer.stop()

        if event_handler.process:
            event_handler.process.terminate()
            event_handler.process.wait()

    observer.join()


if __name__ == "__main__":
    main()