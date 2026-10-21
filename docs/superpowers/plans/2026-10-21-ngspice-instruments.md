# Ngspice instruments implementation plan

Goal: connect the current desktop schematic to real ngspice and functional instrument panels.
Architecture: restricted compiler + cancellable subprocess runner + sampled result; Tk worker/poll loop keeps UI responsive. No new Python runtime dependencies.
Spec: ../specs/2026-10-21-ngspice-instruments.md

- [x] Write failing integration tests in prototype/tests/test_spice.py: RC, RL, DC divider, diode and switch, source validation, sine, AC cutoff, missing engine, invalid bounds.
- [x] Implement prototype/workbench/spice.py: Analysis, Result, source compiler, deck compiler, parse_table, Engine.run/cancel. Retain netlist/log/data export. Real ngspice test every analysis.
- [x] Implement prototype/workbench/measurements.py with tested differential readings, RMS and windowed spectrum interpolation; zero reference must fail for transfer ratio.
- [x] Implement prototype/workbench/instruments.py for editable generator, node-selectable meter/Bode/logic/spectrum panels and data export.
- [x] Integrate async run/stop/settings/DC analysis and advanced tools into existing app.py; handle errors and stale results on edits.
- [x] Exercise UI with Xvfb, retain actual screenshots and numerical reports. Run all tests, independently review diff, publish tested branch.

Review focus: no arbitrary SPICE directives from value fields; sample vectors align with adaptive time values; edits invalidate results; stop actually stops; absent engine fails clearly. Preserve upstream and document partial parity and exact external-project license decisions.
