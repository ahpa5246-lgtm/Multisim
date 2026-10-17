# Engineering rules

Build a real desktop circuit workbench based on pinned Qucs-S + ngspice. Preserve working upstream features and copyright notices. Never substitute decorative controls for simulation.

- Read docs/DESIGN.md, docs/PLAN.md, docs/PARITY.md and docs/REVIEW.md first.
- Work on one measurable milestone per branch. Run unit tests and actual solver checks; GUI changes require a compiled binary and visual interaction evidence.
- Compare behavior with documented NI Multisim workflows. Mark each result as implemented, verified, partial, blocked, or untested; screenshots alone do not prove numerical correctness.
- Never claim Multisim parity from analytic tests alone. Reference measurements need version, circuit, models, solver tolerances, and raw output.
- Missing Qt, ngspice, Windows, or a real .ms14 fixture is a recorded blocker, never a pass.
- Do not fabricate .ms14 parsing, silently drop unsupported components, or overwrite imported originals.
- Do not merge competing copyleft source without reviewing the exact licenses.
- Keep upstream pinned; update only with fresh build and regression evidence.
- Record changes, failures, commands and the next bounded task in docs/REVIEW.md.
- Do not promise continuous execution. Scheduled runs are bounded and subject to available tools and quota.
