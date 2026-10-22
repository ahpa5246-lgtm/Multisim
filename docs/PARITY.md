# Multisim parity ledger

Status is evidence based. Upstream capabilities are not automatically locally verified.

| Workflow | Foundation | Evidence / remaining gate |
|---|---|---|
| Desktop schematic editor | Upstream supplied, unverified here | Qt compilation and interaction required |
| Component placement/wires/save/load | Upstream supplied, unverified here | Place RC, reconnect wire, save/reload, inspect netlist |
| RC transient | Test harness implemented | Requires real ngspice run; analytic baseline only |
| Oscilloscope / multimeter UX | Not implemented locally | Connect probes to real vectors; test units/scales |
| Function generator / logic analyzer | Not implemented locally | Signal and timing validation required |
| .ms14 import | Blocked | Genuine fixture and decoded schema mapping absent |
| .ms14 export | Not implemented | NI acceptance and roundtrip test required |
| Windows installer | Not implemented | Native Windows build and clean-machine install |
| NI numerical comparison | Blocked | NI binary/reference exports absent |

## Comparison protocol
Record NI version, upstream SHA, ngspice version, circuit/model files, supply values, initial conditions, step sizes and tolerances. Save both raw outputs. Compare node voltage, frequency, phase and instrument readings. An analytic pass may expose errors but cannot replace the NI reference.

## Independent Python UI milestone — 2026-10-21

| Workflow | Status | Evidence |
|---|---|---|
| Compact Multisim-inspired workspace layout | Implemented; visually reviewed on Linux | Before/after captures in `docs/evidence`; no pixel parity claimed |
| Component spreadsheet / in-use selection | Verified on Linux | Native Tk interaction tests |
| Placement cursor preview, undo, rotation, zoom | Verified on Linux | Native Tk interaction tests |
| Prototype scope from educational transient solver | Verified for startup RC | Native Tk test; does not use ngspice |
| Separate ngspice RC baseline | Verified | ngspice 42 raw data/log/report in `docs/evidence/rc-ngspice42` |
| Windows rendering / installer | Untested | Linux cannot establish Windows validation |
| Qucs-S GUI build | Untested locally | Upstream preserved; no build claimed |

## Current superseding status — ngspice integration

The Python UI now uses real ngspice for its Run/DC/AC actions. Its earlier educational-only solver status above is historical. Scope/generator/meter/Bode/spectrum/threshold traces are **partial implementations**, with exact limits in `docs/OPEN_SOURCE_AUDIT.md`. R/L/C transients, generic diode, static switch, DC divider, sine source and RC AC cutoff are verified on Linux. Full digital, RF, semiconductor database, arbitrary probe insertion, Windows and .ms14 parity remain missing/untested/blocked as specified there.

## Device-library milestone — 2026-10-22

1,229 adapted Qucs-S library entries: 1,226 BJT models solver-smoke-checked, three op-amp models follower-tested. Three-/five-pin native capture, selection, placement and persistence are implemented. Models/BOM/basic connectivity diagnostics and single-source DC sweeps are implemented. This does not establish manufacturer-characteristic or full Multisim parity. Source/license and 18 skipped input entries are preserved in the generated catalog and notices; interoperability research is separate.
