# Review evidence — 2026-10-18

## Delivered foundation
- Empty target inspected through GitHub and git.
- Qucs-S pinned at 46e47e8fabe852a9d6aab41d8a612ff5a78370c1 (upstream VERSION 26.1.1).
- Mature editor retained as submodule; no custom editor or virtual instruments claimed.
- Python build orchestration, RC netlist, analytical validator, failure tests, two CI jobs added.

## Local verification
- `python3 -m unittest discover -s tests -v`: six tests PASS. These test the validator using synthetic analytic data, not the real solver.
- `python3 scripts/verify_rc.py --output reports/rc.json`: FAIL as intended when ngspice is absent. No real numerical result recorded yet.
- `git diff --check`: PASS.
- System package installation blocked by environment setgroups/setuid restrictions; Qt/CMake/ngspice build could not run locally.

## Self-critique
The repository now has an engineering foundation, not a completed Multisim alternative. The Linux CI build is not interactive GUI verification. A passing RC analytic test is not an NI comparison. Windows packaging, custom instruments and ms14 import remain unimplemented. A genuine Multisim file is still needed for interoperability work; a fixture must not be invented.

## Next bounded task
Read CI logs and fix build/simulation failures. Obtain a native Windows build and test placing/wiring/saving/reopening/running an RC schematic. Record screenshots plus actual solver output. Preserve original upstream branding until a reviewed original design is ready.

## Supervision
A bounded hourly follow-up was created for 24 runs starting 2026-10-18 03:15 Asia/Baghdad. Existing general summaries remain separate. Scheduling does not prove a running Codex Cloud session or guarantee tools/quota on future runs.

## Workspace revision — 2026-10-21

User requested a closer match to NI Multisim's interface. This milestone changes the existing independent Tk prototype, not the pinned Qucs-S editor. The previous foundation-only recommendation to preserve the UI is superseded by that explicit request. The mature upstream editor and its notices remain untouched.

### Implemented
- Two compact icon toolbars with original vector artwork, tooltips, keyboard activation and visible selection state.
- Narrow vertical instrument rail; unavailable instruments are disabled and labelled in tooltips.
- In-use component selector and zoom percentage control.
- Resizable spreadsheet area with real component rows linked to schematic selection, properties, placement and undo.
- Component cursor preview without adding anything to the document before placement.
- Reserved status bar space and an RC example that fits the default canvas height.
- GUI tests added to the existing CI workflow using Xvfb.

### Verification
- Python 3.12 / Tcl-Tk 9.0, Linux: `python -m compileall -q prototype/workbench` PASS. This byte-compiles the Python prototype; it is not a compiled Qucs-S binary or Windows package.
- `DISPLAY=127.0.0.1:94 PYTHONPATH=prototype python -m unittest discover -s prototype/tests -v`: 12 PASS, no skips. Includes actual Tk selection, placement/undo, rotation retaining connections, cursor preview, zoom, and scope display from the educational transient solver.
- `python -m unittest discover -s tests -v`: 6 PASS.
- Real ngspice 42: `python scripts/verify_rc.py --output reports/rc.json` PASS, 511 samples, maximum waveform error 0.0000146819 V. Separate backend baseline; this GUI still uses its educational R/C MNA solver.
- Raw RC circuit, ngspice log, sampled data and validation report are committed under `docs/evidence/rc-ngspice42/`.
- Actual Tk window captures at the same 1360 × 850 client size: [before](evidence/workspace-before.png), [after](evidence/workspace-after.png). Linux font/theme rendering differs from native Windows.
- Initial environment attempts failed: package manager privilege drop, missing X server dependencies, and cross-process display connection. Dependencies were extracted locally and Xvfb/tests run in the same command network namespace; subsequent complete GUI run passed. No failures hidden as skipped GUI checks.

### Comparison and limits
Reference: NI Circuit Design Suite Getting Started Guide, page 3, https://download.ni.com/support/manuals/374482h.pdf. Layout comparison covers compact standard/component/simulation toolbars, left hierarchy, white worksheet, right instruments and bottom spreadsheet. It is an original approximation, not pixel parity or copied NI source/artwork.

Qt/Qucs-S compilation remains unverified in this environment; this revision does not change upstream. Native Windows interaction and packaging remain untested. No NI executable, reference measurement exports or real .ms14 fixture are available, so direct numerical parity and file interoperability remain blocked. Advanced instruments remain unavailable.

