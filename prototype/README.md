# Open Circuit Workbench — native desktop UI prototype

This independent Python/Tkinter prototype is an **original, offline schematic editor inspired by the documented NI Multisim 14.x workspace layout**. It preserves the existing Qucs-S submodule and ngspice verification work in the parent repository and is **not yet connected to Qucs-S internally**. No proprietary NI code, icons or binary assets are included.

## Windows: start the GUI

Install Python 3.10+ from python.org using the standard Tcl/Tk option, then open this `prototype` folder and double-click `START_WINDOWS.bat`. Alternatively run `python run_workbench.py`. Linux: `sh START_LINUX.sh`.

No API keys, web connection or paid software needed. The Python files use only its standard library.

## Tested capabilities

* Native menus, component toolbars, project hierarchy, scrollable dotted drawing canvas, instruments rail, results/netlists tabs.
* Place, move, rotate, edit, undo/redo and delete parts; join connections via orthogonal schematic wires; zoom and grid controls.
* Save/reopen editable `.ocw.json` projects; preview and export SPICE `.cir` netlists for supported linear elements.
* Calculate educational resistive/capacitive transients with DC voltage sources through MNA and backward Euler; show measured node voltages on a virtual oscilloscope.
* Startup RC example: 5 V, 1 kΩ, 1 µF, τ=1 ms. The response approximately reaches 3.16 V after one τ.
* Run `python -m unittest discover -s tests -v` in this folder. Six solver/model unit tests have passed. Linux/Xvfb GUI interaction smoke tests (placement, undo/redo, save/load, scope) have passed.

## Important limitations

**This is not yet NI Multisim-equivalent.** No `.ms14` file support, full database, nonlinear semiconductors, sophisticated SPICE engines in this independent GUI, arbitrary instruments or validated Windows installer. The inductor, diode, LED and switch have graphical symbols, but the local solver supports only R/C and independent DC sources; an inductor is allowed in SPICE export, not the native transient solver. Some instrument buttons explicitly show 'not implemented'. Numerical results are educational and not authoritative SPICE validation. Keep using the parent repository's separate Qucs-S/ngspice engine for production simulation.

## Visual reference and IP

NI Circuit Design Suite Getting Started Guide, 'Multisim User Interface' (menu bar, component toolbar, simulation toolbar, workspace, instrument toolbar): https://download.ni.com/support/manuals/374482h.pdf

Original vector primitives are drawn with Tkinter. This project is not affiliated with NI/Emerson. GPL-2.0-or-later applies to new code; parent Qucs-S and bundled dependencies retain their respective licenses.

## Next engineering milestone

Compile/test the parent Qucs-S backend on Windows; connect real ngspice through a subprocess-backed adapter with input validation, add usable instruments and a component selector; introduce screenshot-based UI regression tests and document functional differences.
