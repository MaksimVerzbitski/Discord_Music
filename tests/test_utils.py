import io
import logging
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from app.utils import console_style as style, dependency_check as deps


class ConsoleTests(unittest.TestCase):
    def test_setup_once_and_plain_redirected_traceback(self):
        root = logging.getLogger()
        previous, level = root.handlers[:], root.level
        scheduler = logging.getLogger('apscheduler')
        scheduler_level = scheduler.level
        try:
            stream = io.StringIO()
            style.setup_logging(stream=stream)
            style.setup_logging(stream=stream)
            try:
                raise ValueError('sample failure')
            except ValueError:
                logging.getLogger('test').exception('test event')
            output = stream.getvalue()
            self.assertEqual(output.count('test event'), 1)
            self.assertIn('ValueError: sample failure', output)
            self.assertNotIn('\033[', output)
        finally:
            for handler in root.handlers[:]:
                if handler not in previous:
                    root.removeHandler(handler)
                    handler.close()
            root.setLevel(level)
            scheduler.setLevel(scheduler_level)

    def test_color_formatter(self):
        record = logging.LogRecord('test', logging.ERROR, '', 0, 'failure', (), None)
        self.assertIn(style.Colors.RED, style.ConsoleFormatter(True).format(record))


class DependencyTests(unittest.TestCase):
    def test_dependency_outcomes(self):
        scenarios = [
            (True, 0, 'ffmpeg', True, True),
            (False, 0, 'ffmpeg', True, False),
            (True, 1, 'ffmpeg', True, False),
            (True, 0, None, True, False),
            (True, 0, 'ffmpeg', False, False),
        ]
        for requirements, code, ffmpeg, sound, expected in scenarios:
            with self.subTest(scenario=(requirements, code, ffmpeg, sound)), \
                 patch.object(deps.Path, 'is_file', side_effect=[requirements, sound]), \
                 patch.object(deps.subprocess, 'run', return_value=SimpleNamespace(returncode=code, stdout='', stderr='test failure')) as run, \
                 patch.object(deps.shutil, 'which', return_value=ffmpeg):
                self.assertEqual(deps.check_dependencies(), expected)
                if requirements:
                    self.assertEqual(run.call_args.args[0][:3], [deps.sys.executable, '-m', 'pip'])
                else:
                    run.assert_not_called()

    def test_cannot_launch_pip(self):
        with patch.object(deps.Path, 'is_file', return_value=True), \
             patch.object(deps.subprocess, 'run', side_effect=OSError('cannot launch')):
            self.assertFalse(deps.check_dependencies())
