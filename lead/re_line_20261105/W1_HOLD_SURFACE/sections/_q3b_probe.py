# -*- coding: utf-8 -*-
"""Q3b probe -- full census of [Actions] sections in ra2youli/ maps.

Run:
    python -I -X utf8 D:/Project/ra2-campaign-forge/lead/re_line_20261105/W1_HOLD_SURFACE/sections/_q3b_probe.py
    (stdout is redirected to _q3b_probe_out.txt by the caller)

Zero game interaction. Read-only over ra2youli/ and the trip tree.

[Actions] record layout (ra2forge/triggers.py:19-20, ra2forge/maplib.py:463-472):
    ID=COUNT,(CODE,P1..P6,P7)*        -> 1 + COUNT*8 comma-separated tokens
    The FIRST token is the number of actions in that record, NOT an action kind.
    Each of the COUNT 8-token groups begins with the action kind (CODE).
    P7 is 'A' when unused. P-parameters may be non-numeric (text, hex IDs).
So this probe computes BOTH histograms:
    (a) count_hist  -- histogram of the COUNT field (this is what the leader's
                       precheck reported as "kinds"; see report section 5)
    (b) kind_hist   -- histogram of actual action kinds (the deliverable)

Also emits:
    - per-file rows (n_records / n_actions / kind_hist / has110 / has127)
    - a loose cross-check: any bare '110'/'127' token anywhere in an [Actions] value
    - the sha256 -> physical-file mapping for all distinct map_sha256 values
      appearing in measure_w*.json under the qc161_u0400_trip tree
"""

import collections
import hashlib
import json
import os
import re
import sys

MAP_ROOT = r"D:\Project\ra2-campaign-forge\ra2youli"
TRIP_ROOT = (r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
             r"\CONTINUE_20261003\lead\qc161_u0400_trip")
EXTS = {".yrm", ".map", ".mmx"}
HDR = re.compile(r"^\s*\[Actions\]\s*$", re.I)
SECTION = re.compile(r"^\s*\[[^\]]+\]\s*$")
MEASURE = re.compile(r"measure_w\d*\.json")


def out(*a):
    print(*a)


def list_maps():
    fs = []
    for dp, dn, fn in os.walk(MAP_ROOT):
        for f in fn:
            if os.path.splitext(f)[1].lower() in EXTS:
                fs.append(os.path.join(dp, f))
    return sorted(fs)


