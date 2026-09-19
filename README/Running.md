# Running the bot

From the project root, install the Python dependencies:

```powershell
python -m pip install -r requirements_for_discordBot.txt
```

Install FFmpeg and make sure `ffmpeg -version` works in the same terminal.
Place the entrance tune at `sounds/nokia-tune-1600-36527.mp3`; this directory
is ignored by Git, so a fresh checkout does not include the recording.
Set `DISCORD_TOKEN` in your local `.env`, then run `python watcher.py`.
The bot runs `app/utils/dependency_check.py` before importing third-party packages:
it resolves the requirements using the active Python interpreter, then checks
FFmpeg and the entrance sound. A failed check stops startup. You can also start
the bot directly with `python music_bot.py` from the project root.

`app/utils/console_style.py` provides timestamped, colored console logging.
Redirected output is plain text; set `NO_COLOR` to disable terminal colors.
Discord uses the shared handler so errors are not printed twice.

## Checking entrance playback

Join a normal voice channel and use `/join`. The bot needs Connect and Speak
permissions and must not be server-muted or locally muted by the listener.
Stage channels require the bot to be allowed to speak.

The command acknowledges immediately, then connects and plays the tune. Repeating
`/join` while audio is playing reports that playback is busy. Decoder and player
errors are reported separately from connection errors.

The console reports the number of decoded audio frames at completion. This proves
that the local player processed audio, not that Discord clients received it.
If playback completes but is silent, check the bot's per-user volume/local mute,
compare with another listener, and retry `/leave` followed by `/join`. If both
listeners hear nothing, investigate voice transport or encryption using a fresh
log. Do not enable raw gateway DEBUG logging: it includes session credentials.

Run local regression checks with `python -m unittest discover -s tests -v`.
The decoder integration test requires FFmpeg and the local MP3. These checks do
not log in to Discord or verify sound at a listener.
