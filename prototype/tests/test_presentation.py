"""Presentation regressions: real widgets and a real ngspice AM circuit."""
import gc
import math
import os
import shutil
import unittest
from tkinter import ttk

from workbench.app import Workbench
from workbench.course import BY_ID
from workbench.measurements import mean
from workbench.spice import Engine


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


@unittest.skipUnless(os.environ.get('DISPLAY'), 'Requires a real Tk display')
class PresentationUITests(unittest.TestCase):
    def setUp(self):
        self.app = Workbench()
        self.app.update()

    def tearDown(self):
        self.app.destroy()
        self.app = None
        gc.collect()

    def test_generator_apply_preserves_existing_sources(self):
        source = next(p for p in self.app.doc.parts if p.kind == 'V')
        for value in ('3.3', 'SIN(-1.2 .4 200)', 'PULSE(-2 4 0 1u 1u 499u 1m)',
                      'PULSE(-1 1 0 500u 500u 0 1m)'):
            with self.subTest(value=value):
                source.value = value
                self.app.generator()
                self.app.update()
                win = next(w for w in self.app.winfo_children() if w.winfo_class() == 'Toplevel')
                next(w for w in win.winfo_children() if isinstance(w, ttk.Button)).invoke()
                from workbench.spice import source_value
                self.assertEqual(source_value(source.value), source_value(value))

    def test_generator_switching_source_loads_its_settings(self):
        source = next(p for p in self.app.doc.parts if p.kind == 'V')
        source.value = 'SIN(2 3 400)'
        second = self.app.doc.add('V', 900, 300, 'SIN(-1 .2 700)')
        self.app.generator()
        self.app.update()
        win = next(w for w in self.app.winfo_children() if w.winfo_class() == 'Toplevel')
        selector = next(w for w in descendants(win) if isinstance(w, ttk.Combobox))
        selector.set(second.id)
        self.app.update()
        next(w for w in win.winfo_children() if isinstance(w, ttk.Button)).invoke()
        self.assertEqual(second.value, 'SIN(-1 .2 700)')
        self.assertEqual(source.value, 'SIN(2 3 400)')

    @unittest.skipUnless(shutil.which('ngspice') or os.environ.get('OCW_NGSPICE'), 'Requires ngspice')
    def test_am_instrument_windows_draw_real_data(self):
        self.app.load_am()
        self.assertTrue(self.app.doc.wires)
        self.assertEqual(self.app.active_experiment, 'am-jfet')
        self.app.result = Engine().run(self.app.doc, self.app.analysis)
        for method, title in (('scope', 'Oscilloscope'), ('multimeter', 'Differential Meter'),
                              ('logic', 'Logic traces'), ('spectrum_panel', 'Voltage spectrum')):
            with self.subTest(instrument=method):
                getattr(self.app, method)()
                self.app.update()
                win = next(w for w in self.app.winfo_children()
                           if w.winfo_class() == 'Toplevel' and title in w.title())
                if method == 'scope':
                    selectors = [w for w in descendants(win) if isinstance(w, ttk.Combobox)]
                    self.assertIn('Off', selectors[1]['values'])
                    selectors[1].set('Off');self.app.update()
                canvases = [w for w in descendants(win) if w.winfo_class() == 'Canvas']
                if canvases:
                    self.assertTrue(any(c.find_all() for c in canvases))
                else:
                    text = next(w for w in descendants(win) if w.winfo_class() == 'Text')
                    self.assertIn('RMS', text.get('1.0', 'end'))
                win.destroy()

    def test_fit_actually_fits_large_course_circuit(self):
        self.app.doc = BY_ID['npn-frequency'].document()
        self.app.fit()
        self.app.update()
        self.assertLess(self.app.scale_factor, 1)
        for part in self.app.doc.parts:
            self.assertLess((part.x + 130) * self.app.scale_factor, self.app.canvas.winfo_width())
            self.assertLess((part.y + 100) * self.app.scale_factor, self.app.canvas.winfo_height())


@unittest.skipUnless(shutil.which('ngspice') or os.environ.get('OCW_NGSPICE'), 'Requires ngspice')
class AMCircuitTests(unittest.TestCase):
    def run_am(self, message='SIN(-1.2 .4 200)'):
        experiment = BY_ID['am-jfet']
        from pathlib import Path
        from workbench.core import Document
        document = Document.load(Path(__file__).resolve().parents[2]/'examples/am-jfet.ocw.json')
        next(p for p in document.parts if p.id == 'VM').value = message
        result = Engine().run(document, experiment.analysis)
        values = result.voltages[result.labels['out']]
        pairs = [(t, y) for t, y in zip(result.axis, values) if t >= .005]
        times, values = map(list, zip(*pairs))
        def amplitude(frequency):
            a = 2 * mean(times, [y * math.sin(2 * math.pi * frequency * t) for t, y in pairs])
            b = 2 * mean(times, [y * math.cos(2 * math.pi * frequency * t) for t, y in pairs])
            return math.hypot(a, b)
        return result, amplitude

    def test_real_jfet_produces_carrier_and_symmetric_sidebands(self):
        result, amplitude = self.run_am()
        carrier, lower, upper = [amplitude(f) for f in (10000, 9800, 10200)]
        self.assertGreater(carrier, .030)
        self.assertLess(carrier, .032)
        self.assertAlmostEqual(lower, upper, delta=.0001)
        self.assertGreater(2 * lower / carrier, .23)
        self.assertLess(2 * lower / carrier, .27)
        self.assertEqual(BY_ID['am-jfet'].components[0][2], 'BF245B')
        self.assertIn('JJ1 ', result.deck)

    def test_removing_message_removes_sidebands(self):
        result, amplitude = self.run_am('-1.2')
        self.assertGreater(amplitude(10000), .025)
        self.assertLess(amplitude(9800), .0001)
        self.assertLess(amplitude(10200), .0001)
