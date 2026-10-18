import tempfile
import unittest
from pathlib import Path
from scripts.desktop_save import save_copy

class SaveSafetyTests(unittest.TestCase):
    def test_existing_schematic_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'existing.sch'
            path.write_text('original')
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                save_copy(1, '123', path)
            self.assertEqual(path.read_text(), 'original')
