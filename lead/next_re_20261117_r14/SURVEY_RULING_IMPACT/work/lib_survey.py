# -*- coding: utf-8 -*-
"""SURVEY-RULING-IMPACT shared library.

Own recomputation from on-disk raw tables. No value is copied from any card,
PANEL or COMMON: every number used in the deliverable is produced here.

Denominator discipline (R14_COMMON 9.1):
  A = 12,916 = data rows of function_atlas.tsv (lower bound; DoD clause-1 literal denominator)
  B = 14,487 = business-entry view (coverage minus 3,944 _initterm thunks)   <- not used for % here
  C = 18,431 = all-entry view (= coverage.tsv data rows)
Per-subsystem named%/proved% always use A.

Thresholds are computed here, never quoted:
  named  threshold = ceil(0.9 * n)
  proved threshold = ceil(0.5 * n)
"""
import os
import re
import math
import collections

ROOT = r"D:\Project\ra2-campaign-forge"
COVERAGE = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
PANEL = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\PANEL.md")
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
OUT = os.path.join(ROOT, r"lead\next_re_20261117_r14\SURVEY_RULING_IMPACT")
EV = os.path.join(OUT, "EVIDENCE")
WORK = os.path.join(OUT, "work")

G_PROVED = "[\u5df2\u8bc1]"          # [已证]
G_STATIC = "[\u9759\u6001\u63a8\u65ad]"  # [静态推断]
G_UNPROV = "[\u672a\u8bc1]"          # [未证]

SUBS_ALL = ["S%02d" % i for i in range(1, 23)]
SUBS_21 = [s for s in SUBS_ALL if s != "S22"]   # S22 excluded from % by 9.1


def ceil90(n):
    return int(math.ceil(0.9 * n - 1e-12))


def ceil50(n):
    return int(math.ceil(0.5 * n - 1e-12))


def load_coverage():
    """Return list of dicts. Header is comma-separated; data rows are TAB, 8 cols.
    Column 5 (idx 4) is grade - read-only use."""
    rows = []
    with open(COVERAGE, encoding="utf-8", errors="replace") as f:
        hdr = f.readline()
        assert hdr.startswith("entry,"), "unexpected coverage header: %r" % hdr[:40]
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            if not line.strip():
                continue
            p = line.split("\t")
            if len(p) != 8:
                raise SystemExit("bad field count %d for %r" % (len(p), p[0]))
            rows.append({
                "entry": p[0].strip().upper(),
                "sub": p[1].strip(),
                "name": p[2],
                "sem": p[3],
                "grade": p[4].strip(),
                "ev": p[5],
                "nsrc": p[6],
                "conflict": p[7].strip(),
            })
    return rows


def load_atlas_entries():
    """Atlas entry set + per-entry size/n_callers (only used where explicitly noted;
    the 4-ring channel in p6 does NOT use atlas entry+size)."""
    ents = []
    meta = {}
    with open(ATLAS, encoding="utf-8", errors="replace") as f:
        f.readline()
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            if not line.strip():
                continue
            p = line.split("\t")
            e = p[0].strip().upper()
            ents.append(e)
            try:
                meta[e] = {"size": int(p[1]), "n_instr": int(p[2]),
                           "n_callers": int(p[3]), "n_callees": int(p[4])}
            except (ValueError, IndexError):
                meta[e] = {"size": None, "n_instr": None, "n_callers": None, "n_callees": None}
    return ents, meta


# ---- name classification -------------------------------------------------
RE_SLOT = re.compile(r"::v?slot\d+$")
# `Class::sub_XXXXXXXX` self-invented placeholder. NOTE: the on-disk form drops
# leading zeros (`AudioController::sub_4060F0`, 6 hex digits), so the digit run
# must NOT be pinned to 8 - that defect silently returned 0 hits on first run.
RE_CLASSSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")


def named_L(name):
    """L reading (R14-R14 panel): non-empty and does not start with sub_."""
    n = name.strip()
    return bool(n) and not n.startswith("sub_")


def is_clas_sub(name):
    """`Class::sub_XXXXXXXX` self-invented placeholder (hex run of any length)."""
    return bool(RE_CLASSSUB.search(name.strip()))


def named_S_r14(name):
    """S(R14): L minus `Class::sub_XXXXXXXX` (slotN still counted)."""
    return named_L(name) and not is_clas_sub(name)


def named_S_strict(name):
    """S(strict): S(R14) minus `Class::slotN` / `::vslotN` (8.1 error-source 13)."""
    n = name.strip()
    if not named_S_r14(n):
        return False
    return not RE_SLOT.search(n)


def is_template_instance(name):
    """Container/template instantiation name marker, as used by a-S13-K4:
    mangled template names look like  ?$VectorClass::PAVBombClass:::
    i.e. contain '?$' (template name marker) or '::?$'."""
    return "?$" in name


def is_slot_named(name):
    return bool(RE_SLOT.search(name.strip()))


def subsystem_stats(rows, atlas_set):
    """Per-subsystem A-denominator stats over coverage intersect atlas (upper entry)."""
    st = collections.defaultdict(lambda: {
        "atlas_n": 0, "named_L": 0, "named_S": 0, "named_strict": 0,
        "proved": 0, "static": 0, "unproved": 0, "rows": []})
    for r in rows:
        if r["entry"] not in atlas_set:
            continue
        s = st[r["sub"]]
        s["atlas_n"] += 1
        s["rows"].append(r)
        if named_L(r["name"]):
            s["named_L"] += 1
            if named_S_r14(r["name"]):
                s["named_S"] += 1
                if named_S_strict(r["name"]):
                    s["named_strict"] += 1
        if r["grade"] == G_PROVED:
            s["proved"] += 1
        elif r["grade"] == G_STATIC:
            s["static"] += 1
        elif r["grade"] == G_UNPROV:
            s["unproved"] += 1
    return st


def verdict(n, named, proved):
    """DoD clause 1 (named_S) and clause 2 (proved) both must pass."""
    if n == 0:
        return (False, False, 0, 0)
    tn, tp = ceil90(n), ceil50(n)
    return (named >= tn, proved >= tp, tn, tp)


def passing(st, named_key="named_S", proved_key="proved"):
    out = []
    for s in SUBS_ALL:
        if s not in st:
            continue
        d = st[s]
        n = d["atlas_n"]
        if n == 0:
            continue
        named = d[named_key] + d.get("_override_named_delta_" + named_key, 0) if False else d[named_key]
        ok_n, ok_p, tn, tp = verdict(n, named, d[proved_key])
        if ok_n and ok_p:
            out.append(s)
    return out


def w(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def wl(path, lines):
    w(path, "\n".join(lines) + "\n")
