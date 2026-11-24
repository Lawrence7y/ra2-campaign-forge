#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W80 CONFIG-KNOB TOOL -- the independent variable of this card.

Commands:
  pristine                 -> byte-copy + SHA-256 of EVERY knob config (pre-game)
  prep <trip> <condition>  -> restore ALL knob configs byte-wise from pristine,
                              delete game-generated .sav/.svg, apply ONE knob
                              edit (if condition != base), save PRE-EDIT bytes
                              + hashes, write CONFIG_PRE.json + tree_pre.json
  post <trip>              -> write CONFIG_POST.json + tree_post.json + DIFF.json
  restore_all              -> restore ALL knob configs byte-wise from pristine

CONDITIONS (each changes exactly ONE line of exactly ONE file vs `base`):
  base       : no edit (current signed-off config)
  e1_30      : ddraw.ini  [ddraw]  maxgameticks=0  -> 30
  e1_15      : ddraw.ini  [ddraw]  maxgameticks=0  -> 15
  e1_60      : ddraw.ini  [ddraw]  maxgameticks=0  -> 60
  e2_gs2     : RA2MD.INI  [Options] GameSpeed=1 -> 2
  e2_gs0     : RA2MD.INI  [Options] GameSpeed=1 -> 0
  e3_unlock  : ra2render.ini [Speed] UnlockGameSpeed=0 -> 1

Only files in KNOB_FILES are ever written by this tool; MAP_FILES are left
untouched (they are installed by w80_offline.py and are identical for the same
map across conditions).  All writes land inside W80_survive_mechanism.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w80_common as C
import w80_lib as L

# Config files that are pure knobs (never touched by a package install).
KNOB_FILES = (
    "ddraw.ini", "RA2MD.INI", "ra2.ini", "ra2render.ini", "ra2render.log",
    "ra2md.lcf", "Ra2.lcf", "yuri.lcf", "Register.ini",
    "BATTLEMD98.INI", "RA2MD.INI.benchbak",
    "ra2forge_uninstall.txt.pre-migrate.bak",
)
# Package-installed files (identical for the same map across all conditions).
MAP_FILES = (
    "BATTLEMD.INI", "BATTLEMD.INI.ra2forge.bak", "MAPSELMD.INI",
    "RA2F_M1.MAP", "expandmd98.mix", "ra2forge_install.json",
    "ra2forge_install.json.seal",
)
CONDITIONS = {
    "base":      None,
    "e1_30":     ("ddraw.ini",       "ddraw",   "maxgameticks",    "30"),
    "e1_15":     ("ddraw.ini",       "ddraw",   "maxgameticks",    "15"),
    "e1_60":     ("ddraw.ini",       "ddraw",   "maxgameticks",    "60"),
    "e2_gs2":    ("RA2MD.INI",       "Options", "GameSpeed",       "2"),
    "e2_gs2_all":("RA2MD.INI",       "*",       "GameSpeed=1",     "GameSpeed=2"),
    "e2_gs0":    ("RA2MD.INI",       "Options", "GameSpeed",       "0"),
    "e3_unlock": ("ra2render.ini",   "Speed",   "UnlockGameSpeed", "1"),
}


def sha(p: Path):
    return L.sha256_file(p) if p.is_file() else None


def write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str),
                 encoding="utf-8")


# --------------------------------------------------------------- ini edit
def edit_ini_one_line(path: Path, section: str, key: str, new_value: str):
    """Replace the value of `key` in ONE ini section, byte-preserving elsewhere.

    Returns (before_bytes, after_bytes, record).  Raises if the target line is
    not exactly one, or if any OTHER byte of the file changes.
    """
    before = path.read_bytes()
    nl = b"\r\n" if b"\r\n" in before else b"\n"
    lines = before.split(nl)
    cur = ""
    hits = []
    new_lines = []
    for ln in lines:
        s = ln.strip()
        if s.startswith(b"[") and s.endswith(b"]"):
            cur = s[1:-1].decode("latin-1").strip().lower()
        prefix = (key + "=").lower().encode("ascii")
        if cur == section.lower() and s.lower().startswith(prefix):
            hits.append(ln)
            new_lines.append(key.encode("ascii") + b"=" + new_value.encode("ascii"))
        else:
            new_lines.append(ln)
    if len(hits) != 1:
        raise RuntimeError("%s [%s] %s= : expected 1 line, found %d"
                           % (path.name, section, key, len(hits)))
    after = nl.join(new_lines)
    # prove ONLY that one line changed: rebuild and compare line-by-line
    diff_idx = [i for i, (a, b) in enumerate(zip(lines, new_lines)) if a != b]
    if len(diff_idx) != 1:
        raise RuntimeError("more than one line changed: %r" % diff_idx)
    path.write_bytes(after)
    rec = {
        "file": path.name, "section": section, "key": key,
        "before_line": hits[0].decode("latin-1"),
        "after_line": new_lines[diff_idx[0]].decode("latin-1"),
        "line_index": diff_idx[0], "newline": "CRLF" if nl == b"\r\n" else "LF",
        "before_sha256": hashlib.sha256(before).hexdigest(),
        "after_sha256": hashlib.sha256(after).hexdigest(),
        "before_size": len(before), "after_size": len(after),
        "bytes_changed_outside_line": False,
    }
    return before, after, rec


