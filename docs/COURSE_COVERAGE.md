# Electronics II course validation

The supplied 113-page course was read as text and visually reviewed in page contact sheets. Diagrams on PDF pages 25, 42, 110 and 113 were additionally inspected at full size. Page references below are **PDF** pages; printed lecture pages are two lower. The private course PDF is not redistributed in this repository; its digest is recorded in evidence/source.json.

This is topology and model-specific numerical validation, not a claim that every worked example, related problem, physical diagram or idealized numerical answer has been reproduced. All ten chapters have executable coverage. Three fixtures directly reproduce numerical component/source values from the PDF; others use explicitly stated representative values. No result is a direct NI Multisim comparison.

## Course crosswalk

| PDF pages | Material / circuit family | Executable fixtures | Status / limit |
|---|---|---|---|
| 1–2 | Cover, contents, textbook references | No electrical experiment | Reviewed |
| 3–8 | Structure, NPN/PNP operation, alpha/beta and currents | NPN/PNP active/cutoff/saturation | Electrical terminal behavior tested; semiconductor cross-sections and arithmetic-only examples are not simulated experiments |
| 9–15 | CE configuration, input/output characteristics, DC load line | bjt-characteristics; bjt-output-20/40/60; active/cutoff/saturation | One family of collector curves at three base currents; not an interactive two-source curve tracer |
| 16–19 | CB configuration / bias example; CC mentioned in configuration overview | common-base; emitter-follower | DC topology/model checks; no reference exports from NI |
| 20–22 | Q point and load-line family | bjt-output-*; voltage-divider-bias | Model-specific curves; graph annotations / graphical homework construction remain manual |
| 23–25 | Voltage-divider bias | voltage-divider-bias; pdf-p25-bias | p25 exact supply/resistors, finite-beta model differs from ideal VBE=0.7 V/no-base-loading calculation |
| 26–28 | Emitter bias / beta stability | emitter-bias | DC verified; no temperature/Monte Carlo stability sweep |
| 28–30 | Collector feedback | collector-feedback | DC verified; not every beta/temperature substitution |
| 31–36 | JFET symbols, drain/transfer curves, pinch-off | njf/pjf-transfer; jfet-output-0/-1/-2 | Electrical models verified; breakdown/destruction and device geometry are not validated |
| 37–39 | N/P-channel self-bias, transfer/load-line construction | njf/pjf-self-bias | Bias verified; manual graph construction not automated |
| 40–43 | Divider and BJT current-source bias | jfet-divider; jfet-current-source; 2N4341 catalog smoke check | Representative circuit values. p42 assumes a particular device's VD=7.5 V; that does not uniquely specify its model parameters, so no forced match is asserted |
| 44–50 | Enhancement/depletion MOSFET construction and transfer | nmos/pmos-transfer; depletion-nmos/pmos | Four terminals D/G/S/B; bulk explicit; generic textbook models distinguished from catalog devices |
| 51–54 | MOS divider, drain feedback and zero bias | nmos/pmos-divider/feedback; depletion-* | DC verified; not each numeric worksheet variant |
| 54–55 | IGBT equivalent / gate control | igbt-0, igbt-10, igbt-current-gain | Explicitly limited original MOS+PNP equivalent. No real IGBT switching tail, rating, thermal or breakdown validation |
| 56–61 | Coupling/bypass effects, dB, critical frequency | npn/njf-frequency/amplifier; RC equivalents | Full BJT/JFET circuits plus analytic attenuation checks. Arithmetic-only dB conversion examples are not separate circuits |
| 62–68 | Input/output/bypass low-frequency equivalents | input-coupling; output-coupling; bypass-equivalent | Isolated RC response checks plus full amplifier cases |
| 69–75 | Internal capacitance / Miller high-frequency equivalents | miller-input/output; npn/njf-frequency | High-frequency attenuation tested. Specific textbook parasitic values and every Miller arithmetic example are not independently recreated |
| 76–79 | SCR equivalent, trigger, latch, interruption | scr; scr-commutation | Upstream regenerative model; pre-trigger, latched, interrupted/recovered states checked. Mechanical switch interaction and parallel-short commutation are not separately validated |
| 80–81 | Half-wave power control / firing angle | scr-half-wave | AC circuit runs with adjustable POT; not a calibrated full 0–180-degree firing-angle instrument |
| 82–83 | DIAC bidirectional breakover | diac-1/-1 | Upstream DB3 model, both polarities tested; not a four-quadrant characterization |
| 84–85 | TRIAC operation / equivalent | triac; triac-reverse | Both supply/gate polarities tested; no complete quadrant/temperature characterization |
| 86–90 | Op-amp characteristics / negative feedback | voltage-follower; noninverting; inverting | Powered LM358 model. Infinite bandwidth/zero offset are not attributed to a real device |
| 91–95 | Closed-loop noninverting/inverting gain | noninverting; inverting | Numeric gain/voltage checks |
| 96–100 | Zero/nonzero detection; interference | comparator-0/1/-1/divider/zener/interference | Real LM358 used as course op-amp comparator. Interference is deterministic two-sine injection, not stochastic noise analysis or dedicated comparator timing |
| 101–105 | Sum, weighted sum, averaging | summing; summing-gain; averaging; scaling | Explicit resistor-weight and output checks; generalized arbitrary-input formula is not every numeric exercise |
| 106–110 | Ideal-topology/practical integrators | integrator-false/true; pdf-p110-integrator | Exact p110 values: 10k/200k/47nF, ±2.5 V, 1 kHz. Slope and settled amplitude checked with real LM358 |
| 111–113 | Ideal-topology/practical differentiators | differentiator-false/true; pdf-p113-differentiator | Exact p113 values with **idealized** amplifier reproduce ±4.4 V. Separate slower practical LM358 fixture; real LM358 is not asserted to meet 100 kHz ideal slew demands |

