import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pc_agent import telegram_bot


class VoiceTranscriptionTests(unittest.TestCase):
    def test_convert_audio_to_wav_uses_ffmpeg_binary(self):
        fake_module = types.SimpleNamespace(get_ffmpeg_exe=lambda: "C:/ffmpeg.exe")

        with tempfile.NamedTemporaryFile(suffix=".oga", delete=False) as handle:
            handle.write(b"fake audio")
            temp_path = Path(handle.name)

        try:
            with patch.dict(sys.modules, {"imageio_ffmpeg": fake_module}), \
                 patch.object(telegram_bot.subprocess, "run") as run_mock:
                result = telegram_bot._convert_audio_to_wav(temp_path)

            self.assertEqual(result, temp_path.with_suffix(".wav"))
            run_mock.assert_called_once()
            self.assertEqual(run_mock.call_args.args[0][0], "C:/ffmpeg.exe")
        finally:
            temp_path.unlink(missing_ok=True)
            if 'result' in locals() and result and result.exists():
                result.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
