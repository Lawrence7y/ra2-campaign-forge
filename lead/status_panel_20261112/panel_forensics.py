# -*- coding: utf-8 -*-
"""
Five-Dimension Quantitative Status Panel Forensics Script (2026-11-12)
Strictly adheres to:
1) Zero live execution (no gamemd.exe / ra2loader / YURI.exe, no attach/memory read/hook)
2) Only writes inside D:\\Project\\ra2-campaign-forge\\lead\\status_panel_20261112\\
3) Executed via: python -I -X utf8 D:\\Project\\ra2-campaign-forge\\lead\\status_panel_20261112\\panel_forensics.py
4) All SHA-256 fingerprints computed via hashlib.sha256
"""

from __future__ import annotations

import datetime
import hashlib
import io
import os
import re
import shutil
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
OUT_DIR = os.path.join(ROOT, "lead", "status_panel_20261112")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def file_meta(rel_path: str) -> dict:
    full = os.path.join(ROOT, rel_path) if not os.path.isabs(rel_path) else rel_path
    if not os.path.isfile(full):
        return {"path": rel_path, "exists": False}
    st = os.stat(full)
    tz = datetime.timezone(datetime.timedelta(hours=8))
    mtime_iso = datetime.datetime.fromtimestamp(st.st_mtime, tz).isoformat(timespec="seconds")
    lines = None
    if full.endswith((".md", ".py", ".txt", ".json", ".ini", ".cpp", ".h", ".MAP", ".map")):
        try:
            with open(full, "rb") as f:
                lines = f.read().count(b"\n") + 1
        except Exception:
            lines = None
    return {
        "path": rel_path,
        "exists": True,
        "size": st.st_size,
        "sha256": sha256_file(full),
        "mtime": mtime_iso,
        "lines": lines,
    }