Next bounded task: run this exact revision on Windows and validate opening, component selection, wiring, save/reopen and scope rendering before producing an installer. Connecting this prototype to ngspice is a separate functional milestone.

## Functional engine/instrument integration — 2026-10-21

User asked for missing functionality and open-source reuse, beyond appearance. Research and functional coverage are documented in `docs/OPEN_SOURCE_AUDIT.md` (19 candidate projects/resources, with links, reuse decisions and explicit gaps). This is a targeted relevant-project survey, not an exhaustive internet search.

### Implemented milestone

- Restricted original adapter to separately installed ngspice, now invoked from the native UI. Old educational core remains for compatibility/testing, but Run no longer uses it.
- Transient / DC operating point / AC analysis with real vectors, original generic diode/LED electrical models, R/L/C, waveform voltage sources and static switches.
- Worker-thread execution, actual process cancellation, queued-success cancellation guard, stale-result rejection, bounded run time and restricted source syntax.
- Scope, generator, differential voltage/RMS/frequency meter, source current/power readings, Bode, threshold trace viewer, sampled voltage spectrum, CSV/raw/netlist/log export.
- `-n` disables spiceinit loading. Malformed source directives/nonfinite values/unsupported kinds fail explicitly.
- Full plan/spec in docs/superpowers. Existing Qucs-S pin and notices unchanged. No third-party source has been copied or vendored by this branch.

### Verification and review

Linux, Python 3.12, Tk9, ngspice42, real Xvfb display: prototype suite includes real solver regressions for RC/RL/DC/diode/switch/sine/AC cutoff, measurement numerical checks, parser/absent-engine/cancellation checks and native UI interactions. Root suite remains required. Python 3.10 grammar is explicitly parsed; native Python3.10/Windows runtime is not locally verified.

Independent review found a Python3.11 f-string grammar incompatibility (fixed), a queued-result cancellation race (fixed with regression test), and false low-frequency spectrum aliases from fixed 512-point reduction (reproduced with 700 Hz becoming 188 Hz, then fixed using automatic non-reducing radix-2 FFT; numerical regression now passes). Finite input sampling and interpolation still limit spectra; the panel states Nyquist/limits.

A repeat GUI invocation failed because stale display 94's lock prevented Xvfb startup; a fresh display is used for the final run. The initial failure is an environment/display failure, not recorded as a pass. See final command/count below.

Actual window captures and solver netlists/logs/tables/CSV: `docs/evidence/ngspice-instruments/`. Transient sample values use adaptive times, not array indices. No NI numerical parity, Qt binary compilation, Windows package or .ms14 interoperability is claimed.

Next bounded task: multi-pin/model schema and validated transistor/op-amp circuits; then structured DC/sweep/noise adapters. The audit records the other tool families, including digital/HDL and RF/network workflows, as missing rather than inheriting their capabilities from candidate repositories.

Final local command: `OCW_NGSPICE=/tmp/ocw-deps/usr/bin/ngspice LD_LIBRARY_PATH=/tmp/ocw-deps/usr/lib/x86_64-linux-gnu bash /tmp/ocw_instruments_final.sh` (starts Xvfb on a fresh TCP display, runs full prototype tests, captures actual instruments, then root tests and byte-compiles): **31 prototype + 6 root tests PASS**, no skips. Sine source evidence: 2 V peak, 1 kHz, measured total RMS 1.414216838 V and frequency 1000.0 Hz. Native Windows and NI binary references remain untested/unavailable. Spectrum provides an auto/explicit upper-frequency display bound; its full record remains preserved.

## Device library and DC sweep — 2026-10-22