def parse_actions(path):
    """Return (have_section, n_sections, records, kind_hist, count_hist,
               malformed, loose_hits)."""
    txt = open(path, "rb").read().decode("latin-1")
    insec = False
    have = False
    n_sections = 0
    records = 0
    kind_hist = collections.Counter()
    count_hist = collections.Counter()
    malformed = []
    loose_hits = []
    for lineno, ln in enumerate(txt.splitlines(), 1):
        if HDR.match(ln):
            insec = True
            have = True
            n_sections += 1
            continue
        if insec and SECTION.match(ln):
            insec = False
            continue
        if not insec:
            continue
        s = ln.strip()
        if not s or s.startswith(";") or "=" not in s:
            continue
        key, val = s.split("=", 1)
        toks = [x.strip() for x in val.split(",")]
        records += 1
        try:
            n = int(toks[0])
        except (ValueError, IndexError):
            malformed.append((lineno, "BAD_COUNT", s[:100]))
            continue
        count_hist[n] += 1
        rest = toks[1:]
        if len(rest) != n * 8:
            malformed.append((lineno, "LEN", n, len(rest), s[:100]))
        for i in range(min(n, len(rest) // 8)):
            try:
                k = int(rest[8 * i])
            except ValueError:
                malformed.append((lineno, "BAD_KIND", s[:100]))
                continue
            kind_hist[k] += 1
        # independent, layout-agnostic cross-check
        for t in rest:
            if t == "110" or t == "127":
                loose_hits.append((lineno, t, s[:100]))
    return (have, n_sections, records, kind_hist, count_hist,
            malformed, loose_hits)


def fmt_hist(h):
    return "{" + ", ".join("%d:%d" % (k, v) for k, v in sorted(h.items())) + "}"


def main():
    out("=== Q3b PROBE / full census ===")
    out("MAP_ROOT =", MAP_ROOT)
    out("EXTS =", sorted(EXTS))
    files = list_maps()
    out("n_files =", len(files))
    by_ext = collections.Counter(os.path.splitext(p)[1].lower() for p in files)
    out("by_ext =", dict(sorted(by_ext.items())))

    rows = []
    global_hist = collections.Counter()
    n_with = n_without = n_records = n_actions = 0
    all_malformed = []
    all_loose = []
    has110 = []
    has127 = []
    multi = []
    for p in files:
        name = os.path.basename(p)
        rel = os.path.relpath(p, MAP_ROOT)
        (have, nsec, recs, kh, ch, mal, loose) = parse_actions(p)
        if have:
            n_with += 1
        else:
            n_without += 1
        if nsec > 1:
            multi.append((rel, nsec))
        n_records += recs
        n_actions += sum(kh.values())
        global_hist.update(kh)
        for m in mal:
            all_malformed.append((rel,) + tuple(m))
        for l in loose:
            all_loose.append((rel,) + tuple(l))
        if kh.get(110):
            has110.append((rel, kh[110]))
        if kh.get(127):
            has127.append((rel, kh[127]))
        rows.append((rel, have, nsec, recs, sum(kh.values()), ch, kh))

    out("files_with_[Actions] =", n_with)
    out("files_without_[Actions] =", n_without)
    out("n_[Actions]_sections =", sum(r[2] for r in rows))
    out("multi_section_files =", len(multi), multi[:20])
    out("n_records =", n_records)
    out("n_actions =", n_actions)
    out("malformed_records =", len(all_malformed))
    for x in all_malformed[:40]:
        out("  MAL", x)
    out("loose_110_127_tokens_in_[Actions]_values =", len(all_loose))
    for x in all_loose[:40]:
        out("  LOOSE", x)
    out("distinct_action_kinds =", len(global_hist))
    out("GLOBAL_KIND_HIST =", fmt_hist(global_hist))
    out("FILES_WITH_110 =", len(has110), has110)
    out("FILES_WITH_127 =", len(has127), has127)

    out("")
    out("=== PER-FILE TABLE (TSV) ===")
    out("relpath\thas_actions\tn_sections\tn_records\tn_actions\tcount_hist\tkind_hist\thas110\thas127")
    for rel, have, nsec, recs, na, ch, kh in rows:
        out("%s\t%s\t%d\t%d\t%d\t%s\t%s\t%s\t%s" % (
            rel, "Y" if have else "N", nsec, recs, na,
            fmt_hist(ch), fmt_hist(kh),
            "Y" if kh.get(110) else "N",
            "Y" if kh.get(127) else "N"))

    out("")
    out("=== LEADER 8-MAP CROSS-CHECK ===")
    leader = [
        "[2]0LoadBench_U0050.yrm", "[2]0LoadBench_U0100.yrm",
        "[2]0LoadBench_U0200.yrm", "[2]0LoadBench_U0400.yrm",
        "[2]0LoadBench_U0800.yrm", "ECH01.MAP", "ECH02.MAP", "ECH03.MAP",
    ]
    by_name = {os.path.basename(p): r for p, r in zip(files, rows)}
    for n in leader:
        r = by_name.get(n)
        if r is None:
            out("MISSING", n)
            continue
        rel, have, nsec, recs, na, ch, kh = r
        out("%s\thave=%s\tcount_hist=%s\treal_kind_hist=%s\thas110=%s\thas127=%s" % (
            n, have, fmt_hist(ch), fmt_hist(kh),
            "Y" if kh.get(110) else "N", "Y" if kh.get(127) else "N"))

    # ---- sha -> physical file mapping ----
    out("")
    out("=== MAP_SHA -> PHYSICAL FILE ===")
    shas = {}                       # full sha -> 8-char prefix
    usage = collections.Counter()  # prefix -> n measure_w files
    n_measure = 0
    sample = {}
    for dp, dn, fn in os.walk(TRIP_ROOT):
        for f in fn:
            if not MEASURE.fullmatch(f):
                continue
            p = os.path.join(dp, f)
            n_measure += 1
            try:
                d = json.load(open(p, encoding="utf-8", errors="replace"))
            except Exception as e:
                out("  JSON_ERR", os.path.relpath(p, TRIP_ROOT), repr(e))
                continue
            for k, v in d.items():
                if "map" in k.lower() and "sha" in k.lower() and isinstance(v, str):
                    shas[v] = v[:8]
                    usage[v[:8]] += 1
                    sample.setdefault(v[:8], os.path.relpath(p, TRIP_ROOT))
    out("n_measure_w_files_under_trip_root =", n_measure)
    out("distinct_map_sha256 =", len(shas))

    # Hash every candidate physical map under the trip root (bounded: trip root only)
    by_hash = collections.defaultdict(list)
    n_cand = 0
    for dp, dn, fn in os.walk(TRIP_ROOT):
        for f in fn:
            low = f.lower()
            if "xmp29u2" in low or low.endswith((".map", ".yrm")):
                p = os.path.join(dp, f)
                if not os.path.isfile(p):
                    continue
                n_cand += 1
                h = hashlib.sha256(open(p, "rb").read()).hexdigest()
                by_hash[h].append(os.path.relpath(p, TRIP_ROOT))
    out("n_candidate_physical_files_hashed =", n_cand)

    out("prefix\tfull_sha256\tn_measures\tsample_measure_w\tstatus\tphysical_paths\thas_[Actions]_and_kinds")
    for full, pre in sorted(shas.items(), key=lambda x: x[1]):
        paths = sorted(by_hash.get(full, []))
        if not paths:
            out("%s\t%s\t%d\t%s\t找不到\t\t" % (
                pre, full, usage[pre], sample.get(pre, "")))
            continue
        # parse [Actions] on the first physical hit, for information
        first = os.path.join(TRIP_ROOT, paths[0].replace("\\", os.sep))
        try:
            (hv, ns, rc, kh, ch, ml, lo) = parse_actions(first)
            act_desc = "have=%s kinds=%s has110=%s has127=%s" % (
                hv, fmt_hist(kh), "Y" if kh.get(110) else "N",
                "Y" if kh.get(127) else "N")
        except Exception as e:
            act_desc = "parse_error=" + repr(e)
        out("%s\t%s\t%d\t%s\tFOUND\t%s\t%s" % (
            pre, full, usage[pre], sample.get(pre, ""),
            " ; ".join(paths[:4]) + (" ...(total %d)" % len(paths) if len(paths) > 4 else ""),
            act_desc))

    # Are any measurement shas present in ra2youli/ itself?
    out("")
    out("=== MEASUREMENT SHAS PRESENT UNDER ra2youli/? ===")
    hit = []
    for p in files:
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if h in shas:
            hit.append((os.path.relpath(p, MAP_ROOT), h[:8]))
    out("matches =", len(hit), hit)

    out("")
    out("=== END ===")


if __name__ == "__main__":
    main()
