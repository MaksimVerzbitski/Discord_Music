import asyncio
import logging
import shutil
from pathlib import Path

import discord

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENTRANCE_SOUND = PROJECT_ROOT / "sounds" / "nokia-tune-1600-36527.mp3"


class MeasuredAudio(discord.AudioSource):
    """Detect empty decoder output and report the amount of audio processed."""

    def __init__(self, source):
        self.source = source
        self.frames = 0

    def read(self):
        data = self.source.read()
        if data:
            self.frames += 1
        return data

    def is_opus(self):
        return self.source.is_opus()

    def cleanup(self):
        self.source.cleanup()

    @property
    def _current_error(self):
        # Preserve FFmpeg's error reporting through this counting wrapper.
        return getattr(self.source, "_current_error", None)


async def wait_for_voice_encryption(voice_client, timeout=10):
    # discord.py 2.7 exposes connection completion before MLS readiness.
    # These internal fields are read only; never log keys or session contents.
    connection = getattr(voice_client, "_connection", None)
    version = getattr(connection, "dave_protocol_version", 0)
    if not isinstance(version, int):
        return
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while version > 0 and not connection.can_encrypt:
        if not voice_client.is_connected():
            raise RuntimeError("Voice disconnected while waiting for encryption.")
        if loop.time() >= deadline:
            raise RuntimeError("Discord voice encryption did not become ready. Use /leave then /join.")
        await asyncio.sleep(0.05)
        version = connection.dave_protocol_version
    logger.info(
        "[VOICE TRANSPORT] DAVE version=%s ready=%s mode=%s",
        version, bool(getattr(connection, "can_encrypt", False)),
        getattr(voice_client, "mode", "unknown"),
    )


async def play_entrance_sound(voice_client: discord.VoiceClient) -> None:
    if not ENTRANCE_SOUND.is_file():
        raise RuntimeError("Missing entrance sound: sounds/nokia-tune-1600-36527.mp3.")
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is missing from the bot's PATH.")
    if not voice_client.is_connected():
        raise RuntimeError("The voice connection was lost.")
    if voice_client.is_playing() or voice_client.is_paused():
        raise RuntimeError("Audio is already playing. Wait for it to finish before using /join again.")

    await wait_for_voice_encryption(voice_client)

    loop = asyncio.get_running_loop()
    finished = loop.create_future()

    def complete(error):
        if not finished.done():
            if error is None:
                finished.set_result(None)
            else:
                finished.set_exception(error)

    def after(error):
        loop.call_soon_threadsafe(complete, error)

    source = MeasuredAudio(discord.FFmpegPCMAudio(
        source=str(ENTRANCE_SOUND), executable="ffmpeg",
        before_options="-nostdin", options="-vn",
    ))
    try:
        voice_client.play(source, after=after)
    except Exception:
        source.cleanup()
        raise

    logger.info("[AUDIO] Entrance playback started: %s", ENTRANCE_SOUND.name)
    try:
        await asyncio.wait_for(finished, timeout=30)
    except (asyncio.CancelledError, TimeoutError):
        if voice_client.source is source:
            voice_client.stop()
        raise
    if source.frames == 0:
        raise RuntimeError("FFmpeg produced no audio. Check its console output.")
    logger.info(
        "[AUDIO] Playback completed: %s frames (%.2fs). Listener reception is unverified.",
        source.frames, source.frames * 0.02,
    )
