import unittest
from unittest.mock import patch

from pc_agent.tools import system_tools


class VoiceFeedbackMuteTests(unittest.TestCase):
    def setUp(self):
        system_tools._VOICE_FEEDBACK_MUTED = False

    def test_speak_voice_feedback_is_skipped_when_muted(self):
        system_tools.set_voice_feedback_mute(True)

        with patch("subprocess.Popen") as mock_popen:
            system_tools.speak_voice_feedback("hello world")

        mock_popen.assert_not_called()

    def test_toggle_voice_feedback_mute_flips_state(self):
        self.assertFalse(system_tools.is_voice_feedback_muted())

        system_tools.toggle_voice_feedback_mute()
        self.assertTrue(system_tools.is_voice_feedback_muted())

        system_tools.toggle_voice_feedback_mute()
        self.assertFalse(system_tools.is_voice_feedback_muted())


if __name__ == "__main__":
    unittest.main()
