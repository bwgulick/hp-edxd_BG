# HANDOFF — hpMCA ↔ Bluesky integration

**Purpose:** self-contained brief for a *fresh Claude Code session* to integrate the hpMCA
energy-dispersive XRD application with Bluesky at 16-BM-B. Captures a full survey of hpMCA
already done so the new session does **not** need to re-run discovery.

**How to use:** paste this whole file into a new session as the opening message, or say
"read HANDOFF_hpmca_bluesky.md and continue."

**Sibling brief:** `HANDOFF_sonicpy_epics_bridge.md` in this directory. hpMCA is structurally
the *same problem* as SonicPy — a Hrubiak-authored PyQt app with an EPICS bridge that exists
but is commented out — and SonicPy's resolution (Design A + soft IOC + ophyd device + GUI
launch panel) is the template. Read that one too; do not re-litigate decisions settled there.

---

## 0. First actions for the new session

1. Read `HANDOFF_sonicpy_epics_bridge.md` (the precedent) and this repo's `CLAUDE.md`
   (code map + the "validate physics via a direct probe with isolated CA / private port /
   `persist=False`; never clobber the user's config" rule).
2. Read the bits repo's `CLAUDE.md` if present — that is the *port target*, not this sandbox.
3. **Verify before trusting line numbers.** This brief names *symbols*; grep the symbol.
   hp-edxd is a separate repo on its own branch and drifts.
4. **Settle §5 (the scope boundary) with Brian before writing code.** Everything downstream
   depends on it, and one plausible answer is "build less than you think."

---

## 1. Context & goal

- **Beamline:** APS 16-BM-B (HPCAT). User: Brian Gulick.
- **hpMCA's author (Ross Hrubiak) has moved on — modifying hpMCA is allowed**, same as SonicPy.
- **Stated goal:** launch hpMCA from the Bluesky GUI or from a terminal, as part of porting
  the 16-BM-B controls stack to Bluesky/BITS.
- **Realistic goal underneath it:** hpMCA is the tool the beamline actually uses to view and
  analyze EDXD spectra. Bluesky needs to (a) start it, (b) not fight it over the detector
  record, and (c) exchange enough state that an automated P/T experiment can use both.

---

## 2. Repos & key paths

| What | Where |
|---|---|
| **hp-edxd / hpMCA** (survey subject) | `C:\Users\bgulick\Documents\GitHub\SonicPy-devel\hp-edxd_BG` |
| **Bluesky sandbox** (this repo) | `C:\Users\bgulick\Documents\GitHub\16BMB_bluesky_sandbox` |
| **BITS / beamline port target** | `C:\Users\bgulick\bmbgitlab\16bmb-bits` |
| **SonicPy** (the precedent) | `C:\Users\bgulick\Documents\GitHub\SonicPy-devel\SonicPy-devel` |

hp-edxd is a **multi-app repo**: `hpMCA.py`, `aEDXD.py`, `multiangle.py`, `mdc.py`, `xrda.py`,
`SXDM.py` each sit at the root with their own package (`hpm/`, `axd/`, `multiangle/`, …).
Only `hpMCA.py` / `hpm/` matter here. `old/` is a junk drawer — ignore it entirely.

**BITS files that already exist and are the templates to copy:**

| File | Why it matters |
|---|---|
| `src/bm16b/gui/panels/ultrasonic_panel.py` | `_launch_sonicpy` — **the exact launch pattern to copy** |
| `src/bm16b/gui/panels/mca_menu.py` | where an hpMCA button belongs; already has greyed placeholders |
| `src/bm16b/gui/panels/mca_viewer.py` | **overlaps hpMCA** — see §5 |
| `src/bm16b/devices/dante_mca.py` | the ophyd device that owns `16bmbDante:mca1` today |
| `src/bm16b/sim/sonicpy_ioc.py` | soft-IOC blackboard pattern, if a bridge IOC is needed |
| `src/bm16b/plans/ultrasonic.py` | fire-and-forget plan helper pattern |

**As of this survey, BITS contains zero references to hpMCA.** This is greenfield; the only
`hp-edxd` mentions are in `src/bm16b/utils/jcpds.py`, describing the JCPDS file format.

---

## 3. Architecture findings — already verified, do NOT re-discover

### 3.1 Entry point and the absence of a CLI

`hpMCA.py` is 19 lines: `from hpm import main; main()`. `main()` is in `hpm/__init__.py` —
sets DPI awareness, builds `QApplication`, constructs `hpmcaController`, `widget.show()`,
`app.exec_()`.

**There is no argparse, no CLI flags, no environment-variable configuration.** You cannot
currently tell hpMCA at launch which detector to open or which file to load. This is the
single biggest blocker to "launch it from the GUI usefully," and §6 Phase 2 fixes it.

Version: `__version__ = "0.7.3"` in `hpm/__init__.py`.

### 3.2 Structure

MVC-ish, ~30k lines in `hpm/` plus shared `utilities/` and `mypyeqt/`.

- **`hpm/models/mcaModel.py` → class `MCA`** — the base data model: spectrum data,
  `McaCalibration` (offset/slope/quad/two_theta/wavelength + a `dx_type` of `'edx'`/`'adx'`),
  `McaROI` list, `McaElapsed`, `McaPresets`, `McaEnvironment`.
- **Two subclasses supply the two data sources:**
  - `multiFileMCA` (`hpm/models/calcMCA.py`) — files and folders.
  - `epicsMCA` (`hpm/models/epicsMCA.py`) — live detector over Channel Access. Descends from
    Mark Rivers' IDL/Python `epicsMca`; Hrubiak ported it to Py3 + Qt signalling in 2018.
- **`hpm/controllers/hpmca_controller.py` → class `hpmcaController`** — the hub (~990 lines).
  Owns `self.mca`, the `element` index, and `self.Foreground` (`'epics'` or `'file'`).
  Everything else hangs off it.
- **`hpm/widgets/hpMCA_ui.py`** builds the main window in hand-written Qt (no runtime `.ui`).
- **`mypyeqt/`** — PV-bound Qt widgets (`pvQLineEdit`, `pvQOZButton`, `pvQProgressBar`…)
  used for the live acquisition controls.
- **Settings** persist as JSON in the user's *home directory*: `hpMCA_defaults.json`,
  `hpMCA_folder_settings.json`, `hpMCA_file_settings.json`, `hpMCA_file_naming_settings.json`.

### 3.3 The dual-source design (central idea)

hpMCA holds a file MCA **and** an EPICS MCA at the same time (`fileMCAholder`,
`epicsMCAholder`) and swaps which is foreground via the **File view** / **Live view** buttons.
On each swap the EPICS preset widgets are `connect()`/`disconnect()`'d from their PVs — see
`set_file_mca` and `set_epics_mca`. Only the live view can drive hardware.

### 3.4 The EPICS layer — what hpMCA does to the mca record

`openDetector()` prompts for a record name (default from `~/hpMCA_defaults.json`). `epicsMCA`
then builds a per-detector PV dict against the synApps mca record:

| group | fields |
|---|---|
| calibration | `CALO CALS CALQ TTH EGU` |
| elapsed | `ERTM ELTM ACT RTIM STIM` |
| acquire | `STRT STOP ERAS ACQG PROC ERST READ` |
| data | `VAL NUSE NMAX` |
| presets | `PRTM PLTM PCT PCTL PCTH CHAS DWEL PSCL` |
| ROIs | `R0..R23` × `lo hi bg nm`, plus `R{n}` / `R{n}N` |

- **Multi-element discovery:** if the record name ends in `mcaN`, it probes `prefix:mca1`,
  `mca2`, … with a 0.05 s connection timeout until one fails → `n_detectors`. Record names are
  composed as `record_name[:-1] + str(i+1)`, i.e. **it assumes a trailing single digit.**
  `16bmbDante:mca1` fits that shape; verify the probe loop doesn't mis-count on the Dante.
- **Async:** `epicsMonitor` (a `QObject` wrapping `pyepics.add_callback` into a `pyqtSignal`)
  plus a debounced `custom_signal`, so a fast detector can't flood the GUI.

**⚠ The `.ACQG` trap — already known on the BITS side.** hpMCA's `handle_mca_callback_acqg`
monitors `.ACQG` to sync its Start/Stop buttons. `bm16b/devices/dante_mca.py` documents that
**the Dante asyn driver does not drive `.ACQG`** — it reads 0 through a real acquisition.
Independently, hpMCA's author hit the same wall from the other side: `acq_stopped` is actually
detected by watching the *start-time* field `.STIM` change (`handle_mca_callback_end_time`),
with the comment *"this is the only way I could figure out how detect stop when scanning."*

Consequence: **hpMCA's live view will probably show wrong button state on the Dante**, even
though the `.STIM` fallback keeps acquisition-complete detection working. Test this first —
it is cheap to check and it colours the whole §5 decision.

### 3.5 What hpMCA *writes* to the record

This is the coexistence hazard. In live view hpMCA is a writer, not an observer:

- `epicsMCA.set_rois` puts `R{n}lo/hi/nm` **and clears every unused ROI slot to `-1`**.
- `epicsMCA.set_calibration` puts `CALO/CALS/CALQ/TTH/EGU`.
- `acqOn` / `acqOff` / `acqErase` put `STRT` / `STOP` / `ERAS`.
- `set_presets` puts the whole presets group.

`devices.yml` declares `ge_detector` as `DanteMCA` on prefix `16bmbDante:mca1`. If hpMCA opens
that same record, **two writers share one record** and hpMCA can silently overwrite a
calibration the 2θ plan just wrote.

### 3.6 Analysis features (for scope discussions)

Menu-driven controller+widget pairs: JCPDS phase overlays with P/T EOS, ROI management with
peak fitting, energy calibration (`eCalWidget`), 2θ calibration (`TthCalWidget`), XRF line
lookup, pattern overlays, lattice refinement with Birch–Murnaghan thermal EOS, amorphous
analysis (S(q)/PDF), and a multi-spectra browser with masking for folder-scale datasets.

**This is the real value of hpMCA and none of it exists on the Bluesky side.**

### 3.7 File I/O

`hpm/models/mcaIO.py`: `.hpmca` (native ASCII), Amptek `.mca`, `.chi`, `.xy`, `.dat`,
GSAS `.fxye`, PNG. Auto-export on save is configurable per format. A `QFileSystemWatcher`
exists to auto-load new files in a watched folder — **but it is disconnected** (§4.3).

---

## 4. What is commented out / disabled

Ranked by impact on this integration. Symbols are the anchors; grep them.

### 4.1 `epics_sync = False` — `hpm/__init__.py` ★ most important

A module-level kill switch. `FileSaveController` does `from .. import epics_sync` and gates
its entire EPICS file-record block on it. With it `False`, `self.pvs_file` stays `{}`, so
`update_epics_filename()` silently no-ops inside a bare `except`.

**hpMCA already knows how to publish the filename it just saved to
`16bmb:mca_file:FullFileName_RBV`, and that is switched off by one line.**

### 4.2 `FileSaveController.epics_connections()` is `pass`

Below it, commented out, is the full areaDetector-style PV set the author intended:
`FilePath`, `FilePath_RBV`, `FileName`, `FileName_RBV`, `FullFileName_RBV`, `FileTemplate`,
`FileTemplate_RBV`, `WriteMessage`, `FileNumber`, `FileNumber_RBV`, `AutoIncrement`,
`AutoIncrement_RBV`, `WriteStatus`, `FilePathExists_RBV`, `AutoSave`, `AutoSave_RBV`,
`WriteFile`, `WriteFile_RBV`.

Below *that*, in a docstring, is the exact EPICS db record to create:

```
record(waveform,"16bmb:mca_file:FullFileName_RBV"){
    field(DESC,"FullFileName")
    field(DTYP,"Soft Channel")
    field(DESC,"file name")
    field(NELM,"256")
    field(FTVL,"CHAR")
}
```

The default record prefix is `file_record = '16bmb:mca_file'` (in `utilities/hpMCAutilities.py`,
the defaults class). **This is the designed-but-unbuilt control surface, and it is exactly what
a Bluesky plan would drive.**

### 4.3 Folder watcher disconnected — `FileSaveController`

Both `directoryChanged.connect(...)` / `.disconnect(...)` calls inside
`folder_watcher_start_watching` / `folder_watcher_stop_watching` are commented out, and
`folder_watcher_handle_directory_changed` is a `'''...'''` block. The `SignalProxy` and
`handle_directory_changed` still exist and work — nothing calls them.
`folder_watcher_stop_watching` even prints a warning about precisely this.

**If the handoff mechanism is "Bluesky writes spectra, hpMCA follows the folder," this is the
line you restore.** Un-commenting it is the smallest possible integration that does something
useful.

### 4.4 The autoload block in `main()` — `hpm/__init__.py` ★ the CLI template

~20 commented lines of `controller.file_save_controller.openFile(...)`, `.openFolder(...)`,
`controller.load_calibration(...)`, `controller.phase_controller.add_btn_click_callback(...)`,
`controller.multiple_datasets_controller.show_view()`.

Debug scaffolding — but it is the author demonstrating that the controller can be driven
programmatically after construction. **This is the body of the `--file` / `--folder` /
`--detector` CLI in Phase 2.** Do not invent an API; use these calls.

### 4.5 Dead UI wiring

- **hklGen fully disabled.** Import commented in `hpmca_controller.py`; `self.hlkgen_controller`
  construction commented in `initControllers`; `hklGen_module()` is `pass`. But
  `ui.actionhklGen.triggered.connect(self.hklGen_module)` is live and
  `menu_items_set_enabled` explicitly **enables** `actionhklGen` → a menu item that does
  nothing. The `hklGenController` / `hklGenModel` / `hklGenWidget` triple is unreferenced.
- **`actionShowCalibration` unreachable.** Its `connect` is commented in `create_connections`
  and its `menuControl.addAction` is commented in `hpMCA_ui.py` — yet `menu_items_set_enabled`
  still enables it. `show_calibration()` and `self.show_calibration_widget` are constructed
  and live, with no way in.
- **"Save next" removed** — the menu entry (`hpMCA_ui.py`) and its filename-increment logic
  (`FileSaveController`) are both commented out.
- **`multispectral_refresh_folder_btn_clicked_callback` is `pass`** with a note that it moved
  into `FileSaveController`, but the button is still connected.

### 4.6 Inside `epicsMCA`

- **Three dead monitors:** `start_monitor`, `stop_monitor`, `why_stopped` are all commented
  out at construction. Their handlers survive as `pass` with the bodies in `'''...'''`
  (`handle_mca_callback_start`, `handle_mca_callback_stop`, `handle_mca_callback_why_stopped`).
  This is the residue of the `.ACQG` struggle in §3.4 — useful archaeology, don't just delete it.
- **ROI background width dropped:** `roi.bgd_width` get/put are commented in `get_det_rois`
  and `set_rois`. The `R{n}bg` PVs are created but never read or written.

### 4.7 Housekeeping (low priority)

- ~30 commented import lines (`#from epics.clibs import *`, Dioptas leftovers such as
  `#from ....model.DioptasModel import DioptasModel`, strays like `#import imp`).
- `MultipleDatasetsController`: scratch-buffer, mask-scaling and q/E view code.
- `mcaPlotController`: cursor unit-conversion on axis change.
- `#self.antialias_btn` in four places in `hpMCA_ui.py`.
- **Unwired files — nothing imports any of them:** `hpm/controllers/adc_controller.py`,
  `hpm/controllers/test.py`, `hpm/models/rois_test.py`, `hpm/tabtest.py`, and the whole
  `stripchart/` package. Plus the entire `old/` tree.
- **`catch1d.env` at the repo root is empty (0 lines).** It is read at `epicsMCA` init to build
  the environment-PV list embedded in saved file headers, so the Environment module currently
  shows nothing. *Same state as SonicPy's `catch1d.env`* — if Brian wants environment PVs in
  file headers, this file is the one to populate, on both apps.

---

## 5. THE SCOPE BOUNDARY — decide this first ★

Do not start coding until Brian answers this. Two facts collide:

1. **BITS already has `gui/panels/mca_viewer.py`** — a live EDXD spectrum viewer with
   counts-vs-energy plotting, acquisition control and an ROI table, already correct about
   `dante1:AcquireBusy`. It overlaps hpMCA's live view.
2. **hpMCA writes to the mca record** (§3.5), so running both against
   `16bmbDante:mca1` means two writers on one record.

Three coherent answers:

- **(A) hpMCA = viewer/analysis; Bluesky = acquisition owner. ← recommended.**
  hpMCA never opens the detector in live view; it opens *folders* that Bluesky writes. The
  folder watcher (§4.3) becomes the handoff. No shared-record writes, `.ACQG` never matters,
  and hpMCA's genuine value (§3.6 — JCPDS, EOS, lattice refinement, amorphous analysis) is
  exactly what Bluesky lacks. Smallest change, largest payoff.
- **(B) hpMCA keeps live view; Bluesky yields the record while it is open.** Needs an
  interlock (who holds the detector?) and hits the `.ACQG` problem head-on. More faithful to
  current operator habit, considerably more work.
- **(C) Full bidirectional bridge** — build out §4.2 so Bluesky commands hpMCA's file saving.
  This is the direct analogue of SonicPy Design A and the largest lift. Justified only if
  hpMCA must *save* on a plan's command.

**Recommendation: A now, C later if a plan turns out to need hpMCA-side saving.** B looks
appealing because it matches today's workflow, but it buys a concurrency problem to preserve a
habit that a Launch button plus a folder watcher can satisfy.

---

## 6. The plan — phases

### Phase 0 — Smoke test (do before anything else, ~1 hour)
Run hpMCA against the real Dante and answer three questions empirically:
1. Does `openDetector('16bmbDante:mca1')` connect at all?
2. Does the multi-element probe loop report the right `n_detectors`? (§3.4 — the `[:-1]` slice.)
3. Do the Start/Stop buttons show correct state, or does the `.ACQG` problem bite? (§3.4.)

Record the answers here. They may settle §5 on their own.

### Phase 1 — Scope decision (§5). **Get Brian's sign-off.**

### Phase 2 — Give hpMCA a CLI *(in hp-edxd; ~20 lines)*
Add argparse to `main()` in `hpm/__init__.py` (keep `hpMCA.py` as the thin shim):

```
--detector <PV>   → controller.openDetector(detector=...)
--file <path>     → controller.file_save_controller.openFile(filename=...)
--folder <path>   → controller.file_save_controller.openFolder(foldername=...)
--calibration <f> → controller.load_calibration(filename=...)
```

The commented autoload block (§4.4) is the body — those calls are the author's own and are
known to work. Keep bare `python hpMCA.py` behaving exactly as today.

### Phase 3 — Launch panel *(in BITS)*
New `src/bm16b/gui/panels/hpmca_panel.py`, copying `ultrasonic_panel._launch_sonicpy`:
`subprocess.Popen([sys.executable, ENTRY], cwd=APP_DIR, env=env)`, a `BM16B_HPMCA_DIR`
env override, a clear message when the path is wrong rather than a silent failure, and a
`QTimer` showing Running / Stopped (exit N). Wire a button into `mca_menu.py`, which already
has the slot and a column of greyed placeholders.

Pass the Phase-2 flags from the panel so the launch is *useful*, not just a blank window.

### Phase 4 — Data handoff, cheap direction (hpMCA → Bluesky)
Set `epics_sync = True` (§4.1) and create the `16bmb:mca_file:FullFileName_RBV` waveform
record — the db snippet is in §4.2, verbatim from the source. Add an ophyd `EpicsSignalRO`
so a plan can read which file hpMCA last wrote. Near-free; do it even under scope (A).

### Phase 5 — Folder-watcher handoff (scope A)
Restore the two commented `directoryChanged` connects (§4.3) so hpMCA auto-loads spectra as
Bluesky writes them. Validate against a throwaway directory, never real data.

### Phase 6 — (only if scope C) Full bridge
Build out the areaDetector-style PV set (§4.2), a soft IOC modelled on
`src/bm16b/sim/sonicpy_ioc.py` (passive blackboard, no putters), an ophyd device alongside
`UltrasonicScanner`, and a plan helper modelled on `plans/ultrasonic.py`.

---

## 7. Environment & porting gotchas

- **hp-edxd pins old dependencies.** Its README requires PyQt5 **5.9.2**, pyqtgraph **0.11.0**
  (explicitly *"Not compatible with 0.12.0+"*), pyepics 3.4.0, burnman 0.9.0, PyCifRW 4.4.1,
  on Python 3.7. There is **no `requirements.txt`** — only prose in the README and the
  PyInstaller `.spec`. BITS uses `qtpy` under pixi. **These environments will not reconcile.**
  That is an independent, decisive argument for `subprocess.Popen` over importing hpMCA
  in-process — do not attempt `from hpm import main` inside the BITS GUI.
- `from epics.clibs import *` at the top of `hpmca_controller.py` is a PyInstaller DLL-bundling
  hack. Harmless, but it makes pyepics a hard import-time dependency.
- **Settings live in the user's home, not the repo:** `~/hpMCA_defaults.json` etc. The
  `detector` default is still `'16bmb:aim_adc1'` and `file_record` is `'16bmb:mca_file'`.
  A per-beamline default is a JSON edit, not a code change — but it is also **user state you
  must not clobber** during testing.
- hp-edxd ships PyInstaller specs (`hpMCA.spec`) and an existing release pipeline. If the
  controls machine runs a frozen hpMCA rather than source, Phase 2's CLI needs a rebuild —
  confirm with Brian which one is deployed.

---

## 8. Validation strategy & guardrails

- **Windows validation:** follow `bluesky-sim-testing-gotchas`. Use a direct probe with
  isolated Channel Access on a **private port** and `persist=False`; do not trust a headless
  IOC-without-GUI harness for physics.
- **Never clobber the user's data or config.** Keep test output in a throwaway directory.
  Do not touch `~/.16bmb_beamline/…` or `~/hpMCA_*.json` — back them up before any test that
  could write them (hpMCA saves settings on many ordinary actions).
- **Two writers is the failure mode to watch for.** Any test that puts hpMCA in live view
  against a record Bluesky also owns can overwrite a real calibration. Prefer a sim record.
- **Shared files (multi-session):** re-read before editing.
- **Delegate blast-radius discovery** to an Explore/Agent subagent, not greps into the main
  context. Prefer narrow reads over whole-file dumps.

---

## 9. Open decisions to confirm with Brian

1. **§5 scope boundary — A, B or C.** Recommend A. Everything else depends on this.
2. Does hpMCA's live view need to survive at all, given `mca_viewer.py` already exists?
3. Is the deployed hpMCA run from source or from a PyInstaller build? (Affects Phase 2.)
4. PV prefix for any hpMCA bridge: keep the author's `16bmb:mca_file:*`, or match the SonicPy
   convention with `16bmb:hpmca:*`?
5. Should `catch1d.env` be populated (for both hpMCA and SonicPy), and with which PVs?
6. Does the commented-out dead UI (hklGen, Show Calibration) get removed, or left as-is?
   It is Hrubiak's unfinished work, not ours — removing it is a judgment call, not a cleanup.

---

## 10. Survey provenance

Full read of `hpMCA.py`, `hpm/__init__.py`, `hpm/controllers/hpmca_controller.py`,
`hpm/models/epicsMCA.py`; targeted reads of `FileSaveController.py`, `mcaModel.py`,
`calcMCA.py`, `mcaIO.py`, `hpmcaWidget.py`, `hpMCA_ui.py`, `utilities/hpMCAutilities.py`.
Systematic commented-code sweep across `hpm/`, `utilities/`, `mypyeqt/`. BITS side:
`devices/mca.py`, `devices/dante_mca.py`, `devices/ultrasonic.py`, `gui/panels/mca_menu.py`,
`gui/panels/mca_viewer.py`, `gui/panels/ultrasonic_panel.py`, `gui/pv_names.py`,
`configs/devices.yml`, `sim/sonicpy_ioc.py`, `plans/tth_calibration.py`.

**Nothing in hp-edxd or BITS was modified.** This document is the only artifact.
