# Multisim interoperability investigation — 2026-10-22

The objective is reproducible electrical behavior and familiar workflows. This investigation examines public NI documentation, existing open-source implementations and reusable models. It does not claim complete Multisim reconstruction.

## Documented routes

- [NI component creation](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YH5fCAG): match symbol terminals, model pin order and electrical model. Implemented here for BJT C/B/E and op-amp +/−/VCC/VEE/OUT, not physical package numbering.
- [NI discrete MOS model import](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z000000fzgoSAA): the next device-family extension needs explicit model type and terminal mappings, rather than renaming another component.
- [NI DC sweep](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YH7vCAG): compare source values and output vectors. This branch adds single-source voltage sweeps and current/voltage plots.
- [NI SPICE netlist import](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YG0ACAW): use exported SPICE as the first exchange/reference route, before attempting native project roundtrip.
- [NI component transfer](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YHyaCAG): component-database transfer is a separate workflow from circuit-file conversion. Do not assume a decoded database is a freely redistributable component library.

## Existing decoder source inspected

[cinderblock/electronics-workbench-decoder](https://github.com/cinderblock/electronics-workbench-decoder), commit `cb9c13bc6131488bf0c6ac15505d54b4a7e3aa2a`, package 0.2.0, ISC, copyright Cameron Tacklind 2021–2026. Read package.json, LICENSE, src/formats.ts and src/decode.ts. It uses node-pkware for compressed XML and mdb-reader for database extraction. No decoder source is copied into this branch.

The source distinguishes compressed circuit/project XML containers from Jet component databases. This supplies a possible container layer, but not our document/pin/connectivity mapping. Header detection, decompression length checks, version-specific XML entities, embedded models, unsupported entities, encoding and original-file preservation all need tests before an import command is exposed.

Next interoperability acceptance requires legally supplied representative circuits, decoded XML preservation, explicit unsupported-entity reports, pin/net mapping comparison against exported SPICE, and NI-side open/save validation. A blank synthetic container is insufficient. There is no native .ms14 import/export in this release.

## Reuse delivered in this milestone

The pinned Qucs-S source is used directly: Transistors.lib and BJT_Extended.lib model values, Basic_BJT property order, BJT::spice_netlist exclusion logic, and three SpiceOpamp.lib subcircuits. The adapter and full license/provenance are shipped. 1,229 entries are available; 18 unsupported input entries are explicitly recorded in the generated catalog's skipped list. No count is fabricated by listing unimplemented devices as usable.

The 1,226 BJT entries each receive an ngspice operating-point smoke check. Three op-amps receive a closed-loop follower test. These establish loading/fixture behavior; comprehensive manufacturer-characteristic, transient, thermal, noise and NI-equivalence validation remain separate.
