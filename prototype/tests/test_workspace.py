"""Run with DISPLAY set (CI uses Xvfb); exercises real Tk widgets."""
import os
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
    def test_run_opens_scope_with_real_transient(self):
        a=self.app
        a.run()
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
