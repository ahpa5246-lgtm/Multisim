import unittest
from scripts.verify_netlist import validate_rc_netlist

class NetlistTests(unittest.TestCase):
    good = '* RC\nV1 in 0 DC 5\nR1 in out 1k tc1=0\nC1 out 0 1u\n.end\n'

    def test_correct_topology_and_values(self):
        self.assertEqual(validate_rc_netlist(self.good)['components'], 3)

    def test_disconnected_ground_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_rc_netlist(self.good.replace('C1 out 0', 'C1 out floating'))

    def test_wrong_value_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_rc_netlist(self.good.replace('1k', '2k'))

    def test_missing_component_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_rc_netlist(self.good.replace('C1 out 0 1u\n', ''))
