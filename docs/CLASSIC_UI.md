# Classic desktop workbench — visual and functional acceptance

## Reference and scope

This is an **original, open-source classic EDA shell**, not a binary or trademark clone of NI Multisim. The layout follows the public NI *Getting Started with NI Circuit Design Suite* guide, Chapter 2 (menu/standard toolbar, component toolbar, In Use list, left Design Toolbox, center schematic, right instruments toolbar, bottom Spreadsheet View and status bar). Reference: https://docs-be.ni.com/bundle/374482d/raw/resource/enus/374482d.pdf

No NI screenshots, fonts, copyrighted icon assets or proprietary code are bundled. The interface uses Tk widgets and original electrical drawing primitives.

## Changes implemented

- Neutral grey Windows-CAD color system, consistent 9 pt font metrics, crisp focus and active toolbar states, more compact docking and tab strip.
- Three functional top bars: standard actions and simulation, electrical drawing tools, and labeled component shortcuts. All component shortcuts call the existing placement workflow.
- New **Project** navigator inside the Design Toolbox. Double-click the Schematic, Component list, or SPICE netlist nodes to open the corresponding existing workbench view. The existing **Hierarchy** and **Components** tabs remain unchanged in function.
- Document tab styled as a classic active schematic tab; gridded drawing paper, original blue symbol strokes, red wires and connection dots. The resistor symbol is now the recognizable ANSI zigzag, without changing the original electrical pin coordinates.
- Fixed connection-dot paint order: red connected terminal markers render on top of all component terminals. Unconnected pins remain hollow blue circles.
- Restyled **Select a Component** catalog with searchable Master Database, family filters, model provenance, symbol preview on drawing paper and the original Place action.
- Instrument rail and Spreadsheet View retain all existing simulation operations. Bottom status area shows pointer coordinates and simulation engine identification.
- All of the existing simulation backend, project persistence, numerical methods and Qucs-S submodule are untouched.

## Verification

Run from `prototype`:

```bash
python -m compileall -q workbench
xvfb-run -a python -m unittest discover -s tests -v
xvfb-run -a -s "-screen 0 1600x1050x24" python scripts/capture_classic_ui.py --output reports/classic-workbench.png
```

The screenshot script depends on `Pillow` and an X11 display. CI installs them and uploads an actual PNG named `classic-workbench-screenshot`; it is not a design mockup.

Manual verification still required on Windows:
1. Open application and ensure normal 1366+ px layout without clipped controls. Note: narrower windows may need OS-level scaling or future adaptive toolbars.
2. Place resistor, wire and ground, rotate and save/reload; verify schematic remains electrically identical.
3. Open the component catalog, filter/select LM358 and inspect its electrical model.
4. Run transient and DC operations against an installed ngspice binary, read meter and scope.
5. Check menus, keyboard focus, projector explorer navigation and tooltips under Windows display scaling.

## Explicit limitations

This improves **structure and appearance** but does not establish pixel-perfect visual equivalence with a specified Multisim release, native `.ms14` support, Windows installer quality, real instrument parity or numerical equivalence. The Qucs-S Qt application remains a separate upstream editor, not a second skin for this Tk application.