def edit_ini_all_lines(path: Path, old_line: str, new_line: str):
    """Coverage probe: replace EVERY exact `old_line` in the file (all sections).

    Still ONE knob (GameSpeed), applied uniformly to every section that holds
    the old value, so the effective section is guaranteed to be included.
    """
    before = path.read_bytes()
    nl = b"\r\n" if b"\r\n" in before else b"\n"
    lines = before.split(nl)
    ob = old_line.encode("ascii")
    nb = new_line.encode("ascii")
    hits = [i for i, ln in enumerate(lines) if ln.strip() == ob]
    if not hits:
        raise RuntimeError("%s: no exact line %r found" % (path.name, old_line))
    for i in hits:
        lines[i] = nb
    after = nl.join(lines)
    path.write_bytes(after)
    rec = {"file": path.name, "section": "*all*", "key": old_line,
           "before_line": old_line, "after_line": new_line,
           "line_indices": hits, "n_lines_changed": len(hits),
           "newline": "CRLF" if nl == b"\r\n" else "LF",
           "before_sha256": hashlib.sha256(before).hexdigest(),
           "after_sha256": hashlib.sha256(after).hexdigest(),
           "before_size": len(before), "after_size": len(after),
           "bytes_changed_outside_lines": False}
    return before, after, rec


# --------------------------------------------------------------- commands
def cmd_pristine():
    # Use a DEDICATED directory: out\pristine\ is owned by w80_offline.py
    # (its own 21 W79-style copies).  Sharing it would make restore_knobs()
    # resurrect files that were absent in the freshly-installed sandbox.
    pdir = C.OUT / "knob_pristine"
    pdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for n in KNOB_FILES:
        src = C.GAME / n
        if src.is_file():
            dst = pdir / n
            dst.write_bytes(src.read_bytes())
            rows.append({"file": n, "present": True, "size": dst.stat().st_size,
                         "sha256": sha(dst)})
        else:
            rows.append({"file": n, "present": False, "size": None, "sha256": None})
    write_json(C.OUT / "CONFIG_PRISTINE.json",
               {"game": str(C.GAME), "knob_files": list(KNOB_FILES), "rows": rows})
    print(json.dumps({"cmd": "pristine", "n_present": sum(r["present"] for r in rows)},
                     ensure_ascii=False))
    return 0


def restore_knobs():
    rows = []
    for n in KNOB_FILES:
        src = C.OUT / "knob_pristine" / n
        dst = C.GAME / n
        if src.is_file():
            dst.write_bytes(src.read_bytes())
            rows.append({"file": n, "restored": True,
                         "byte_identical": dst.read_bytes() == src.read_bytes(),
                         "sha256": sha(dst)})
        else:
            if dst.exists():
                dst.unlink()
            rows.append({"file": n, "restored": True, "absent_baseline": True})
    return rows


def config_hashes():
    out = {}
    for n in KNOB_FILES + MAP_FILES:
        p = C.GAME / n
        out[n] = {"present": p.is_file(),
                  "size": p.stat().st_size if p.is_file() else None,
                  "sha256": sha(p)}
    return out


