# Review evidence — 2026-10-18

## Delivered foundation
- Empty target inspected through GitHub and git.
- Qucs-S pinned at 46e47e8fabe852a9d6aab41d8a612ff5a78370c1 (upstream VERSION 26.1.1).
- Mature editor retained as submodule; no custom editor or virtual instruments claimed.
- Python build orchestration, RC netlist, analytical validator, failure tests, two CI jobs added.

## Local verification
- `python3 -m unittest discover -s tests -v`: six tests PASS. These test the validator using synthetic analytic data, not the real solver.
- `python3 scripts/verify_rc.py --output reports/rc.json`: FAIL as intended when ngspice is absent. No real numerical result recorded yet.
- `git diff --check`: PASS.
- System package installation blocked by environment setgroups/setuid restrictions; Qt/CMake/ngspice build could not run locally.

## Self-critique
The repository now has an engineering foundation, not a completed Multisim alternative. The Linux CI build is not interactive GUI verification. A passing RC analytic test is not an NI comparison. Windows packaging, custom instruments and ms14 import remain unimplemented. A genuine Multisim file is still needed for interoperability work; a fixture must not be invented.

## Next bounded task
Read CI logs and fix build/simulation failures. Obtain a native Windows build and test placing/wiring/saving/reopening/running an RC schematic. Record screenshots plus actual solver output. Preserve original upstream branding until a reviewed original design is ready.

## Supervision
A bounded hourly follow-up was created for 24 runs starting 2026-10-18 03:15 Asia/Baghdad. Existing general summaries remain separate. Scheduling does not prove a running Codex Cloud session or guarantee tools/quota on future runs.


## Follow-up: verified remote foundation and desktop startup gate

At main commit dbeff93b875e5e14a6d9d07376af0522ce595563, both Linux desktop compilation and the real ngspice regression succeeded:
https://github.com/ahpa5246-lgtm/Multisim/actions/runs/39078237801

Simulation job 117529733037 logs report max_error_v=1.4681871751243136e-05 (about 0.0147 mV), below the 20 mV contract. This is real ngspice evidence against the analytic RC solution, not against NI Multisim. Desktop job 117529732861 succeeded, but its old final check only tested that the installed binary was executable.

The next bounded milestone adds scripts/verify_desktop.py and a CI Xvfb startup capture. It requires a live process with a visible window at least 640x400, records title/geometry, captures a real PNG and startup log, and terminates its own process. Missing dependencies, early exits and no window fail. The version check now executes the actual binary. Capture may include a first-run dialog; it is explicitly NOT proof of a usable editor or completed drawing/simulation workflow.

Local checks: six validator tests pass; Python compileall passes; nonexistent executable fails with exit 1. Full GUI capture cannot run locally without Qt/X11 dependencies; the new remote job must supply that evidence. No Windows, .ms14, instrument, or NI parity claim. Next run must inspect this PR and its artifacts before expanding scope.


## Startup failure diagnosis and focused repair

Run 39082440616 at commit 53acf337ee3e27cb50506bb7842e8f1a4fdc4528 built successfully and passed the real solver check, but desktop startup timed out:
https://github.com/ahpa5246-lgtm/Multisim/actions/runs/39082440616
The failing step was Capture actual X11 startup (desktop job 117542006018); the version command succeeded.

Source inspection of pinned upstream qucs/qucs.cpp lines 175–250 shows that first launch opens the modal information notice titled Set simulator before main.cpp calls QucsMain->show(). The prior harness ignored every small window and never acknowledged that notice. This is a source-backed diagnosis pending remote confirmation, not evidence that the application crashed.

Repair stays in PR #1: capture and acknowledge that exact informational notice once for this process, then retain the existing 640x400 main-window gate. Unknown dialogs receive no key events. On timeout, record observed window titles/geometry and a root screenshot rather than leaving only a silent log. A regression test restricts acknowledgement to the known notice; all seven local tests and Python compilation pass. X11 execution is still unavailable locally. Inspect the next CI result and actual screenshots before marking startup verified. No UI feature, Windows, .ms14 or NI parity claim.


## X11 notice lifetime race — follow-up repair

Run 39085913601 (4451957fff0b778b468938a696017dc01010b5a7) again passed simulation and compilation but failed during the notice acknowledgement:
https://github.com/ahpa5246-lgtm/Multisim/actions/runs/39085913601
The exact error was X_SendEvent BadWindow from xdotool key --window ... Return. Downloaded and visually inspected artifact 12121042550: setup-notice.png shows the real informational notice reporting /usr/bin/ngspice and the installed qucsator_rf. This confirms the earlier first-run diagnosis; it does not show the main editor.

The remaining failure is consistent with Qt destroying the notice on Return key-down before xdotool sends key-up. The harness now tolerates only a BadWindow key-send error followed by a BadWindow probe confirming the same window has disappeared. Every other failure, including a still-open notice, propagates. The main window and process-alive gates remain unchanged.

