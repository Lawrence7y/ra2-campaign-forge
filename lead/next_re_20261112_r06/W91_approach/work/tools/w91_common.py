#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W91 shared helpers - paths, command capture, full-tree manifest, diff,
byte-pristine restore.  CARD COPY (derived from W90 common, re-pointed to W91_approach).  Uses w90_lib's Sink + sha256_file.  Never import another
card's script.  PKG is per-STEP (work/pkg_<step>/W88Probe, byte-identical
copies of the W88 built packages); each trip installs exactly one package.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import w91_lib as L

ROOT = Path(r"D:\Project\ra2-campaign-forge")
RUN = ROOT / "lead" / "next_re_20261112_r06"
CARD = RUN / "W91_approach"
OUT = CARD / "out"
WORK = CARD / "work"
TOOLS = WORK / "tools"
GAME = OUT / "sandbox_game"
REAL = ROOT / "ra2youli"
LOCK = RUN / ".game_instance.lock"
V15 = (ROOT / "lead" / "next_re_20261112_r02" / "W60_battlemd_inplace"
       / "ra2forge_patched_v15")   # 工具链本体在 r02，只读使用

FEATURE_SET = WORK / "w91_feature_set.json"


def pkg_path(step: str) -> Path:
    """Built package dir for one step (W88Probe folder emitted by ra2forge)."""
    return WORK / ("pkg_" + step) / "W88Probe"


def design_path(step: str) -> Path:
    return WORK / ("w91_design_%s.json" % step)


PYEXE = r"C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"

# W44 signed-off real-dir baseline (LEAD_VERDICT_C_line_E2E.md section 3).
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
# Sandbox writable config files: byte-copy + hash BEFORE any write, restore at
# the end with a real SHA self-proof.
PRISTINE = (
    "BATTLEMD.INI", "BATTLEMD98.INI", "RA2MD.INI", "RA2MD.INI.benchbak",
    "ddraw.ini", "gamemd.exe", "ddraw.dll", "ra2md.lcf",
    "expandmd98.mix", "expandmd98.mix.old-pre-migrate",
    "ra2forge_install.json", "ra2forge_install.json.seal",
    "ra2forge_uninstall.txt.pre-migrate.bak",
    "BATTLEMD.INI.ra2forge.bak", "expandmd98.mix.ra2forge.bak",
    "ECH01.MAP", "ECH02.MAP", "ECH03.MAP",
    "ECH01.MAP.ra2forge.bak", "ECH02.MAP.ra2forge.bak",
    "ECH03.MAP.ra2forge.bak",
)


def env_utf8():
    e = dict(os.environ)
    e["PYTHONIOENCODING"] = "utf-8"
    e["PYTHONUTF8"] = "1"
    return e


def run_cmd(sink, label, argv, cwd=None, timeout=420, env=None):
    rec = {"label": label, "argv": [str(a) for a in argv],
           "cwd": str(cwd) if cwd else None}
    try:
        r = subprocess.run([str(a) for a in argv],
                           cwd=str(cwd) if cwd else None,
                           capture_output=True, text=True,
                           timeout=timeout, env=env or env_utf8())
        rec.update(stdout_tail=r.stdout[-16000:], stderr_tail=r.stderr[-8000:],
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


def v15_cmd(sink, label, args, timeout=420):
    return run_cmd(sink, label,
                   [PYEXE, "-B", "-X", "utf8", "-m", "ra2forge"] + args,
                   cwd=V15, timeout=timeout)


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


def save_pristine(sink, root: Path = None):
    root = root or GAME
    rows = []
    pdir = OUT / "pristine"
    pdir.mkdir(parents=True, exist_ok=True)
    for name in PRISTINE:
        src = root / name
        if src.is_file():
            dst = pdir / name
            dst.write_bytes(src.read_bytes())
            rows.append({"file": name, "sha256": L.sha256_file(dst),
                         "size": dst.stat().st_size, "present": True})
        else:
            rows.append({"file": name, "sha256": None, "present": False})
    sink.step("pristine_saved", rows=rows, n_present=sum(1 for r in rows if r["present"]))
    return rows


def restore_one(name: str, sink, label=None, root: Path = None):
    root = root or GAME
    src = OUT / "pristine" / name
    dst = root / name
    if not src.is_file():
        if dst.is_file():
            dst.unlink()
        sink.step("restore_one", file=name, action="removed_absent_baseline", label=label)
        return {"file": name, "restored": not dst.exists(), "absent_baseline": True}
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    ok = dst.read_bytes() == src.read_bytes()
    sink.step("restore_one", file=name, sha256=L.sha256_file(dst),
              expected=L.sha256_file(src), byte_identical=ok, label=label)
    return {"file": name, "sha256": L.sha256_file(dst), "byte_identical": ok,
            "present_baseline": True}


def lock_read() -> str:
    return LOCK.read_text(encoding="utf-8", errors="replace") if LOCK.is_file() else "<absent>"


def lock_owner() -> str:
    for ln in lock_read().splitlines():
        if ln.startswith("owner="):
            return ln.split("=", 1)[1].strip()
    return ""


def lock_claim_w91(purpose: str):
    L.lock_claim("w91", purpose)


def lock_release(purpose: str):
    L.lock_claim("lead", purpose)

