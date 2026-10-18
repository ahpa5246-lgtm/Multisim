import unittest
from scripts.verify_desktop import is_known_setup_notice

class StartupNoticeTests(unittest.TestCase):
    def test_only_identified_informational_notice_can_be_acknowledged(self):
        self.assertTrue(is_known_setup_notice('Set simulator'))
        for title in ['Qucs', 'Save changes?', 'Overwrite file', '', 'Set simulator - Error']:
            self.assertFalse(is_known_setup_notice(title))
