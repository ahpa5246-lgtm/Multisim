# Qucs-S derived device data

Source: https://github.com/ra3xdh/qucs_s at 46e47e8fabe852a9d6aab41d8a612ff5a78370c1.
GPL-2.0-or-later; full license in COPYING.qucs-s. The full corresponding original
source is pinned under upstream/qucs-s. Rebuild with scripts/import_qucs_devices.py.

qucs-devices.json adapts library/Transistors.lib, BJT_Extended.lib and selected
SpiceOpamp.lib entries. Model descriptions retain contributor attributions.
Basic_BJT parameter order and BJT::spice_netlist exclusions are adapted from
qucs/components/bjtsub.cpp and bjt.cpp, Michael Margraf (C) 2003–2004,
GPL-2.0-or-later. Op-amp subcircuits are copied verbatim from SpiceOpamp.lib;
authors Vadim Kuznetsov and Timofey Moiseev as recorded in that library.

These are upstream library models, not a guarantee of manufacturer accuracy,
package pin numbering or suitability for a particular purchased device.
Our symbols use electrical pin order C/B/E for BJT and +/−/VCC/VEE/OUT for op-amps.

## Electronics Workbench container metadata

interop.py adapts the format headers and section layout from
https://github.com/cinderblock/electronics-workbench-decoder at
cb9c13bc6131488bf0c6ac15505d54b4a7e3aa2a. Cameron Tacklind (C) 2021–2026,
ISC; full notice in COPYING.ew-decoder. No decompressor or XML mapper is shipped.
