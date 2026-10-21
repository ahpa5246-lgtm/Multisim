"""Run with DISPLAY set (CI uses Xvfb); exercises real Tk widgets."""
import os, time, shutil
import unittest
from types import SimpleNamespace
from workbench.app import Workbench

@unittest.skipUnless(os.environ.get('DISPLAY'), 'Requires a real Tk display / Xvfb')
class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.app = Workbench()
        self.app.update()
    def tearDown(self):
        self.app.destroy()
    def test_sheet_tracks_placement_and_undo(self):
        a=self.app
        self.assertEqual(len(a.component_sheet.get_children()), 4)
        a.set_mode('R')
        a.canvas_down(SimpleNamespace(x=800,y=180))
        self.assertEqual(len(a.component_sheet.get_children()),5)
        a.undo()
        self.assertEqual(len(a.component_sheet.get_children()),4)
    def test_sheet_selection_selects_schematic(self):
        a=self.app
        a.component_sheet.selection_set('R1')
        a.component_sheet.event_generate('<<TreeviewSelect>>')
        a.update()
        self.assertEqual(a.selected,'R1')
    def test_zoom_and_tool_selection(self):
        a=self.app
        a.tool_buttons['wire'].invoke()
        self.assertEqual(a.mode,'wire')
        a.zoom(1.25)
        self.assertEqual(a.zoom_value.get(),'125%')
        a.cancel()
        self.assertEqual(a.mode,'select')
    def test_rotation_preserves_connected_pins(self):
        a=self.app
        a.selected='R1'
        resistor=next(p for p in a.doc.parts if p.id=='R1')
        old=resistor.pins()
        a.rotate()
        self.assertEqual(resistor.rotation,90)
        self.assertTrue(any(w.b==resistor.pins()[0] for w in a.doc.wires))
        self.assertNotEqual(old,resistor.pins())
        a.undo()
        self.assertEqual(next(p for p in a.doc.parts if p.id=='R1').rotation,0)
    @unittest.skipUnless(shutil.which('ngspice') or os.environ.get('OCW_NGSPICE'),'Requires ngspice')
    def test_run_opens_scope_with_real_transient(self):
        a=self.app
        a.run()
        until=time.monotonic()+5
        while a._job is not None and time.monotonic()<until:a.update();time.sleep(.01)
        a.update()
        self.assertIsNotNone(a.timeline)
        times,history,nets=a.timeline
        self.assertGreater(history[nets[('C1',0)]][-1],4.9)
        scopes=[w for w in a.winfo_children() if w.winfo_class()=='Toplevel']
        self.assertTrue(any('Oscilloscope' in w.title() for w in scopes))
    def test_cursor_preview_does_not_change_document(self):
        a=self.app
        count=len(a.doc.parts)
        a.set_mode('C')
        a.canvas_move(SimpleNamespace(x=800,y=180))
        self.assertTrue(a.canvas.find_withtag('placement'))
        self.assertEqual(len(a.doc.parts),count)
        a.cancel()
        self.assertFalse(a.canvas.find_withtag('placement'))
    def test_generator_applies_real_source_and_invalidates_result(self):
        from tkinter import ttk
        a=self.app;a.generator();a.update()
        win=next(w for w in a.winfo_children() if w.winfo_class()=='Toplevel')
        button=next(w for w in win.winfo_children() if isinstance(w,ttk.Button))
        button.invoke();a.update()
        self.assertEqual(next(p for p in a.doc.parts if p.kind=='V').value,'SIN(0 5 1000)')
        self.assertIsNone(a.result)
    @unittest.skipUnless(shutil.which('ngspice') or os.environ.get('OCW_NGSPICE'),'Requires ngspice')
    def test_bode_and_meter_panels_use_result(self):
        from workbench.spice import Engine,Analysis
        a=self.app
        a.result=Engine().run(a.doc,Analysis(kind='ac'))
        a.trace_panel('Bode');a.update()
        windows=[w for w in a.winfo_children() if w.winfo_class()=='Toplevel']
        self.assertTrue(any('Bode' in w.title() for w in windows))
        a.result=Engine().run(a.doc,Analysis(kind='op'))
        a.multimeter();a.update()
        self.assertTrue(any('Differential Meter' in w.title() for w in a.winfo_children() if w.winfo_class()=='Toplevel'))
    def test_stop_discards_already_queued_success(self):
        import queue,copy
        from workbench.spice import Engine
        a=self.app;a._job=queue.Queue();a.engine=Engine();a.result=None
        a._job.put((object(),None))
        a.stop()
        called=[]
        a._poll_analysis(copy.deepcopy(a.doc),lambda:called.append(True))
        self.assertIsNone(a.result);self.assertFalse(called)
