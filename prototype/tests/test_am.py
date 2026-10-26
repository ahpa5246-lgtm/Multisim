"""Analytic and real-ngspice checks for the lecture's AM Example 1."""
import math
import os
from pathlib import Path
import shutil
import unittest

from workbench.core import Document
from workbench.spice import Analysis, Engine, compile_deck, source_value, am_parameters

FIXTURE=Path(__file__).resolve().parents[2]/'examples'/'am-example1.ocw.json'

class AMSourceUnitTests(unittest.TestCase):
    def test_source_parameters(self):
        self.assertEqual(am_parameters('AM(3.55 2.35 20 1)'),(3.55,2.35,20,1))
        self.assertEqual(source_value('AM(3.55 2.35 20 1)'), 'AM(3.55 2.35 20 1)')
        for value in ('AM(3.55 2.35 1 20)', 'AM(0 2 20 1)', 'AM(3 -2 20 1)',
                      'AM(3 2 20)', 'AM(3 2 nan 1)', 'AM(3 2 20 0)',
                      'AM(3 2 20 1)\\n.end'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                source_value(value)
    def test_fixture_and_deck(self):
        doc=Document.load(FIXTURE)
        deck,nets,nodes,sources=compile_deck(doc,Analysis(duration=1,points=4000))
        self.assertIn('BV1 ', deck)
        self.assertIn('cos(2*pi*1*time)',deck)
        self.assertIn('cos(2*pi*20*time)',deck)
        self.assertIn('VV1 ',deck)
        self.assertIn('i(vV1)',deck)
        self.assertEqual(sources,['V1'])
        self.assertNotEqual(nets[('V1',0)],'0')
        self.assertEqual(nets[('V1',1)],'0')
        with self.assertRaisesRegex(ValueError,'transient'):
            compile_deck(doc,Analysis(kind='ac'))

@unittest.skipUnless(shutil.which('ngspice') or os.environ.get('OCW_NGSPICE'), 'ngspice required for real AM solver verification')
class AMSourceNgspiceTests(unittest.TestCase):
    def test_waveform_lecture_envelope(self):
        doc=Document.load(FIXTURE)
        out=Engine(os.environ.get('OCW_NGSPICE')).run(doc,Analysis(duration=1,points=5000))
        v=out.voltages[out.nets[('V1',0)]]
        def sample(t):
            k=min(range(len(out.axis)),key=lambda i:abs(out.axis[i]-t))
            self.assertLess(abs(out.axis[k]-t),0.002)
            return v[k]
        # fc=20 Hz makes carrier cosine positive at every quarter-period.
        for t,expected in [(0,5.9),(.25,3.55),(.5,1.2),(.75,3.55),(1,5.9)]:
            with self.subTest(t=t):
                self.assertAlmostEqual(sample(t),expected,delta=0.09)
        self.assertAlmostEqual((5.9-1.2)/(5.9+1.2),2.35/3.55,places=6)
