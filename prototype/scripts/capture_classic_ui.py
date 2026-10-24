"""Capture real running Tk CAD workbench in a virtual display.

Requires DISPLAY and Pillow. The PNG is a captured application window, not a mockup.
"""
import argparse
import os
import sys
from pathlib import Path

if not os.environ.get("DISPLAY"):
    raise SystemExit("A graphical DISPLAY is required for a screenshot")

from PIL import ImageGrab
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workbench.app import Workbench


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reports/classic-workbench.png")
    args = parser.parse_args()
    app = Workbench()
    try:
        app.update_idletasks()
        app.update()
        app.geometry("1460x900+20+20")
        app.update_idletasks()
        app.update()
        x, y = app.winfo_rootx(), app.winfo_rooty()
        w, h = app.winfo_width(), app.winfo_height()
        if min(w, h) < 500:
            raise RuntimeError(f"Unexpected workbench size {w}x{h}")
        image = ImageGrab.grab(bbox=(x, y, x+w, y+h))
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
        print(f"Captured {path} ({image.width}x{image.height})")

        # Capture genuine modal picker and generator dialogs, too. Their
        # contents are native live Tk widgets attached to the current app.
        app.component_browser()
        app.update()
        picker = next(w for w in app.winfo_children()
                      if w.winfo_class() == "Toplevel"
                      and "Select a Component" in w.title())
        picker.geometry("1060x680+80+80")
        app.update_idletasks()
        app.update()
        ImageGrab.grab(bbox=(picker.winfo_rootx(), picker.winfo_rooty(),
                             picker.winfo_rootx()+picker.winfo_width(),
                             picker.winfo_rooty()+picker.winfo_height())
                       ).save(path.with_name("classic-component-picker.png"))
        picker.destroy()
        app.update()

        app.generator()
        app.update_idletasks()
        app.update()
        generator = next(w for w in app.winfo_children()
                         if w.winfo_class() == "Toplevel"
                         and "Function Generator" in w.title())
        generator.geometry("+180+140")
        app.update_idletasks()
        app.update()
        ImageGrab.grab(bbox=(generator.winfo_rootx(), generator.winfo_rooty(),
                             generator.winfo_rootx()+generator.winfo_width(),
                             generator.winfo_rooty()+generator.winfo_height())
                       ).save(path.with_name("classic-function-generator.png"))
        print("Captured real component catalog and generator dialogs")
        generator.destroy()
    finally:
        app.destroy()


if __name__ == "__main__":
    main()
