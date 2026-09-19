import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from app.commands.voice import VoiceCommands
from app.services import audio


class VoiceTests(unittest.IsolatedAsyncioTestCase):
    def interaction(self):
        vc = Mock()
        vc.is_connected.return_value = True
        channel = Mock()
        channel.name = 'Test'
        channel.permissions_for.return_value = SimpleNamespace(connect=True, speak=True)
        vc.channel = channel
        response = SimpleNamespace(defer=AsyncMock(), send_message=AsyncMock())
        async def connect():
            response.defer.assert_awaited_once()
            return vc
        channel.connect = AsyncMock(side_effect=connect)
        interaction = SimpleNamespace(
            guild=SimpleNamespace(voice_client=None, me=SimpleNamespace(voice=None)),
            user=SimpleNamespace(voice=SimpleNamespace(channel=channel)),
            response=response, edit_original_response=AsyncMock(),
        )
        return interaction, vc

    async def test_acknowledged_before_connection(self):
        interaction, vc = self.interaction()
        with patch('app.commands.voice.play_entrance_sound', new_callable=AsyncMock) as play:
            await VoiceCommands.join.callback(VoiceCommands(Mock()), interaction)
        play.assert_awaited_once_with(vc)
        interaction.edit_original_response.assert_awaited_once_with(content='Joined **Test**.')

    async def test_playback_failure_is_not_connection_failure(self):
        interaction, _ = self.interaction()
        with patch('app.commands.voice.play_entrance_sound', new_callable=AsyncMock) as play:
            play.side_effect = RuntimeError('No audio')
            await VoiceCommands.join.callback(VoiceCommands(Mock()), interaction)
        self.assertEqual(interaction.edit_original_response.call_args.kwargs['content'],
                         'Entrance sound failed. No audio')

    def client(self):
        vc = Mock()
        vc.is_connected.return_value = True
        vc.is_playing.return_value = False
        vc.is_paused.return_value = False
        return vc

    async def test_busy_does_not_create_ffmpeg(self):
        vc = self.client()
        vc.is_playing.return_value = True
        with patch.object(audio.ENTRANCE_SOUND.__class__, 'is_file', return_value=True), \
             patch.object(audio.shutil, 'which', return_value='ffmpeg'), \
             patch.object(audio.discord, 'FFmpegPCMAudio') as factory:
            with self.assertRaisesRegex(RuntimeError, 'already playing'):
                await audio.play_entrance_sound(vc)
            factory.assert_not_called()

    async def test_failed_start_cleans_up_source(self):
        vc = self.client()
        vc.play.side_effect = discord_error = RuntimeError('start failed')
        with patch.object(audio.ENTRANCE_SOUND.__class__, 'is_file', return_value=True), \
             patch.object(audio.shutil, 'which', return_value='ffmpeg'), \
             patch.object(audio.discord, 'FFmpegPCMAudio') as factory:
            with self.assertRaisesRegex(RuntimeError, str(discord_error)):
                await audio.play_entrance_sound(vc)
            factory.return_value.cleanup.assert_called_once()

    async def test_real_decoder_and_thread_callback(self):
        vc = self.client()
        tasks = []
        def play(source, *, after):
            def consume():
                try:
                    while source.read():
                        pass
                    after(None)
                finally:
                    source.cleanup()
            tasks.append(asyncio.create_task(asyncio.to_thread(consume)))
        vc.play.side_effect = play
        await audio.play_entrance_sound(vc)
        await asyncio.gather(*tasks)
        source = vc.play.call_args.args[0]
        self.assertGreater(source.frames, 100)

    async def test_empty_decoder_output_is_failure(self):
        vc = self.client()
        vc.play.side_effect = lambda source, after: after(None)
        with patch.object(audio.ENTRANCE_SOUND.__class__, 'is_file', return_value=True), \
             patch.object(audio.shutil, 'which', return_value='ffmpeg'), \
             patch.object(audio.discord, 'FFmpegPCMAudio'):
            with self.assertRaisesRegex(RuntimeError, 'no audio'):
                await audio.play_entrance_sound(vc)

    async def test_thread_error_reaches_command(self):
        vc = self.client()
        vc.play.side_effect = lambda source, after: after(RuntimeError('encoder failed'))
        with patch.object(audio.ENTRANCE_SOUND.__class__, 'is_file', return_value=True), \
             patch.object(audio.shutil, 'which', return_value='ffmpeg'), \
             patch.object(audio.discord, 'FFmpegPCMAudio'):
            with self.assertRaisesRegex(RuntimeError, 'encoder failed'):
                await audio.play_entrance_sound(vc)


if __name__ == '__main__':
    unittest.main()

class EncryptionTests(unittest.IsolatedAsyncioTestCase):
    async def test_unready_encryption_blocks_playback(self):
        vc = Mock()
        vc._connection = SimpleNamespace(dave_protocol_version=1, can_encrypt=False)
        vc.is_connected.return_value = True
        with self.assertRaisesRegex(RuntimeError, 'encryption did not become ready'):
            await audio.wait_for_voice_encryption(vc, timeout=0)

    async def test_ready_encryption_proceeds(self):
        vc = Mock()
        vc._connection = SimpleNamespace(dave_protocol_version=1, can_encrypt=True)
        await audio.wait_for_voice_encryption(vc, timeout=0)

    async def test_wrapper_preserves_decoder_error(self):
        source = Mock()
        source._current_error = RuntimeError('decoder failed')
        wrapped = audio.MeasuredAudio(source)
        self.assertIs(wrapped._current_error, source._current_error)
