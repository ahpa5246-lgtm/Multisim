# Desktop foundation implementation plan

Goal: preserve a mature circuit editor and add reproducible build/numerical verification.
Architecture: pinned Qt6 Qucs-S submodule; standalone Python orchestration and ngspice regression.
Spec: docs/DESIGN.md.

- [x] Inspect empty target and upstream build requirements; pin source revision.
- [x] Add scripts/build.py to configure, build and install without shell interpolation.
- [x] Add RC fixture, analytic validator, and tests for numerical errors, NaN, missing samples and solver absence.
- [x] Add CI jobs for unit tests, real ngspice and Linux GUI compilation.
- [x] Document precise parity gaps and review evidence.
- [ ] Obtain successful remote build and solver logs.
- [ ] Build Windows package and perform editor wiring/save/load/run interaction test.

Review focus: missing dependency must fail; nonfinite data must fail; inadequate time coverage must fail; file paths containing spaces must work; subprocess failure must propagate.