Three new regression cases were observed failing before the helper existed, then all ten tests passed after implementation. Python compilation and diff checks pass. Real X11 confirmation remains pending the next CI run; no startup-success claim is made. Continue the existing PR rather than creating another milestone or weakening the gate.


## Verified Linux startup and next schematic gate

At commit 34b9cff473738065752343f056c625a1cafdaefe, both workflows passed:
https://github.com/ahpa5246-lgtm/Multisim/actions/runs/39089285681
Downloaded startup artifact 12122511783 and visually inspected startup.png. It shows the actual Qucs-S 26.1.1 editor with component browser, blank schematic grid and Ngspice selected, after the known notice was acknowledged. startup.json records a 720x500 window. Startup is now verified on Linux X11 only.

Harsh review: the component dock consumes roughly half this small window, leaving limited drawing space; bottom status labels overlap or crowd. This unmodified upstream screen is functional startup evidence, not a polished Multisim-like workbench. No component has yet been placed interactively, saved, reopened or simulated from the GUI. Windows remains unverified.

The next measurable gate in the existing foundation PR is export of an explicit RC schematic through the compiled editor's --netlist --ngspice command. Added examples/rc.sch plus a fixture-specific validator that checks three component values, source polarity and grounded connectivity. CI saves the actual exported netlist and report. Four new tests failed before implementation and all fourteen local tests now pass; compileall and diff checks pass. Actual editor export is pending CI, not declared successful.

Comparison source checked 2026-10-18: NI documents Transfer > Export netlist and schematic-to-SPICE workflow:
https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000YHimCAG&l=en-US
https://www.ni.com/docs/en-US/bundle/multisim/page/topics/multisim-spice-reference.html
The gate checks the analogous basic export task only. It does not prove compatibility of full models, NI file formats, instruments, netlist dialects, or numerical results. The separate charging netlist still supplies the analytic solver baseline; the schematic's export check is not a transient-equivalence claim.


## Schematic export verified; native Windows gate prepared

Run 39093208887 succeeded at 69f16040034c85305433d1cc9a55c17ab2082931:
https://github.com/ahpa5246-lgtm/Multisim/actions/runs/39093208887
Downloaded artifact 12124326150 and inspected the actual rc-export.cir and validation.json. The compiled editor exported V1 in 0 DC 5, R1 in out 1K and C1 0 out 1U; the capacitor is nonpolar, so its reversed terminal order preserves the tested connectivity. The report passes all three component checks. This confirms file parsing/export, not interactive placement, GUI save/reload or transient startup behavior.

Next bounded milestone: native Windows compilation and the same schematic-export contract using MSYS2 UCRT64, following the pinned upstream deploy.yml dependency/build approach. It lives on a separate stacked branch based on the verified foundation PR. The native job will compile/install, execute --version and run the RC export validator. It deliberately does not call a build artifact a portable installer: standalone Qt/runtime deployment, ngspice bundling and clean-machine interaction remain open.

Local evidence remains fourteen passing Python tests, compileall and diff checks. A Windows runner result does not exist yet; this change adds the gate, not a Windows success claim. No new backend, service, proprietary source, .ms14 support or instrument UI is introduced.


## Native Windows export verified; bridge to real simulation

Native Windows run 39096265664 passed at 99e81d442243c5b864f4cdcfcb743c905a80cfa4:
https://github.com/ahpa5246-lgtm/Multisim/actions/runs/39096265664
Downloaded artifact 12125467419 and inspected its exported netlist and passing validation.json. The Windows executable parsed rc.sch and exported the same V1/R1/C1 graph and values. This proves native compilation and offscreen export inside MSYS2; it does NOT prove GUI usability, a portable installer, or bundled ngspice.

The next bounded test closes a real integration gap: until now schematic export and the analytic solver baseline were separate. scripts/verify_rc.py now accepts --netlist, preserves all exported devices/includes, and replaces only the control block with explicit zero-charge (uic) measurement conditions. CI runs ngspice on those actual exported devices and validates the sampled waveform using the existing analytic contract. This changes test initial conditions deliberately; it is not a claim that the schematic's default DC-initialized transient charges from zero.

Two new cases were observed failing before implementation, then all sixteen local tests passed. They check that exported device text survives command substitution and ambiguous/missing control blocks fail. Full solver integration remains pending CI because ngspice is unavailable locally. A passing future run will establish schematic-file -> editor export -> solver -> analytic waveform, still without interactive GUI or NI comparison claims.


## Exported-device simulation verified; schematic visual inspection prepared

Run 39099994687 passed at 80ada4fafa5e635dc5df52510f4285dcf67f6b18:
https://github.com/ahpa5246-lgtm/Multisim/actions/runs/39099994687
Downloaded artifact 12125989438 and inspected exported-rc.json: 511 samples, maximum error 1.4681871751243136e-05 V, ngspice-42. The real chain schematic file -> compiled editor export -> actual exported devices -> ngspice -> analytic waveform is verified with explicitly overridden zero-charge measurement commands. This is still not an NI result comparison or GUI simulation test.

