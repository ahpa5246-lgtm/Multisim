import unittest
from scripts.verify_gui_dataset import validate


def fixture():
    times = '\n'.join(str(i*.005/100) for i in range(101))
    voltage = '\n'.join(['5']*101)
    return f'<Qucs Dataset 26.1.1>\n<indep time 101>\n{times}\n</indep>\n<dep tran.v(in) time>\n{voltage}\n</dep>\n<dep tran.v(out) time>\n{voltage}\n</dep>'


class DatasetTests(unittest.TestCase):
    def test_baseline(self):
        self.assertEqual(validate(fixture())['samples'], 101)

    def test_corruptions(self):
        text = fixture()
        cases = [text.replace('time 101', 'time 102'), text.replace('0.005\n', '0.0049\n'),
                 text.replace('\n5\n', '\nnan\n', 1), text.replace('\n5\n', '\n4\n', 1),
                 text.replace('tran.v(out)', 'missing'), text + text,
                 text.replace('0.0\n', '0.001\n', 1)]
        for corrupt in cases:
            with self.subTest(corrupt=corrupt[:50]), self.assertRaises(ValueError):
                validate(corrupt)