- Previous PR #10 CI was inspected: native Python workflow and Desktop foundation both succeeded. The desktop job compiled Qucs-S and uploaded the Linux binary. This is remote Linux build evidence, not Windows/NI parity.
- Reused pinned Qucs-S source/model data, with GPL-2.0-or-later notices and full COPYING under prototype/workbench/data. scripts/import_qucs_devices.py reproduces the compressed catalog deterministically. Parameter order/exclusions derive from Michael Margraf's Basic_BJT/BJT code; descriptions retain model-contributor attribution; op-amp subcircuits retain upstream authors.
- Added 1,226 BJT models plus LM358/LM324/NE5532; three-/five-terminal schematic capture and model assignment; searchable family/model database; Models/BOM/Diagnostics panels; single-source DC sweep dialog and output-vector plot; tested example documents.
- Initial model import skipped femto values because the engineering-prefix parser lacked `f`; fixed with an explicit conversion regression. 18 unsupported source entries remain explicitly listed, not silently simulated.
- First op-amp run failed because the extracted runtime lacked initialized XSPICE polynomial code models. Restored complete ngspice runtime scripts/codemodel paths for testing. Normal installations must include their standard code-model files; failures remain explicit.
- Independent review fixed sweep axes accidentally reaching time-domain meter statistics, prohibited diode-connected BJT topology, and missing descriptive search terms for basic parts. No remaining important findings reported.
- Local Linux/Python3.12/Tk9/ngspice42: every adapted BJT operating-point smoke check passes; all three op-amp followers pass; source sweep has 51 points over 0–5 V. LM358 follower: input 0.2 V, output 0.1999530428 V. Full suite and snapshots are recorded under docs/evidence/device-library.
- A GUI interaction verifies model search, placement, five pins, model provenance, BOM content and sweep rejection by the meter. Pin rotation/save/load, diode-connected NPN/PNP and femto conversion have regressions.
- Public NI documentation and decoder source investigation are in docs/INTEROPERABILITY_RESEARCH.md. Container decoding is not claimed as circuit import.
- Remaining: MOS families, richer ICs/digital devices, hierarchical sheets, advanced analyses, Windows packaging and .ms14 mapping/NI roundtrip validation. Next bounded task is a four-terminal MOS model path with drain/gate/source/bulk mapping and I–V tests.

Final verification: `bash /tmp/verify_devices123.sh` with complete extracted ngspice42 runtime and real Xvfb on display123: **40 prototype tests + 6 root tests PASS, no skips**. One prototype test iterates every one of the 1,226 adapted BJT models. Native UI interactions and actual screenshots completed. Python3.10 grammar and byte-compilation pass. Verification transcript is committed in docs/evidence/device-library/verification.log. Windows and direct NI numerical comparison remain unverified.

## Reference typography, component selector and read-only inspection — 2026-10-22

Compared NI desktop documentation/screens with actual application captures; fixed unavailable Segoe UI fallback, themed tables and headings, neutral grid and title strips. Added component symbol/model details and cleared stale previews on empty searches. This remains an independent interface with substantial visual and functional differences; no exact-match claim.

Added bounded read-only container metadata inspection derived from the pinned ISC decoder. No native import or decompression. JSON export rejects original paths and hardlink aliases. Inspected the MIT multisim-mcp COM implementation: it requires the installed licensed Windows NI product and is not a portable simulator replacement. Details and remaining gaps are in INTEROPERABILITY_RESEARCH.md.

Final local command: `bash /tmp/verify_reference137.sh`, Linux Python3.12/Tk9/ngspice42 with fresh Xvfb display137: **46 prototype + 6 root tests PASS**, no skips; byte-compilation and actual GUI captures complete. Evidence: docs/evidence/reference-ui. Windows rendering, native file roundtrips and direct NI numerical/pixel comparison remain unverified. Next bounded task remains four-terminal MOS model support with real I–V tests.

Independent review found unbounded special/growing-file reads and excessive section allocation. Fixed with regular-file checks, bounded reads and a 4096-section cap; regressions pass.

Final GUI validation initially crashed twice with Tcl_AsyncDelete after repeated window disposal. Test teardown now explicitly collects destroyed Tk windows on their owning main thread before later solver workers can trigger cyclic collection. The full final run passes; the earlier crashed runs are not passes.

## Electronics II course and student-circuit validation — 2026-10-22

Scope: supplied 113-page Electronics II PDF, ten chapters. Read extracted text and reviewed page contact sheets; enlarged the exact numerical diagrams on PDF p25/42/110/113. COURSE_COVERAGE.md distinguishes terminal-level topology coverage, ideal arithmetic, limited generic models and individual exercises not reproduced. No course-completion or NI parity claim.

