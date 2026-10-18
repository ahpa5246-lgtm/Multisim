# Desktop foundation implementation plan

Goal: preserve a mature circuit editor and add reproducible build/numerical verification.
Architecture: pinned Qt6 Qucs-S submodule; standalone Python orchestration and ngspice regression.
Spec: docs/DESIGN.md.

- [x] Inspect empty target and upstream build requirements; pin source revision.
- [x] Add scripts/build.py to configure, build and install without shell interpolation.
- [x] Add RC fixture, analytic validator, and tests for numerical errors, NaN, missing samples and solver absence.
- [x] Add CI jobs for unit tests, real ngspice and Linux GUI compilation.
- [x] Document precise parity gaps and review evidence.
- [x] Obtain successful remote build and solver logs (run 39078237801).
- [x] Capture and visually inspect actual Linux startup (run 39089285681, artifact 12122511783); startup alone is not interaction validation.
- [x] Export RC schematic with the compiled editor and validate values/connectivity in CI (run 39093208887).
- [x] Compile on native Windows and run the same schematic export contract (run 39096265664).
- [x] Simulate the actual editor-exported RC devices with explicit zero-charge test conditions (run 39099994687).
- [x] Visually inspect the loaded RC schematic in desktop and narrow Linux windows (run 39106858952; narrow analysis block clips).
- [x] Exercise GUI Save As and validate the saved circuit through editor export (run 39126560602).
- [x] Visually inspect a fresh GUI process reopening the GUI-saved RC copy (run 39144396633).
- [ ] Trigger F2 in reopened Linux GUI and inspect a newly produced dataset.
- [ ] Build Windows package and perform editor wiring/save/load/run interaction test.

Review focus: missing dependency must fail; nonfinite data must fail; inadequate time coverage must fail; file paths containing spaces must work; subprocess failure must propagate.
