#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W44 shared helpers: paths, command capture, full-tree manifest, diff.

All phases import this; it reuses w44_lib's Sink (NDJSON) and sha256_file.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import w44_lib as L

ROOT = Path(r"D:\Project\ra2-campaign-forge")
RUN = ROOT / "lead" / "next_re_20261112_r02"
W44 = RUN / "W44_c_line_e2e"
OUT = W44 / "out"
GAME = W44 / "sandbox_game"
REAL = ROOT / "ra2youli"
V12 = RUN / "W41_csf_install" / "ra2forge_patched_v12"
DESIGN = W44 / "designs" / "w44_two_missions.json"
PKG_OUT = OUT / "pkg"
PKG = PKG_OUT / "W27 Live Campaign"
CSF_WORK = OUT / "csf_work" / "ra2md.csf"
CSF_BASE = RUN / "W40_csf_live" / "out" / "official_ra2md.csf"
OFFICIAL_CSF_SHA = "1b90bb0756137f46ff529af043fe798d7f1f9fa1713a4110f17e1d674de81f1c"
OFFICIAL_CSF_SIZE = 332973
OFFICIAL_MAPSEL_SHA = "074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52"
OFFICIAL_MAPSEL_SIZE = 5573
W39_APPENDED_MAPSEL_SHA = "11cc1cacb0e0d49d71ddc13b94179fa3c7ebe90c9048be2e076453b8684b0886"
W39_APPENDED_MAPSEL_SIZE = 6108
CSF_TEXT = "W44_C_LINE_CSF_DESC_VISIBLE_20261113"

BASELINE = {
    "file_count": 647,
    "total_bytes": 1989215270,
    "maplike_count": 277,
    "RA2MD.INI": "c91c6a47",
    "gamemd.exe": "73201cc0",
    "ddraw.dll": "85e0f7d5",
    "ra2forge_install.json": "fe3bdf62",
}
MAPLIKE_EXT = {".yrm", ".mpr", ".map"}
PRISTINE = ("RA2MD.INI", "ddraw.ini", "RA2MD.INI.benchbak",
            "gamemd.exe", "ddraw.dll", "BATTLEMD.INI",
            "ra2forge_install.json")


def env_utf8():
    e = dict(os.environ)
    e["PYTHONIOENCODING"] = "utf-8"
    e["PYTHONUTF8"] = "1"
    return e


def run_cmd(sink, label, argv, cwd=None, timeout=420, env=None):
    """Run a command, capture everything, write a full log + an NDJSON record."""
    rec = {"label": label, "argv": [str(a) for a in argv],
           "cwd": str(cwd) if cwd else None}
    try:
        r = subprocess.run([str(a) for a in argv],
                           cwd=str(cwd) if cwd else None,
                           capture_output=True, text=True,
                           timeout=timeout, env=env or env_utf8())
        rec.update(stdout_tail=r.stdout[-12000:], stderr_tail=r.stderr[-6000:],
                   exit_code=r.returncode)
    except Exception as e:
        rec.update(exit_code=-999, error=repr(e), stdout_tail="", stderr_tail="")
    log = OUT / ("cmd_%s.log" % label)
    with log.open("w", encoding="utf-8", errors="replace") as f:
        f.write("ARGV: %s\nCWD: %s\nEXIT: %s\n\n--- STDOUT ---\n%s\n\n--- STDERR ---\n%s\n"
                % (json.dumps(rec["argv"], ensure_ascii=False), rec["cwd"],
                   rec["exit_code"], rec["stdout_tail"], rec["stderr_tail"]))
    rec["log"] = str(log)
    sink.step("cmd_" + label, **rec)
    return rec


def v12_cmd(sink, label, args, timeout=420):
    """python -m ra2forge <args> with V12 as cwd (package root on sys.path)."""
    return run_cmd(sink, label, ["python", "-B", "-X", "utf8", "-m", "ra2forge"] + args,
                   cwd=V12, timeout=timeout)