Implemented 87 editable course/student fixtures with explicit checks and analysis settings. Added JFET N/P, four-terminal MOS N/P and depletion models; pinned Qucs-S SCR/DIAC/TRIAC models; original limited MOS+PNP IGBT equivalent; selected real diode models; current sources, series zero-V current probe, potentiometer and persistent named net aliases. Catalog: 1240 adapted Qucs-S entries plus 11 explicitly original educational models. Rebuild is deterministic using both import scripts. Six selected model names absent from those upstream libraries are explicitly listed rather than fabricated. Full notices retained; TI TLC555 block was inspected but not copied under an assumed GPL permission.

UI: searchable experiment browser and Load/Load-and-Run; selected-analysis toolbar/F5; explicit AC input source; new families in palette/picker; pin order/provenance; named instrument nodes; scope A/B cursors and delta measurements; branch-current probe in meter; label spacing and worksheet height adjusted. Labelled modular fixtures are electrically editable but are not copies of the textbook diagram artwork. No screenshots are included in the user response.

Failures found during exploratory real-solver runs and corrected:
- AC excitation went to the first supply instead of signal input. Added explicit AC source and regression; full BJT/JFET frequency response now tests gain and attenuation.
- ngspice interpreted zero pulse width as its default pulse behavior, making the supposed triangle incorrect. Emit explicit nonzero width with preserved period; derivative fixture checks both polarities.
- Full bridge with ideal floating output had a singular common-mode transient. Fixtures now state 100-megohm leakage paths and source resistance; no global hidden gmin alteration.
- Early amplifier and integrator captures retained startup effects. Extended the measurement interval and used actual-time-based settled checks, not sample-index assumptions.
- Review caught a diode-connected PNP in the IGBT equivalent; corrected its collector/emitter topology and added a current-gain test (2.1 A under the stated synthetic parameters) that the erroneous series-diode equivalent cannot pass.
- Unknown diode model typo silently selected a generic diode. Now explicit Generic is allowed and unknown named models fail. Invalid saved net aliases reject before installation into the UI. Tests cover both.
- Attached aliases follow pin motion/rotation; model numbering is unchanged through persistence. Net labels are excluded from physical BOM/isolated-pin counts.

Final local verification: `bash /tmp/verify_course151.sh`, fresh Xvfb TCP display151, Python3.12/Tk9/ngspice42: **56 prototype + 6 root tests PASS, no skips**, byte-compilation succeeds. The prototype solver test iterates all 87 course fixtures; existing test still iterates all 1226 BJT models. Additional selected FET/diode catalog smoke tests pass. Python3.10 grammar check passes; native Python3.10/Windows runtime untested. Native GUI interaction checklist under evidence includes experiment load/run, matched analysis, AC/Bode, DC sweep, meter/probe, semantic node names, actual scope cursor deltas, picker and experiment-result checks. Independent review reports no remaining material correctness findings; review-agent solver tests were skipped because its environment did not have ngspice, so only the root's explicit complete-runtime runs are counted as solver evidence.

`python scripts/verify_course.py --output /tmp/course-final-evidence` with the same complete extracted runtime: **87/87 PASS**. Exact generated decks, solver logs and measurement bounds/results are committed compactly under docs/evidence/electronics-course. Full raw CSV/tables are reproducible with `--raw`; compact committed evidence does not claim to contain those full tables. Source PDF digest is recorded without redistributing the user's file.

Example results: p110 integrator slope −5341.514 V/s versus ideal −5319.149 V/s and settled swing 2.708 Vpp; p113 idealized differentiator −4.4/+4.4 V. p25 finite-beta bias VCE=2.45778 V differs from textbook's stiff-divider/0.7 V approximation 1.95 V and is explicitly reported as such.

Remaining: not every numerical/related exercise or manual graphical construction is reproduced; exact manufacturer models for selected absent names; full temperature/noise/tolerance/thyristor-quadrant validation; realistic IGBT switching; 555/digital/HDL/MCU/ADC/DAC/transformer/relay families; NI trigger/timebase controls, hierarchy, Windows packaging and .ms14 conversion. No NI executable/reference data is available. Native Qt added-control integration is unverified; this milestone exercises the independent Python workbench. Next bounded task: complete the individual textbook numerical-example ledger and add selected exact manufacturer models, then a separately licensed 555/digital path with timing regressions.

CI caught Python3.11 rejecting a reused quote inside the new course-UI f-string, although local Python3.12 and its feature_version grammar flag accepted it. Moved page formatting outside the f-string. The earlier grammar-only check is insufficient to certify an older interpreter; actual Python3.11 CI is required before merge.
