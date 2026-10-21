# Ngspice-backed instruments

Intent: owner requests actual Multisim-like capabilities and broad reuse, beyond the interface revision. Preserve the existing native UI and pinned Qucs-S source. Work on one measurable branch: integrate ngspice and instruments which consume its results. A complete Multisim clone is not an acceptance claim.

Architecture: an original Python subprocess adapter invokes an independently installed ngspice (no copied third-party source, no shell command construction). Structured analysis settings generate a restricted netlist. A result object retains sampled vectors, netlist and logs for export. UI work runs off the Tk thread and Stop terminates the process. Solver absence or unsupported devices fail visibly, never silently use the educational solver.

Supported capture boundary: existing R/C/L/V/GND, generic diode/LED electrical models, static open/closed switch. Sources accept numeric DC or a validated SIN/PULSE expression only. Reject nonfinite values, bad bounds, arbitrary directives and malformed models. Existing JSON files stay readable. No untrusted arbitrary model scripts or .ms14 conversion.

Tools: transient oscilloscope from real sampled times; DC operating point; AC sweep/Bode transfer ratio with selectable input/output nodes; differential-voltage meter (DC, total RMS, AC RMS); function generator edits a real source; threshold-based logic trace viewer (not digital gate simulation); CSV and evidence export. Spectrum uses uniformly interpolated transient samples (automatic radix-2 length at least the original count; no forced reduction to 512) and a Hann-windowed FFT with amplitude scaling, labelled as sampled voltage spectrum, not calibrated power spectral density. Preserve unavailable instrument labels for unsupported workflows.

Acceptance: actual ngspice regressions for RC charge, RL transient, diode clipping, static switch states, sine generator, DC divider, AC RC cutoff; malformed source/injection, missing executable, process failure and cancellation checks. GUI interactions under Xvfb; screenshot evidence. Root tests remain green. Windows and NI parity remain unverified without native references.