def main() -> int:
    buf = io.StringIO()

    def log(msg: str = "") -> None:
        print(msg)
        buf.write(msg + "\n")

    tz = datetime.timezone(datetime.timedelta(hours=8))
    now_iso = datetime.datetime.now(tz).isoformat(timespec="seconds")
    log(f"=== FIVE-DIMENSION STATUS PANEL FORENSICS | RUN_AT={now_iso} ===")
    log(f"Command: python -I -X utf8 {os.path.abspath(__file__)}")
    log("")

    # 1. Core Target Binaries & Baseline Documents
    log("[SECTION 1] TARGET BINARIES & BASELINE DOCUMENTS")
    core_files = [
        r"ra2bench\gamemd.exe",
        r"ra2youli\gamemd.exe",
        r"ra2bench\ra2render.dll",
        r"docs\PROJECT_DIRECTION.md",
        r"lead\GOAL_THREE_TARGETS_20261018.md",
        r"lead\PENDING_DECISIONS.md",
        r"lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md",
        r"lead\re_progress_check_20261111\RE_PROGRESS_20261111.md",
        r"lead\goal_status_tables_20261019\STATUS_TABLES.md",
        r"lead\direction_ruling_20261108\RULING_DIRECTION.md",
        r"re_atlas\STATUS.md",
        r"re_atlas\LEDGER.md",
        r"re_atlas\INDEX.md",
        r"re_atlas\CONFLICTS.md",
        r"re_atlas\HANDOFF_TO_GOAL3T.md",
    ]
    for rel in core_files:
        m = file_meta(rel)
        log(f"  {m['path']} | exists={m['exists']} | size={m.get('size')} | sha256={m.get('sha256')} | mtime={m.get('mtime')} | lines={m.get('lines')}")
    log("")

    # 2. Dimension 1: Performance (T50, T55e, §602/603/604/607/609, G1 freeze)
    log("[SECTION 2] DIMENSION 1: PERFORMANCE EVIDENCE FILES")
    dim1_files = [
        r"out\re_work\work_chain\CONTINUE_20261003\lead\goal1_c1c2_readj_20261018\C1C2_READJ_T50.md",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\cards\QC161.md",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\TRIP_ID_RECONCILIATION_20261018.md",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\measure_w0.json",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\measure_w1.json",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\measure_w2.json",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\evidence\20261019T180440325218\MANIFEST.json",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\evidence\20261019T180440325218\XMP29U2.MAP",
        r"lead\slowframe_r3_20261108\S604_GAP_RECHECK.md",
        r"lead\s604_script_hunt_20261109\S604_SCRIPT_HUNT.md",
        r"lead\s604_script_hunt_20261109\_sh_generator_512655.txt",
    ]
    for rel in dim1_files:
        m = file_meta(rel)
        log(f"  {m['path']} | exists={m['exists']} | size={m.get('size')} | sha256={m.get('sha256')} | mtime={m.get('mtime')} | lines={m.get('lines')}")
    log("")

    # 3. Dimension 2: Stability (W11, 0x7CFC9F 5 single-steps, Breakpoints 2/6, RC-4)
    log("[SECTION 3] DIMENSION 2: STABILITY EVIDENCE FILES")
    dim2_files = [
        r"lead\re_line_20261105\W11_EXCEPT_FRESHNESS\W11_EXCEPT_FRESHNESS.md",
        r"lead\re_line_20261105\W11_EXCEPT_FRESHNESS\candidate\test_except_freshness.py",
        r"lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py",
        r"lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\W9_SINGLESTEP.md",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc124_observe_chain\QC124_VERDICT.json",
        r"ra2bench\except.txt",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\boot_hang_triage_20261018\EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc119_after_entry\carrier\except.txt",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc120_entry_then_arm\carrier\except.txt",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc121_entry_then_arm\carrier\except.txt",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc123_rc1_only\carrier\except.txt",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc124_observe_chain\_backup\except_pre_qc124.txt",
        r"lead\r2_unclosed_b_20261108\B_BREAKPOINTS_2_6.md",
        r"lead\b_unclosed_trace_20261108\B_BREAKPOINT2_TRACE.md",
        r"lead\criteria_r3_verify_20261108\R2_BREAKPOINTS_CLOSURE.md",
    ]
    for rel in dim2_files:
        m = file_meta(rel)
        log(f"  {m['path']} | exists={m['exists']} | size={m.get('size')} | sha256={m.get('sha256')} | mtime={m.get('mtime')} | lines={m.get('lines')}")

    log("  --- 5 Distinct 0x007CFC9F EXCEPTION_SINGLE_STEP except.txt Details ---")
    ss_files = [
        r"out\re_work\work_chain\CONTINUE_20261003\lead\boot_hang_triage_20261018\EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc119_after_entry\carrier\except.txt",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc120_entry_then_arm\carrier\except.txt",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc121_entry_then_arm\carrier\except.txt",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc123_rc1_only\carrier\except.txt",
    ]
    for rel in ss_files:
        full = os.path.join(ROOT, rel)
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            txt = f.read()
        eip = re.search(r"Eip:[0-9A-Fa-f]+\s+Esp:[0-9A-Fa-f]+\s+Ebp:[0-9A-Fa-f]+", txt)
        eax = re.search(r"Eax:[0-9A-Fa-f]+\s+Ebx:[0-9A-Fa-f]+\s+Ecx:[0-9A-Fa-f]+", txt)
        edx = re.search(r"Edx:[0-9A-Fa-f]+\s+Esi:[0-9A-Fa-f]+\s+Edi:[0-9A-Fa-f]+", txt)
        err = re.search(r"Error code: [^\r\n]+", txt)
        log(
            f"    {rel} | size={os.path.getsize(full)} | sha256={sha256_file(full)} | "
            f"{err.group(0) if err else ''} | {eip.group(0) if eip else ''} | "
            f"{eax.group(0) if eax else ''} | {edx.group(0) if edx else ''}"
        )
    log("")

    # 4. Dimension 3: Safe Modification Capability
    log("[SECTION 4] DIMENSION 3: SAFE MODIFICATION CAPABILITY FILES")
    dim3_files = [
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc161_patch_QC194_196_verify_20261018\PATCH_VERIFY_VERDICT.md",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc134_attach_probe\qc134_attach.py",
        r"out\re_work\work_chain\CONTINUE_20261003\lead\qc135_object_locator\qc135_objloc.py",
        r"docs\re\dispatch\W3_20261001_ZCode_S6_gapfix_rm_verify.md",
        r"out\re_work\zcode_live\W3_20261001\gapfix_rm\RM_RESULT.md",
    ]
    for rel in dim3_files:
        m = file_meta(rel)
        log(f"  {m['path']} | exists={m['exists']} | size={m.get('size')} | sha256={m.get('sha256')} | mtime={m.get('mtime')} | lines={m.get('lines')}")
    log("")

    # 5. Dimension 4: DLC Framework (ra2forge) + Deterministic Build Probe
    log("[SECTION 5] DIMENSION 4: RA2FORGE MODULES & BUILD PROBE")
    ra2forge_files = [
        r"examples\demo_campaign.json",
        r"ra2forge\__init__.py",
        r"ra2forge\__main__.py",
        r"ra2forge\cli.py",
        r"ra2forge\design.py",
        r"ra2forge\builder.py",
        r"ra2forge\maplib.py",
        r"ra2forge\triggers.py",
        r"ra2forge\mixlib.py",
        r"ra2forge\install.py",
        r"ra2forge\lzo.py",
        r"ra2forge\format80.py",
    ]
    for rel in ra2forge_files:
        m = file_meta(rel)
        log(f"  {m['path']} | exists={m['exists']} | size={m.get('size')} | sha256={m.get('sha256')} | mtime={m.get('mtime')} | lines={m.get('lines')}")

    sys.path.insert(0, ROOT)
    import ra2forge.cli as rf_cli

    probe1 = os.path.join(OUT_DIR, "build_probe")
    probe2 = os.path.join(OUT_DIR, "build_probe_repeat")
    if os.path.isdir(probe1):
        shutil.rmtree(probe1)
    if os.path.isdir(probe2):
        shutil.rmtree(probe2)

    design_path = os.path.join(ROOT, "examples", "demo_campaign.json")
    rc1 = rf_cli.main(["build", "--design", design_path, "--out", probe1])
    rc2 = rf_cli.main(["build", "--design", design_path, "--out", probe2])
    rc_val = rf_cli.main(["validate", design_path])
    log(f"  ra2forge validate exit={rc_val} | build1 exit={rc1} | build2 exit={rc2}")

    camp_dir1 = os.path.join(probe1, "钢铁残响")
    camp_dir2 = os.path.join(probe2, "钢铁残响")
    deterministic_match = 0
    total_built = 0
    for fn in sorted(os.listdir(camp_dir1)):
        p1 = os.path.join(camp_dir1, fn)
        p2 = os.path.join(camp_dir2, fn)
        s1 = sha256_file(p1)
        s2 = sha256_file(p2)
        eq = s1 == s2
        total_built += 1
        if eq:
            deterministic_match += 1
        log(f"    ARTIFACT {fn} | size={os.path.getsize(p1)} | sha256={s1} | repeat_equal={eq}")
    log(f"  Deterministic build check: {deterministic_match}/{total_built} identical across runs")
    shutil.rmtree(probe2)
    log("")

    # 6. Dimension 5: Reverse-Engineering Knowledge Base Statistics
    log("[SECTION 6] DIMENSION 5: REVERSE-ENGINEERING KNOWLEDGE BASE STATS")
    goal_path = os.path.join(ROOT, "lead", "GOAL_THREE_TARGETS_20261018.md")
    with open(goal_path, "r", encoding="utf-8") as f:
        goal_lines = f.readlines()

    h2_all = []
    sec_headings = []
    for idx, line in enumerate(goal_lines, 1):
        if line.startswith("## "):
            h2_all.append((idx, line.strip()))
        m_sec = re.match(r"^(#{2,3})\s+§(\d+)\b(.*)$", line.strip())
        if m_sec:
            sec_headings.append((idx, int(m_sec.group(2)), line.strip()))

    sec_nums = [x[1] for x in sec_headings]
    log(f"  GOAL_THREE_TARGETS_20261018.md:")
    log(f"    bytes={os.path.getsize(goal_path)} | sha256={sha256_file(goal_path)} | lines={len(goal_lines)}")
    log(f"    total '## ' headings={len(h2_all)}")
    log(f"    total '##/### §N' numbered sections={len(sec_headings)} | unique §N={len(set(sec_nums))}")
    log(f"    first numbered section: L{sec_headings[0][0]} -> {sec_headings[0][2]}")
    log(f"    last 6 numbered sections:")
    for lno, snum, title in sec_headings[-6:]:
        log(f"      L{lno}: (§{snum}) {title}")

    atlas_dir = os.path.join(ROOT, "re_atlas")
    atlas_all_files = []
    atlas_clean_files = []
    for dp, dn, fn_list in os.walk(atlas_dir):
        for fn in sorted(fn_list):
            full = os.path.join(dp, fn)
            rel = os.path.relpath(full, ROOT)
            sz = os.path.getsize(full)
            sh = sha256_file(full)
            atlas_all_files.append((rel, sz, sh))
            if ".mimosa" not in rel and "__pycache__" not in rel:
                atlas_clean_files.append((rel, sz, sh))
    log(
        f"  re_atlas/ total files (all)={len(atlas_all_files)} ({sum(x[1] for x in atlas_all_files)} B) | "
        f"clean content files (excl .mimosa/__pycache__)={len(atlas_clean_files)} ({sum(x[1] for x in atlas_clean_files)} B)"
    )
    for rel, sz, sh in atlas_clean_files:
        log(f"    {rel} | size={sz} | sha256={sh}")

    out_log_path = os.path.join(OUT_DIR, "panel_forensics_stdout.txt")
    with open(out_log_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(buf.getvalue())
    print(f"Saved stdout to {out_log_path} (sha256={sha256_file(out_log_path)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
