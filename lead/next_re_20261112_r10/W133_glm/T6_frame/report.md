# T6_frame — 0x006DD8B0 per-frame decomposition

**Verdict: INCOMPLETE (cancelled early by lead before any disassembly).**

## Established before cancellation [已证]

Environment / artifact availability only; **no instruction-level analysis of `0x006DD8B0` was performed**.

- Toolchain verified: Python 3.12.10, `pefile` 2024.8.26, `capstone` 5.0.7 (`python -c` import check).
- Target present: `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe` [未证 hash — not recomputed; only `Get-Item` metadata taken].
- Supporting artifacts located and headers inspected:
  - `W130_atlas\function_atlas.tsv` (12,916 rows; columns `entry, size, n_instr, n_callers, n_callees, is_fnptr, first_import, n_strings, strings`).
  - `W130_atlas\class_atlas_v2.tsv`, `W130_atlas\vtables_canonical.json` (dict with `vtables` list: entries `{vt, col, class, sig, col_offset, section}`; e.g. vt `0x7E220C8` = `CDFileClass`).
  - `W131_subsystems\calledges.raw.log` (4.18 MB), `W131_subsystems\fn_subsystem_canonical.tsv`, `W131_subsystems\vtable_members.tsv`.
- Output directory `W133_glm\T6_frame\` created; sibling T1/T3/T5 dirs confirmed present.

## Not established (remains open)

- Every planned deliverable: `t6_frame.py`, `loops.tsv`, `cost_centres.tsv`, `unresolved_virtuals.tsv` — none written; no loops of `0x006DD8B0` were identified; the `case 1` branch was never disassembled; no virtual calls resolved; no nesting/quadratic candidates found.
- All findings in the task brief (per-type instance arrays at `0xA8EAE8` etc., `Sleep(1000)`, `switch *(obj+0x2C)`) are carried forward as lead-supplied facts [已证 by parent], not re-verified here.

## Suggested resumption point

Start directly at: load `function_atlas.tsv` for `entry=006DD8B0` (size 9,530), capstone-decode from that entry forward with `md.skipdata = True`, walk the `switch (*(int*)(obj+0x2C))` jump table, then isolate `case 1` and sweep backward branches. No re-planning needed; the original brief is self-contained.
