import tempfile,unittest
from pathlib import Path
from workbench.interop import inspect_container,FORMATS,save_report

class InspectorTests(unittest.TestCase):
    def inspect(self,data):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'sample.bin';path.write_bytes(data)
            out=inspect_container(path);self.assertEqual(path.read_bytes(),data)
            return out
    def test_section_metadata_and_original_preserved(self):
        # Synthetic section metadata only, intentionally not a valid PKWare payload.
        data=FORMATS[0][0]+(5).to_bytes(8,'little')+(5).to_bytes(4,'little')+(3).to_bytes(4,'little')+b'abc'
        result=self.inspect(data)
        self.assertEqual(result['sections'][0]['compressed_bytes'],3)
        self.assertEqual(result['declared_xml_bytes'],5)
        self.assertEqual(result['circuit_mapping'],'Not performed')
    def test_truncated_and_oversized_section_rejected(self):
        for data in (FORMATS[0][0],FORMATS[0][0]+(5).to_bytes(8,'little'),FORMATS[0][0]+(5).to_bytes(8,'little')+(6).to_bytes(4,'little')+(1).to_bytes(4,'little')+b'a'):
            with self.assertRaises(ValueError):self.inspect(data)
    def test_jet_and_unknown_detected_by_header(self):
        self.assertEqual(self.inspect(FORMATS[2][0]+b'123')['format'],'Jet component database')
        self.assertEqual(self.inspect(b'not a circuit')['format'],'Unknown')

    def test_report_cannot_overwrite_original_or_hardlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'original.ms14';source.write_bytes(b'original')
            alias=Path(tmp)/'alias.json';alias.hardlink_to(source)
            for target in (source,alias):
                with self.assertRaises(ValueError):save_report(source,target,'report')
            target=Path(tmp)/'report.json';save_report(source,target,'report')
            self.assertEqual(target.read_text(),'report\n')
            self.assertEqual(source.read_bytes(),b'original')

    def test_excessive_sections_rejected(self):
        data=FORMATS[0][0]+(4097).to_bytes(8,'little')+((1).to_bytes(4,'little')*2+b'x')*4097
        with self.assertRaisesRegex(ValueError,'4096 sections'):self.inspect(data)
    @unittest.skipUnless(Path('/dev/zero').exists(),'requires Linux special file')
    def test_special_file_rejected(self):
        with self.assertRaisesRegex(ValueError,'regular file'):inspect_container('/dev/zero')
