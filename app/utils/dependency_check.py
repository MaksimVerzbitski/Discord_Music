# app/utils/dependency_check.py

import subprocess
import sys
import time
from pathlib import Path

from app.utils.console_style import Colors


REQUIREMENTS_FILE = Path("requirements_for_discordBot.txt")


def draw_progress_bar(
    current: int,
    total: int,
    width: int = 30,
) -> str:
    if total <= 0:
        return Colors.color(
            "[------------------------------]   0%",
            Colors.MAGENTA,
        )

    progress = current / total
    filled = int(width * progress)

    bar = "█" * filled + "-" * (width - filled)
    percent = int(progress * 100)

    return Colors.color(
        f"[{bar}] {percent:3d}%",
        Colors.MAGENTA,
    )


def read_requirements() -> list[str]:
    if not REQUIREMENTS_FILE.exists():
        raise FileNotFoundError(
            f"Requirements file not found: {REQUIREMENTS_FILE}"
        )

    requirements = []

    for line in REQUIREMENTS_FILE.read_text(
        encoding="utf-8"
    ).splitlines():

        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        requirements.append(line)

    return requirements


def check_requirement(requirement: str) -> bool:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "show",
            requirement,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return result.returncode == 0


def install_requirement(requirement: str) -> bool:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            requirement,
        ]
    )

    return result.returncode == 0


def check_dependencies() -> bool:
    requirements = read_requirements()

    total = len(requirements)

    if total == 0:
        print(
            Colors.color(
                "[DEPENDENCIES] No requirements found.",
                Colors.YELLOW,
            )
        )
        return True

    print()
    print("========================================")
    print(" DiscordMusicBot dependency check")
    print("========================================")
    print()

    start_time = time.perf_counter()

    all_ok = True

    for index, requirement in enumerate(
        requirements,
        start=1,
    ):

        print(
            f"\r"
            f"{draw_progress_bar(index - 1, total)} "
            f"Checking {requirement:<25}",
            end="",
            flush=True,
        )

        installed = check_requirement(
            requirement
        )

        if not installed:
            print()

            print(
                Colors.color(
                    f"[DEPENDENCIES] Missing: {requirement}",
                    Colors.YELLOW,
                )
            )

            print(
                Colors.color(
                    f"[DEPENDENCIES] Installing {requirement}...",
                    Colors.YELLOW,
                )
            )

            installed = install_requirement(
                requirement
            )

        if not installed:
            all_ok = False

            print(
                Colors.color(
                    f"[ERROR] Failed to install {requirement}",
                    Colors.RED,
                )
            )

        print(
            f"\r"
            f"{draw_progress_bar(index, total)} "
            f"{requirement:<25}",
            end="",
            flush=True,
        )

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print()
    print()

    if all_ok:
        print(
            Colors.color(
                f"[SUCCESS] Dependencies ready "
                f"in {elapsed:.2f} seconds.",
                Colors.GREEN,
            )
        )

    else:
        print(
            Colors.color(
                f"[ERROR] Dependency check "
                f"finished with errors after "
                f"{elapsed:.2f} seconds.",
                Colors.RED,
            )
        )

    print()

    return all_ok


if __name__ == "__main__":
    success = check_dependencies()

    if not success:
        sys.exit(1)