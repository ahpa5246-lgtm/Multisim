"""Visual-workspace regression: exercise real native widgets, not mockups."""
import os
import gc
import unittest

from workbench.app import Workbench


@unittest.skipUnless(os.environ.get("DISPLAY"), "Needs Tk / Xvfb")
class ClassicShellTests(unittest.TestCase):
    def setUp(self):
        self.app = Workbench()
        self.app.update()

    def tearDown(self):
        self.app.destroy()
        self.app = None
        gc.collect()

    def test_project_navigator_is_connected_to_design(self):
        app = self.app
        roots = app.project_tree.get_children()
        self.assertEqual(len(roots), 1)
        self.assertEqual(len(app.project_tree.get_children(roots[0])), 3)
        self.assertIn(app.doc.title, app.project_tree.item(roots[0], "text"))
        self.assertIn("4 components", app.sheet_summary.get())
        self.assertIn("wires", app.sheet_summary.get())

    def test_classic_component_shortcut_places_real_part(self):
        app = self.app
        def descendants(parent):
            for child in parent.winfo_children():
                yield child
                yield from descendants(child)
        from tkinter import Button
        controls = [w for w in descendants(app) if isinstance(w, Button)]
        quick = next(c for c in controls if c.cget("text") == "BJT NPN")
        quick.invoke()
        self.assertEqual(app.mode, "NPN")
        from types import SimpleNamespace
        before = len(app.doc.parts)
        app.canvas_down(SimpleNamespace(x=850, y=300))
        self.assertEqual(len(app.doc.parts), before + 1)
        self.assertEqual(app.doc.parts[-1].kind, "NPN")

    def test_vector_symbol_terminals_and_junctions_visible(self):
        app = self.app
        self.assertGreater(len(app.canvas.find_withtag("terminal")), 0)
        self.assertGreater(len(app.canvas.find_withtag("junction")), 0)
        # Red junctions are above terminals in the Tk canvas draw stack.
        self.assertLess(max(app.canvas.find_withtag("terminal")),
                        min(app.canvas.find_withtag("junction")))
        self.assertGreater(len(app.canvas.find_withtag("worksheet_grid")), 100)

    def test_project_actions_open_existing_views(self):
        app = self.app
        app.project_tree.selection_set("project_components")
        app._project_open()
        self.assertEqual(app.report_tabs.index("current"), 2)
        app.project_tree.selection_set("project_netlist")
        app._project_open()
        self.assertEqual(app.report_tabs.index("current"), 0)
        self.assertIn("R1", app.panel_results.get("1.0", "end"))