The current branch now asks the desktop capture harness to open examples/rc.sch and capture 1280x900 and 800x600 window views in addition to startup.png. It moves the window to the screen origin to avoid clipping. requested_schematic in the report is deliberately phrased as a request, not proof of successful rendering. The next run must visually inspect actual screenshots for source/resistor/capacitor connections and window density before recording success. No UI redesign or save/reload interaction is claimed.

Local verification: sixteen tests pass; compileall and diff checks pass. Full X11 fixture opening/resizing remains pending remote evidence. Preserve the current PR instead of starting another independent task.


## Loaded schematic visually confirmed; GUI persistence probe

Run 39106858952 succeeded at b5aac2fe75baa17a8f2ba4b9215af845e99263ea:
https://github.com/ahpa5246-lgtm/Multisim/actions/runs/39106858952
Downloaded artifact 12129391101 and visually inspected desktop.png (1280x900) and narrow.png (800x600). Both show rc.sch with V1=5, R1=1k, C1=1u and their wires/grounds. The larger view also shows the full transient-analysis block. The narrow view clips the block to the right and its component dock consumes substantial width: narrow-window usability is not approved. No automatic fitting or redesign is being claimed.

Next bounded milestone is an actual GUI Save As probe in its own stacked branch. It opens the existing circuit, requests the standard Save As shortcut, waits for the exact Enter a Document Name dialog belonging to this process, saves to a new artifact path, then asks the compiled editor to reparse/export that saved file and validate topology/values. It refuses any existing destination and never writes the source example. Missing dialogs/files fail rather than pretending persistence works. The CI screenshots and saved file become review evidence.

Seventeen local unit tests pass, including refusal to overwrite an existing schematic, and Python compilation/diff checks pass. GUI execution is pending CI. In particular, Save As and Save All shortcut interaction in the pinned upstream must be observed rather than assumed. Native Windows GUI/packaging, interactive wiring, instruments and NI parity remain unverified.


## Save As failure and distinct shortcut defaults

Run 39111047781 failed at 01997dfd77c001dbc25a2b2100b9658193cbdc43:
https://github.com/ahpa5246-lgtm/Multisim/actions/runs/39111047781
Compilation, export and numerical checks completed; the real GUI probe failed because Ctrl+Shift+S did not open Enter a Document Name. Downloaded artifact 12130472858 and inspected startup.log: it contains font/file warnings but does not establish the cause by itself.

Pinned qucs_init.cpp registers Save All as Ctrl+Shift+S and Save As using QKeySequence::SaveAs, whose usual Linux binding is Ctrl+Shift+S. A focused local patch gives Save All Ctrl+Alt+S while preserving the platform Save As binding. The collision is a source-backed diagnosis; the next real GUI run must confirm that this resolves the observed failure. The test is not bypassed.

patches/0001-distinct-save-all-shortcut.patch preserves the pinned upstream revision and notices. scripts/apply_patches.py checks that revision, applies only reviewed patches, recognizes an already applied patch and rejects conflicts. Both Linux and Windows builds apply it before configuration. Two local applications succeeded idempotently; the expected distinct source bindings, seventeen tests, compileall and both repository/upstream diff checks passed. Actual patched compilation and GUI saving remain pending CI.

The change affects the default Save All shortcut; existing customized settings may still require conflict review. No document, wiring, model, .ms14 format or solver behavior is modified. The GUI harness now captures a timeout screenshot to improve diagnosis if the expected dialog still fails to appear.


## Save probe environment repair; Windows Git dependency

Runs 39114920084 (Linux) and 39114920083 (Windows) failed at 8287b470dbd9dd1969f58812a9a8c0a0181411c2. Windows failed before compilation because native Python could not start git (WinError 2) inside the isolated MSYS2 environment. Add git explicitly to the MSYS2 install list; no checkout/patch guard is removed.

Linux still did not open Save As after the distinct-shortcut patch, so the earlier collision hypothesis does not fully explain the observed failure. Downloaded artifact 12132307193 and inspected save-timeout.png and startup.log: the application remains on rc.sch without a save dialog; the log contains no explicit ambiguous-shortcut warning. Do not report the shortcut patch as having fixed this GUI failure.

The existing Xvfb test ran without a window manager and only set X input focus. Qt window-scoped actions can remain inactive in that environment. Add Openbox to the isolated CI display and explicitly activate the application's top-level window before requesting Save As. This is an environment correction and remains a hypothesis pending the real run, not a successful save claim. The exact-dialog, non-overwrite and saved-topology checks remain unchanged.

Local evidence: seventeen tests, compileall and diff checks pass. Next run must inspect both jobs and the actual save-dialog/saved-file evidence. No new feature work proceeds while these gates fail.
