# Desktop foundation design

Owner intent: a free desktop alternative with Multisim-like circuit capture, real simulation, instruments and eventual file compatibility. Reuse substantial open-source software; avoid a single-page mockup.

## Selected approach
Use the existing Qucs-S Qt6 editor and ngspice backend. Pin upstream as a submodule, preserving attribution and keeping local work reviewable. A rewrite discards a mature editor; mixing several GUI codebases incurs incompatible architecture and license risk. Neither is needed for the foundation.

## First acceptance boundary
Clone recursively, compile/install the upstream desktop program, and test an RC transient independently using ngspice. A 5 V source charges a 1 uF capacitor through 1 kohm: tau=1 ms; V(tau)=3.160602794 V. Absolute sample error must stay below 20 mV. Missing solvers fail explicitly.

## Next stages
1. Compile and interactively verify on Windows; package with backend and corresponding source notices.
2. Add original instrument panels incrementally, connected to actual simulation data.
3. Study EW decoder separately; require a genuine legally supplied .ms14 fixture before mapping connectivity. Never claim XML extraction is circuit conversion.
4. Compare RC, op-amp, 555 and logic measurements against an identified Multisim version under equivalent models/settings.

## Limits
No NI executable is available here, so direct parity measurements remain blocked. No .ms14 fixture was supplied. Preserve the existing Qucs-S UI until interaction tests can support redesign. Linux compilation does not establish Windows usability.
