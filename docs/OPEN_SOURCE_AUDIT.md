# Functional parity and open-source integration audit — 2026-10-21

This is a targeted search of relevant projects, documentation and source structures, not a claim to have examined every repository on the internet. Public project descriptions establish candidate capabilities; only the integration tests establish what this workbench actually implements. No candidate's whole feature list is inherited merely by listing it here.

## Benchmark and coverage

Reference: [NI's edition comparison](https://www.ni.com/en/shop/electronic-test-instrumentation/application-software-for-electronic-test-and-instrumentation-category/what-is-multisim/multisim-designers/select-edition/ni-multisim-simulation-driven-instruments-and-analyses-feature-c.html), updated January 30, 2026. Target scope is the desktop professional toolset; hardware-driver instruments and proprietary device emulations need separate validation. The mapping below also includes capture/library/interoperability work beyond the instrument list.

| Capability family | This branch | Remaining integration / acceptance gate |
|---|---|---|
| Two-channel scope | Implemented from real transient data | Physical pin-based instrument placement, triggering, timebase/volts-per-division, cursors |
| Four-channel scope | Missing | Add four selectable differential pairs; validate channel scaling |
| Voltage measurement, multimeter, measurement probe | Partial | Selectable differential DC/total RMS/AC RMS; no resistance test-source mode or physical probe placement |
| Ammeter, current probe | Partial | Source-branch currents only; arbitrary branch sensors require netlist insertion and topology tests |
| Wattmeter | Partial | Delivered mean power for a selected source; arbitrary load power requires branch-current capture |
| Frequency counter | Partial | Rising crossings about mean on captured transient; no triggering/hysteresis/gating controls |
| Function generator | Implemented subset | DC, sine, square, triangle applied to V source; no arbitrary waveform editor |
| Bode plotter | Implemented subset | Gain/phase of selectable output/input nodes, first source excited; no impedance/network port fixture |
| Spectrum analysis | Partial | Hann-windowed sampled-voltage amplitudes; no calibrated power-density/impedance mode |
| Logic analysis | Partial | Analog threshold trace only, no event-driven digital simulation or protocol decoder |
| Logic conversion, word generation | Missing | Digital/HDL backend plus truth-table/sequence adapters |
| Distortion measurement | Missing | Settling-window choice, coherent harmonic extraction and THD regression |
| Semiconductor I–V curve tool | Missing | Structured DC sweep and device/model selection; not just plotting an arbitrary vector |
| RF/network analysis | Missing | Port reference planes, impedances, S-parameter fixtures; use Qucsator/scikit-rf candidates |
| ELVIS-style arbitrary source / reader / writer / meter / dynamic analyzer / generator / scope / supply | Missing | Hardware driver/API and device testing are distinct from a simulated front panel |
| Agilent-style source / meter / scope, Tektronix-style scope | Missing | Reproduce documented operation with original UI; no vendor firmware/assets copied |
| Transient, DC operating point, AC sweep | Implemented subset | Exposed from GUI, tested with ngspice; zero-state transient startup, no selectable initial-state method yet |
| Single-frequency AC, DC sweep | Missing in GUI | ngspice backend can support these; add validated settings and parser fixtures |
| Fourier, noise, sensitivity, pole-zero, transfer-function analyses | Missing in GUI | Separate analysis adapters, units and reference circuits; a solver capability is not an implemented UI feature |
| Temperature / parameter / nested sweeps | Missing | Structured experiment runner with bounded jobs and result dimensions |
| Monte Carlo, worst-case, batched analyses | Missing | Seeded tolerance model, sample distributions, cancellation and statistical acceptance |
| Distortion / noise figure | Missing | Device models and numerical/port conventions need dedicated validation |
| Trace-width calculation | Missing | Board stackup/current/temperature assumptions and reference-standard validation |
| User-defined analyses | Missing | Explicit trusted-script workspace separated from restricted schematic value fields |
| Component/model database | Eight existing symbol kinds only | More pin geometries, model registry, units, provenance and redistribution licenses |
| BJT/MOSFET/op-amp/555/logic ICs | Missing in native capture | ngspice may model devices, but symbols, pins, models and tests are still required here |
| PCB layout / footprints / BOM | Missing | KiCad-based exchange workflow; electrical models are not footprint libraries |
| Subcircuits, buses, hierarchical sheets, ERC | Missing | Document-schema and netlisting milestone; preserve old JSON imports |
| .ms14 roundtrip | Blocked | Genuine fixture/schema and NI-side roundtrip validation; none fabricated |
| Windows packaging | Untested | Native solver path selection is provided; installation and clean-machine test still required |

## Candidate search and integration decisions

License labels below describe the linked project or repository listing, not an assertion that every nested model/library shares that license. Exact pinned-file license review is required before copying source. This branch copies **none** of these projects' source code; it invokes the separately installed ngspice executable and preserves the existing pinned Qucs-S tree.

| Resource inspected | Useful contribution | Integration decision |
|---|---|---|
| [ngspice](https://ngspice.sourceforge.io/docs.html), [license tree](https://github.com/ngspice/ngspice/blob/master/COPYING) | Nonlinear analog/mixed-signal engine and extensive analyses; BSD-derived licenses with component notices | **Integrated now via process adapter.** Tested with ngspice 42. Not bundled; retain notices/source if packaging later |
| [Qucs-S](https://github.com/ra3xdh/qucs_s) | Mature editor, device libraries, plots, several solver backends; GPL-2.0 family | Existing pinned editor preserved. Its full UI is separate; native prototype does not inherit it automatically |
| [KiCad SPICE](https://www.kicad.org/discover/spice/) | Model assignment, schematic-to-ngspice architecture | Reference for model registry and future PCB exchange. Do not copy its complete C++ editor into Tk |
| [KiCad symbols](https://gitlab.com/kicad/libraries/kicad-symbols) | Symbol geometry and pin metadata | Candidate importer; symbols do not guarantee working SPICE models. Review current library license/exception at pinned revision |
| [eSim](https://github.com/FOSSEE/eSim) | KiCad/ngspice/GHDL integration; GPLv3 | Strong reference for adapters and HDL workflow; no source merged |
| [CircuitJS1](https://github.com/sharpie7/circuitjs1) | Interactive small circuits and educational examples; GPL family | Different runtime and numerical conventions. Use explicit exchange/reference cases, not silent replacement of SPICE |
| [SimulIDE](https://github.com/SimulIDE/SimulIDE), [project site](https://simulide.com/p/) | MCU and real-time circuit simulation | Repository/site license labels differ (GPL3 vs AGPL3); pin exact project/version before reuse. Candidate independent MCU bridge |
| [Digital](https://github.com/hneemann/Digital) | Logic designer/simulator and remote control; GPL3 | Candidate truth tables, digital gates and word-sequence workflow. Requires mapping and timing semantics |
| [Icarus Verilog](https://github.com/steveicarus/iverilog) | Verilog execution; GPL2 family | Candidate subprocess HDL backend and VCD output, not connected yet |
| [Verilator](https://github.com/verilator/verilator) | SystemVerilog simulation/lint | Candidate larger digital models; generated C++ build/runtime required. Exact license exceptions need pinned review |
| [GHDL](https://github.com/ghdl/ghdl) | VHDL simulation | Candidate VHDL backend, already a precedent in Qucs-S/eSim; no adapter yet |
| [PulseView](https://github.com/sigrokproject/pulseview) | Logic/scope GUI design and acquisition workflow | Candidate external capture viewer; native waveform data adapter needed |
| [libsigrokdecode](https://github.com/sigrokproject/libsigrokdecode) | Protocol decoder API and Python decoder ecosystem; GPL3+ | Candidate after digital channels/VCD exist. Decoding is separate from simulation |
| [scikit-rf](https://github.com/scikit-rf/scikit-rf) | RF networks, measurement and Touchstone data; BSD3 | Candidate network-analyzer math and calibration. Need proper port fixtures, not voltage ratios relabelled as S-parameters |
| [Xyce](https://github.com/Xyce/Xyce) | Alternative large-circuit analog engine; GPL3+ | Candidate second backend for independent regression; install/build burden deferred |
| [Qucsator](https://github.com/Qucs/qucsator) | Qucs circuit engine | Candidate RF workflows; netlist format and analysis conventions differ from ngspice |
| [OpenVAF](https://github.com/pascalkuthe/OpenVAF) | Verilog-A compiler/OSDI models; GPL3 | Candidate advanced device models. Individual integration-test model licenses vary; no bulk copying |
| [PySpice](https://github.com/PySpice-org/PySpice) | Python interface to ngspice/Xyce | Considered wrapper approach. Original small subprocess boundary selected to avoid shared-library deployment and extra Python dependency; no source copied |
| [SpiceSharp](https://github.com/SpiceSharp/SpiceSharp) | C# SPICE engine; MIT | Considered portable alternative, but adds .NET and another validation surface. Not integrated |

## Order of further work

1. Expand component/pin/model schema with BJT/MOS/op-amp and manufacturer-model provenance; validate DC/AC/transient fixtures.
2. Add DC/noise/sweep/Monte Carlo adapters and advanced scope controls on the same result format.
3. Introduce digital/HDL schema and timing tests before treating thresholded analog traces as a logic simulator.
4. Add RF/network ports and scikit-rf/Touchstone support.
5. Validate Windows distribution and NI reference circuits, then investigate real .ms14 fixtures.

These are concrete gaps, not claims of completed or automatically scheduled future work.