def cmd_prep(trip: str, condition: str):
    if condition not in CONDITIONS:
        raise SystemExit("unknown condition %r; choices=%r"
                         % (condition, sorted(CONDITIONS)))
    tdir = C.OUT / trip
    tdir.mkdir(parents=True, exist_ok=True)
    rec = {"trip": trip, "condition": condition, "game": str(C.GAME)}

    # (1) byte-wise restore of ALL knob configs (undoes any game self-write)
    rec["knob_restore"] = restore_knobs()

    # (2) remove game-generated save files (W79: only RA2F_M1.sav ever appears)
    removed = []
    for pat in ("*.sav", "*.svg"):
        for p in sorted(C.GAME.glob(pat)):
            removed.append({"file": p.name, "size": p.stat().st_size,
                            "sha256": sha(p)})
            p.unlink()
    rec["game_generated_removed"] = removed

    # (3) save PRE-EDIT byte copy + hash of the file we are about to change
    edit = CONDITIONS[condition]
    if edit:
        fname = edit[0]
        src = C.GAME / fname
        before_dir = tdir / "config_before"
        before_dir.mkdir(parents=True, exist_ok=True)
        (before_dir / fname).write_bytes(src.read_bytes())
        rec["pre_edit_copy"] = {"file": fname, "path": str(before_dir / fname),
                                "sha256": sha(before_dir / fname),
                                "size": src.stat().st_size}

    # (4) apply the ONE knob edit
    if edit:
        fname, section, key, val = edit
        vdir = C.OUT / "config_variants"
        vdir.mkdir(parents=True, exist_ok=True)
        if section == "*":
            before, after, erec = edit_ini_all_lines(
                C.GAME / fname, key, val)
        else:
            before, after, erec = edit_ini_one_line(
                C.GAME / fname, section, key, val)
        rec["edit"] = erec
        (vdir / ("%s_%s" % (trip, fname))).write_bytes(after)
        rec["post_edit_copy"] = {"path": str(vdir / ("%s_%s" % (trip, fname))),
                                 "sha256": hashlib.sha256(after).hexdigest()}
    else:
        rec["edit"] = None

    # (5) config hashes + diff vs pristine
    ch = config_hashes()
    pristine = json.loads((C.OUT / "CONFIG_PRISTINE.json").read_text(encoding="utf-8"))
    pmap = {r["file"]: r for r in pristine["rows"]}
    rec["config_pre"] = ch
    # Only KNOB_FILES are expected to equal their byte-pristine copies;
    # MAP_FILES are install artifacts and differ from the real-dir baseline.
    rec["config_diff_vs_pristine"] = sorted(
        n for n in KNOB_FILES
        if (ch[n]["sha256"] or "") != (pmap.get(n, {}).get("sha256") or ""))
    rec["map_files"] = {n: ch[n] for n in MAP_FILES}
    # full-tree manifest (content hashes of all 647 files)
    tp = C.write_manifest(tdir / "tree_pre.json", C.GAME)
    rec["tree_pre_summary"] = tp["summary"]
    write_json(tdir / "CONFIG_PRE.json", rec)
    print(json.dumps({"cmd": "prep", "trip": trip, "condition": condition,
                      "edit": rec["edit"],
                      "config_diff_vs_pristine": rec["config_diff_vs_pristine"]},
                     ensure_ascii=False))
    return 0


def cmd_post(trip: str):
    tdir = C.OUT / trip
    pre = json.loads((tdir / "CONFIG_PRE.json").read_text(encoding="utf-8"))
    ch = config_hashes()
    tp = C.write_manifest(tdir / "tree_post.json", C.GAME)
    pre_tree = json.loads((tdir / "tree_pre.json").read_text(encoding="utf-8"))
    d = C.diff_manifests(pre_tree, tp)
    changed_cfg = sorted(n for n in KNOB_FILES + MAP_FILES
                         if (pre["config_pre"][n]["sha256"] or "")
                         != (ch[n]["sha256"] or ""))
    rec = {"trip": trip, "config_post": ch, "config_changed": changed_cfg,
           "tree_post_summary": tp["summary"], "tree_diff": d}
    write_json(tdir / "DIFF.json", rec)
    print(json.dumps({"cmd": "post", "trip": trip,
                      "config_changed": changed_cfg,
                      "tree_added": d["added"], "tree_removed": d["removed"],
                      "tree_changed": d["changed"]}, ensure_ascii=False))
    return 0


def cmd_restore_all():
    rows = restore_knobs()
    write_json(C.OUT / "CONFIG_RESTORE_ALL.json", {"rows": rows})
    bad = [r for r in rows if not (r.get("byte_identical") or r.get("absent_baseline"))]
    print(json.dumps({"cmd": "restore_all", "n": len(rows), "bad": bad},
                     ensure_ascii=False))
    return 1 if bad else 0


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    if a[0] == "pristine":
        return cmd_pristine()
    if a[0] == "prep" and len(a) >= 3:
        return cmd_prep(a[1], a[2])
    if a[0] == "post" and len(a) >= 2:
        return cmd_post(a[1])
    if a[0] == "restore_all":
        return cmd_restore_all()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
