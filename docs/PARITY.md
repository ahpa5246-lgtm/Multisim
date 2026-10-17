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
