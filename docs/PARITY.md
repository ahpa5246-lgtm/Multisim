# Multisim parity ledger

Status is evidence based. Upstream capabilities are not automatically locally verified.

| Workflow | Foundation | Evidence / remaining gate |
|---|---|---|
| Desktop schematic editor | Upstream supplied, unverified here | Linux compilation and visually inspected X11 startup PASS in run 39089285681; interaction unverified |
| Component placement/wires/save/load | Upstream supplied, unverified here | Linux GUI Save As and reparse/export of saved RC PASS in run 39126560602; fresh-process GUI reopening visually verified in run 39144396633; placement and wiring still unverified |
| RC transient | Test harness implemented | Real exported-device charging baseline PASS; GUI F2 dataset contract PASS in run 39171580577 for DC-initialized 5V only; no NI comparison |
| Oscilloscope / multimeter UX | Not implemented locally | Connect probes to real vectors; test units/scales |
| Function generator / logic analyzer | Not implemented locally | Signal and timing validation required |
| .ms14 import | Blocked | Genuine fixture and decoded schema mapping absent |
| .ms14 export | Not implemented | NI acceptance and roundtrip test required |
| Windows native build/export | Verified in MSYS2 | Run 39096265664; GUI and standalone runtime unverified |
| Windows installer | Not implemented | Runtime/backend bundling and clean-machine install required |
| NI numerical comparison | Blocked | NI binary/reference exports absent |

## Comparison protocol
Record NI version, upstream SHA, ngspice version, circuit/model files, supply values, initial conditions, step sizes and tolerances. Save both raw outputs. Compare node voltage, frequency, phase and instrument readings. An analytic pass may expose errors but cannot replace the NI reference.