## Additional student circuits and sources

87 runnable cases total, exposed under Tools → Course Experiments and the toolbar Experiments button. Added Ohm's law, independent current source, potentiometer, series ammeter/current probe, diode half-wave/full bridge/filtered bridge, positive/negative clipping and clamping, generic zener regulation, LED current, RC charging, RL current rise and RLC resonance.

Primary teaching references inspected:

- [NI Multisim user guide](https://download.ni.com/support/manuals/374483a.pdf): desktop component selection, instruments and circuit-analysis workflow. This is a historical manual, not proof of current feature parity.
- [NI introductory amplifier workflow](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YH7MCAW&l=en-US).
- NI teaching resource search records for [electronics labs](https://education.ni.com/teach/resources/594/teaching-electronics-in-technical-and-vocational-colleges), [microelectronics](https://education.ni.com/teach/resources/574/problems-and-explorations-in-microelectronics-with-ni-mydaq-and-multisim?locale=en_US) and [power electronics](https://education.ni.com/teach/resources/774/power-electronics-fundamentals). Their indexed descriptions identify rectifier, bias, LED and regulator families; direct opens of the first two redirected to NI's general academic page during this session. No hidden downloadable curriculum was claimed as read or copied.

The pinned Qucs-S JFET/MOSFET/diode/thyristor source was adapted with notices. Selected model names not present in those source libraries remain listed in `course_unavailable_models` rather than invented: 2N5457, 2N5458, J175, J176, 2N7000, BS170. Original generic models cover their device **families**, not those manufacturers' parts. The available 2N4341 is included. Existing BJT model catalog remains preserved.

The Qucs-S 555 library was inspected; the TLC555 block embeds TI terms, so it was not indiscriminately copied under the repository's GPL notice. 555/556, digital ICs/HDL, ADC/DAC, microcontrollers, transformers/relays, full transistor thermal/noise/distortion and tolerance analyses, hierarchy, PCB layout and native NI file conversion remain outside this milestone. They must not appear as simulated features simply because upstream candidate projects implement them.

## Instruments and UI

- DC, transient, AC and single-voltage-source DC sweep run with ngspice. AC input source is explicitly selectable, so a supply is not accidentally excited.
- Native generator supports DC/sine/square/triangle; triangle pulse widths are explicitly nonzero to avoid ngspice's zero-width default behavior.
- Differential meter reads voltage, RMS and captured voltage-source/probe current; a zero-volt series current probe supports branch-current measurement. It is not an ohmmeter or live hardware instrument.
- Scope has node aliases and A/B sample cursors with delta time/voltage. Cursor reciprocal interval is labelled as such, not automatically called signal frequency. No NI trigger, independent channel scales or calibrated timebase parity.
- Bode, voltage spectrum and thresholded analog logic traces retain their prior bounds. Threshold traces are not digital gate simulation.
- Components palette and browser expose new families, pin order and provenance. Named net aliases join electrically, persist through save/load and follow attached pins on drag/rotation. Aliases are not physical BOM parts.
- Course browser loads editable labelled modular schematics and the matching analysis; it does not copy the PDF's diagram artwork. Check Experiment Results reports model-specific acceptance bounds, not a completed-course certificate.

## Reproduce

Install Python/Tk and a complete ngspice runtime. From the repository root:

```bash
PYTHONPATH=prototype python -m unittest discover -s prototype/tests -v
python -m unittest discover -s tests -v
python scripts/verify_course.py --output reports/course --raw
```

Use Xvfb for Linux headless GUI tests. Set `OCW_NGSPICE` if the solver is not on PATH. Rebuild device data with `python scripts/import_qucs_devices.py` then `python scripts/import_course_devices.py` against the pinned submodule.

Committed compact evidence under `docs/evidence/electronics-course` contains every fixture's checks, exact generated SPICE deck, solver log, source digest and native GUI checklist. Full raw tables/CSV are generated by `--raw`; they are not bundled into this compact evidence. Windows rendering, native Qt interaction for these added controls and NI numerical comparison remain unverified.
