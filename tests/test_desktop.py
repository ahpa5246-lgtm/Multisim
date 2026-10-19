import unittest
from scripts.verify_desktop import is_known_setup_notice

class StartupNoticeTests(unittest.TestCase):
    def test_only_identified_informational_notice_can_be_acknowledged(self):
        self.assertTrue(is_known_setup_notice('Set simulator'))
        for title in ['Qucs', 'Save changes?', 'Overwrite file', '', 'Set simulator - Error']:
            self.assertFalse(is_known_setup_notice(title))

class NoticeRaceTests(unittest.TestCase):
    def test_disappearing_notice_after_return_is_not_a_startup_failure(self):
        from unittest.mock import patch
        import subprocess
        from scripts.verify_desktop import acknowledge_setup_notice
        results = [subprocess.CompletedProcess([], 1, '', 'BadWindow (invalid Window parameter)'),
                   subprocess.CompletedProcess([], 1, '', 'BadWindow')]
        with patch('scripts.verify_desktop.subprocess.run', side_effect=results):
            acknowledge_setup_notice('123')

    def test_badwindow_does_not_hide_a_still_open_notice(self):
        from unittest.mock import patch
        import subprocess
        from scripts.verify_desktop import acknowledge_setup_notice
        results = [subprocess.CompletedProcess([], 1, '', 'BadWindow'),
                   subprocess.CompletedProcess([], 0, 'Set simulator', '')]
        with patch('scripts.verify_desktop.subprocess.run', side_effect=results):
            with self.assertRaises(subprocess.CalledProcessError):
                acknowledge_setup_notice('123')

    def test_other_x11_failures_are_not_ignored(self):
        from unittest.mock import patch
        import subprocess
        from scripts.verify_desktop import acknowledge_setup_notice
        with patch('scripts.verify_desktop.subprocess.run', return_value=subprocess.CompletedProcess([], 1, '', 'Cannot open display')):
            with self.assertRaises(subprocess.CalledProcessError):
                acknowledge_setup_notice('123')
