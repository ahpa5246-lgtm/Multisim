# Multisim interoperability investigation — 2026-10-22

The objective is reproducible electrical behavior and familiar workflows. This investigation examines public NI documentation, existing open-source implementations and reusable models. It does not claim complete Multisim reconstruction.

## Documented routes

- [NI component creation](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YH5fCAG): match symbol terminals, model pin order and electrical model. Implemented here for BJT C/B/E and op-amp +/−/VCC/VEE/OUT, not physical package numbering.
- [NI discrete MOS model import](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z000000fzgoSAA): the next device-family extension needs explicit model type and terminal mappings, rather than renaming another component.
- [NI DC sweep](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YH7vCAG): compare source values and output vectors. This branch adds single-source voltage sweeps and current/voltage plots.
- [NI SPICE netlist import](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YG0ACAW): use exported SPICE as the first exchange/reference route, before attempting native project roundtrip.
- [NI component transfer](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YHyaCAG): component-database transfer is a separate workflow from circuit-file conversion. Do not assume a decoded database is a freely redistributable component library.

## Existing decoder source inspected

[cinderblock/electronics-workbench-decoder](https://github.com/cinderblock/electronics-workbench-decoder), commit `cb9c13bc6131488bf0c6ac15505d54b4a7e3aa2a`, package 0.2.0, ISC, copyright Cameron Tacklind 2021–2026. Read package.json, LICENSE, src/formats.ts and src/decode.ts. It uses node-pkware for compressed XML and mdb-reader for database extraction. The later reference-UI milestone adapts its header registry and section layout for read-only metadata inspection, with its ISC notice. No decompressor or XML circuit mapper is included.

The source distinguishes compressed circuit/project XML containers from Jet component databases. This supplies a possible container layer, but not our document/pin/connectivity mapping. Header detection, decompression length checks, version-specific XML entities, embedded models, unsupported entities, encoding and original-file preservation all need tests before an import command is exposed.

Next interoperability acceptance requires legally supplied representative circuits, decoded XML preservation, explicit unsupported-entity reports, pin/net mapping comparison against exported SPICE, and NI-side open/save validation. A blank synthetic container is insufficient. There is no native .ms14 import/export in this release.

## Reuse delivered in this milestone

The pinned Qucs-S source is used directly: Transistors.lib and BJT_Extended.lib model values, Basic_BJT property order, BJT::spice_netlist exclusion logic, and three SpiceOpamp.lib subcircuits. The adapter and full license/provenance are shipped. 1,229 entries are available; 18 unsupported input entries are explicitly recorded in the generated catalog's skipped list. No count is fabricated by listing unimplemented devices as usable.

The 1,226 BJT entries each receive an ngspice operating-point smoke check. Three op-amps receive a closed-loop follower test. These establish loading/fixture behavior; comprehensive manufacturer-characteristic, transient, thermal, noise and NI-equivalence validation remain separate.

## Reference UI and automation investigation — 2026-10-22

Compared the actual rendered Linux application against NI’s [Multisim getting-started manual](https://download.ni.com/support/manuals/374482h.pdf) and [schematic-capture toolbar reference](https://forums.ni.com/t5/NI-Circuit-Design-Community-Blog/Multisim-Basics-Course-Two-Tips-for-Schematic-Capture/ba-p/3482056). The reference is the classic desktop interface, not Multisim Live. This is a structural comparison, not a pixel-difference or complete parity certification.

| Reference area | Change | Remaining difference |
| --- | --- | --- |
| Desktop typography | Installed sans-serif fallback; Windows Vista theme when available | Linux Tk rendering differs from Windows controls |
| Component selection | Database selector, family/model columns, symbol and pin/model detail panes | No NI database or footprint/package database |
| Workspace | Neutral grid, pale title strips, flat table headings and selection colors | Original icons, docking, menus and dialogs remain different |
| File investigation | Tools → Inspect EW/Multisim Container, SHA-256, header/section metadata, separate JSON report | No decompression, native circuit mapping or NI roundtrip |

Cloned and inspected [yxy050208/multisim-mcp](https://github.com/yxy050208/multisim-mcp) at `34b6f5bb449557a3993ba09c93b183bc2f829b09`, MIT. Its `multisim_client.py` imports pywin32, activates the registered Multisim COM server with EnsureDispatch/dynamic Dispatch, and requires a licensed installed Multisim; it also references electronics-workbench-decoder@0.2.0. Those automation functions cannot make this Linux application equivalent to NI. No code from that project is included.

The inspector adapts electronics-workbench-decoder's header/length layout at the pinned ISC revision above. Synthetic tests verify metadata and malformed bounds, not valid native-file decoding. Inspected source bytes are preserved; saving to the original or a hardlink alias is rejected. Supplied real files and NI-side comparison remain necessary before any editable native import can be advertised.