def manifest(root: Path):
    rows = []
    for p in sorted(root.rglob("*"), key=lambda x: x.as_posix().lower()):
        if p.is_file():
            st = p.stat()
            rows.append({"rel": p.relative_to(root).as_posix(),
                         "size": st.st_size,
                         "mtime_ns": st.st_mtime_ns,
                         "sha256": L.sha256_file(p)})
    return rows


def summary(rows, root: Path):
    d = {"file_count": len(rows),
         "total_bytes": sum(r["size"] for r in rows),
         "maplike_count": sum(1 for r in rows
                              if Path(r["rel"]).suffix.lower() in MAPLIKE_EXT),
         "hashes": {}}
    for name in BASELINE:
        if name in ("file_count", "total_bytes", "maplike_count"):
            continue
        p = root / name
        d["hashes"][name] = L.sha256_file(p) if p.is_file() else None
    return d


def write_manifest(path: Path, root: Path):
    rows = manifest(root)
    payload = {"root": str(root), "summary": summary(rows, root), "files": rows}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return payload


def diff_manifests(a: dict, b: dict):
    """Compare by (rel, size, sha256). mtime is reported separately."""
    am = {r["rel"]: r for r in a["files"]}
    bm = {r["rel"]: r for r in b["files"]}
    added = sorted(set(bm) - set(am))
    removed = sorted(set(am) - set(bm))
    changed = sorted(k for k in (set(am) & set(bm))
                     if am[k]["size"] != bm[k]["size"]
                     or am[k]["sha256"] != bm[k]["sha256"])
    mtime_diff = sorted(k for k in (set(am) & set(bm))
                        if am[k]["mtime_ns"] != bm[k]["mtime_ns"])
    return {"added": added, "removed": removed, "changed": changed,
            "mtime_diff": mtime_diff,
            "identical_tree": not (added or removed or changed),
            "pre_summary": a["summary"], "post_summary": b["summary"]}


def save_pristine(sink):
    """Byte-exact restore targets for the finally self-heal."""
    rows = []
    for name in PRISTINE:
        src = GAME / name
        if src.is_file():
            dst = OUT / ("pristine_" + name)
            dst.write_bytes(src.read_bytes())
            rows.append({"file": name, "sha256": L.sha256_file(dst),
                         "size": dst.stat().st_size})
        else:
            rows.append({"file": name, "sha256": None, "absent": True})
    sink.step("pristine_saved", rows=rows)
    return rows


def restore_one(name: str, sink, label=None):
    src = OUT / ("pristine_" + name)
    dst = GAME / name
    if not src.is_file():
        if dst.is_file():
            dst.unlink()
        sink.step("restore_one", file=name, action="removed_absent_baseline",
                  label=label)
        return {"file": name, "restored": not dst.exists()}
    dst.write_bytes(src.read_bytes())
    ok = dst.read_bytes() == src.read_bytes()
    sink.step("restore_one", file=name, sha256=L.sha256_file(dst),
              expected=L.sha256_file(src), byte_identical=ok, label=label)
    return {"file": name, "sha256": L.sha256_file(dst), "byte_identical": ok}


def heal(sink, label="heal", remove_drops=()):
    """finally self-heal: residual 0, byte-restore configs, remove manual drops."""
    residual = L.list_gamemd()
    sink.step("heal_residual_before", label=label, gamemd_processes=residual)
    rows = []
    for n in ("RA2MD.INI", "ddraw.ini", "RA2MD.INI.benchbak", "BATTLEMD.INI"):
        try:
            rows.append(restore_one(n, sink, label=label))
        except Exception as e:
            sink.step("heal_restore_error", file=n, error=repr(e), label=label)
    drops = []
    for n in remove_drops:
        p = GAME / n
        if p.is_file():
            p.unlink()
            drops.append({"file": n, "removed": True})
        else:
            drops.append({"file": n, "removed": False, "absent": True})
    after = L.list_gamemd()
    sink.step("heal_done", label=label, rows=rows, drops=drops,
              gamemd_residual_before=residual, gamemd_residual_after=after,
              residual_zero=(len(after) == 0))
    return {"rows": rows, "drops": drops, "residual": after}
