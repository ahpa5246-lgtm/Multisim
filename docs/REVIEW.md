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
