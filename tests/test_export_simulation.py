import unittest
from scripts.verify_rc import measurement_deck

class ExportSimulationTests(unittest.TestCase):
    def test_measurement_changes_commands_but_preserves_exported_devices(self):
        original = '* Exported\nV1 in 0 DC 5\nR1 in out 1K\nC1 0 out 1U\n.control\ntran 1u 2m\n.endc\n.END\n'
        result = measurement_deck(original)
        self.assertTrue(result.startswith(original.split('.control')[0]))
        self.assertTrue(result.endswith('\n.END\n'))
        self.assertIn('tran 10u 5m uic', result)
        self.assertIn('wrdata rc.dat v(out)', result)

    def test_ambiguous_control_blocks_are_rejected(self):
        for text in ['R1 in out 1k\n.end', '.control\n.endc\n.control\n.endc']:
            with self.assertRaises(ValueError):
                measurement_deck(text)
