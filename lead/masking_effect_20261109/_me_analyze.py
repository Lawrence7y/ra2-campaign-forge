# -*- coding: utf-8 -*-
"""_me_analyze.py — Steps 1(b,c,d), 2(a-d): independent corpus line-set
quantification, four-gate mechanism trace, and reverse-masking construction.

Read-only on every path outside this write domain. Imports the UNMODIFIED
_rs_carrier_scan.py via importlib (no modification, no write) to reuse its
classify_line / blocks_of / quoted_containing as the ground truth of the
scanner's own logic. All experiments are driven from THIS script.

Corpus definition: identical to the scanner under
  --root lead --ext .md --max-depth 2
i.e. iter_files(root, ['.md'], 2), skip files containing NUL, decode utf-8
with 'replace'. Line unit = occurrence(file, line), same as scanner R2.
"""
import os, io, sys, re, json, hashlib, importlib.util
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LEAD = os.path.join(ROOT, "lead")
SCANNER = os.path.join(LEAD, "refsync_scope_20261109", "_rs_carrier_scan.py")

# ---- import unmodified scanner (read-only) --------------------------------
spec = importlib.util.spec_from_file_location("_me_upstream_scanner", SCANNER)
up = importlib.util.module_from_spec(spec)
spec.loader.exec_module(up)

N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"

def iter_corpus():
    """Mirror up.iter_files(LEAD, ['.md'], 2) + scanner's read filters."""
    for dp, dn, fn in os.walk(LEAD):
        rel_dir = os.path.relpath(dp, LEAD).replace("\\", "/")
        depth = 0 if rel_dir == "." else rel_dir.count("/") + 1
        if depth > 2:
            dn[:] = []
            continue
        for f in sorted(fn):
            if not f.lower().endswith(".md"):
                continue
            p = os.path.join(dp, f)
            if not os.path.isfile(p):
                continue
            try:
                b = open(p, "rb").read()
            except OSError:
                continue
            if b"\x00" in b:
                continue
            yield os.path.relpath(p, LEAD).replace("\\", "/"), b.decode("utf-8", "replace")

def line_sets(needles):
    """Return {needle: set((rel,line_no))} and {key: hit_tuple}."""
    hits = {n: set() for n in needles}
    lines = {}
    scanned = 0
    for rel, txt in iter_corpus():
        scanned += 1
        for i, L in enumerate(txt.splitlines(), 1):
            h = tuple(n for n in needles if n in L)
            if not h:
                continue
            key = (rel, i)
            lines[key] = (h, L)
            for n in h:
                hits[n].add(key)
    return scanned, hits, lines

def show(title, obj):
    print("### " + title)
    print(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=2))
    print("")

def main():
    out = []
    def P(s=""):
        out.append(s)
        print(s)

    P("SCANNER_SHA256 = %s" % hashlib.sha256(open(SCANNER, "rb").read()).hexdigest())
    P("SCANNER_BYTES = %d" % os.path.getsize(SCANNER))
    P("")

    # ---------------- Step 1(b): needle positions on :22 -------------------
    target = os.path.join(LEAD, "s604_verdict_entry_20261109", "_ve_DRAFT_S609.md")
    L22 = io.open(target, encoding="utf-8").read().splitlines()[21]
    P("=== STEP 1(b)  _ve_DRAFT_S609.md:22 needle positions ===")
    P("line22 len = %d" % len(L22))
    P("N1 = %r ; find = %d" % (N1, L22.find(N1)))
    P("N2 = %r ; find = %d" % (N2, L22.find(N2)))
    P("normalized variant %r find = %d" % ("只能判『不可复现』", L22.find("只能判『不可复现』")))
    P("outer quote segment = %r" % L22[L22.find("「只能判"):L22.find("当年错误步骤") + len("当年错误步骤") + 1])
    P("CONTAINS_BOTH_VERBATIM = %s" % (L22.find(N1) >= 0 and L22.find(N2) >= 0))
    P("")

    # quote spans + role trace using upstream code
    spans = up.spans_of_quotes(L22)
    P("=== STEP 1(c)  four-gate mechanism trace on :22 ===")
    P("quote spans (x,y,delim) = %s" % repr(spans))
    for cfg_name, needles in [("single", [N1]), ("double", [N1, N2])]:
        present = [n for n in needles if n in L22]
        poss = [(n, L22.find(n)) for n in present]
        pos = min((p for _, p in poss), default=-1) if poss else -1
        q = up.quoted_containing(L22, pos) if pos >= 0 else None
        negs = [k for k in up.NEG_LEX if k in L22]
        c = up.classify_line(L22, needles, "")
        P("cfg=%-6s present=%s poss=%s min_pos=%d q=%s negs=%s" %
          (cfg_name, present, poss, pos, repr(q), negs))
        P("        UPDATED_SAMPLE.search = %s ; prefix = %s" %
          (bool(up.UPDATED_SAMPLE.search(L22)), L22.lstrip().startswith((">", "|"))))
        P("        classify_line -> %s" % (c["role"] if c else None))
    P("")

    # ---------------- Step 2(a,b): line-set quantification ----------------
    P("=== STEP 2(a,b)  corpus line sets (ext=.md, max-depth=2) ===")
    scanned, hits, lines = line_sets([N1, N2])
    U1, U2 = hits[N1], hits[N2]
    only1, only2, both = U1 - U2, U2 - U1, U1 & U2
    union = U1 | U2
    P("scanned files (mirrored) = %d" % scanned)
    P("|U1| lines hit by N1 only-or-both = %d" % len(U1))
    P("|U2| lines hit by N2 only-or-both = %d" % len(U2))
    P("|only1|  = %d  (N1 hits, N2 does not)" % len(only1))
    P("|only2|  = %d  (N2 hits, N1 does not)  <-- answer 2(a)" % len(only2))
    P("|both|   = %d  (both needles hit the SAME line)" % len(both))
    P("|union|  = %d  (lines scanned with both needles)" % len(union))
    P("")
    P("MISSED lines relative to the two-needle union:")
    P("  N1 only  -> misses %d lines (= |only2|)" % len(only2))
    P("  N2 only  -> misses %d lines (= |only1|)" % len(only1))
    P("  both     -> misses %d lines (union is complete by definition)" % 0)
    P("")
    P("CROSS-CHECK vs unmodified scanner outputs (should equal carrier occurrences):")
    P("  scanner single : carrier occurrences = 79  ; |U1| = %d ; match = %s" % (len(U1), len(U1) == 79))
    P("  scanner double : carrier occurrences = 122 ; |union| = %d ; match = %s" % (len(union), len(union) == 122))
    P("  delta added by the 2nd needle = %d = |only2| (=%d) + overlap-attribution check" % (len(union) - len(U1), len(only2)))
    P("")
    P("is :22 in only2 ? %s   (key = ('s604_verdict_entry_20261109/_ve_DRAFT_S609.md', 22))" %
      (("s604_verdict_entry_20261109/_ve_DRAFT_S609.md", 22) in only2))
    P("")

    # hit-set patterns: how many lines fall in each subset (2^N-1 = 3 nonempty)
    pat = Counter(h for h, _ in lines.values())
    P("hit-set pattern histogram over union (%d nonempty patterns of 2 needles):" % len(pat))
    for k, v in sorted(pat.items(), key=lambda kv: -kv[1]):
        P("   %-70s -> %d lines" % (repr(k), v))
    P("")

    # ---------------- six negative controls: hit sets & actual roles -------
    controls = [
        ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123, "ASSERTION"),
        ("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25, "ASSERTION"),
        ("ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 196, "ASSERTION"),
        ("ledger_bound_20261109/_lb_BOUND_VOLUME.md", 129, "ASSERTION"),
        ("s604_verdict_entry_20261109/_ve_DRAFT_S609.md", 22, "REFUTING_QUOTE"),
        ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215, "ASSERTION"),
    ]
    P("=== six negative controls: per-line hit set under [N1,N2] ===")
    for rel, n, want in controls:
        key = (rel, n)
        h = lines.get(key, ((), ""))[0]
        P("   %s:%-4d want=%-16s hit_set=%s" % (rel, n, want, list(h)))
    P("")

    # ---------------- Step 2(d): reverse masking --------------------------
    P("=== STEP 2(d)  reverse masking via :165 min(pos) ===")
    P("claim: adding a needle can NEVER make a line un-scanned (monotone any/min),")
    P("       but CAN change its ROLE by moving pos out of a quote span.")
    # candidate early needles on the REAL line 22, outside all quote spans
    cands = ["登记效力说明", "与既有草案", "全部不受影响", "暂编", "复算数字"]
    P("candidate extra needles on the REAL :22 (position, inside_quote_span):")
    chosen = None
    for c in cands:
        p = L22.find(c)
        q = up.quoted_containing(L22, p) if p >= 0 else None
        P("   %-14r pos=%-4d q=%s" % (c, p, repr(q)))
        if p >= 0 and q is None and chosen is None:
            chosen = c
    P("chosen N3 = %r" % chosen)
    P("")
    if chosen:
        for cfg_name, needles in [
            ("[N2]", [N2]),
            ("[N1,N2]", [N1, N2]),
            ("[N1,N2,N3]", [N1, N2, chosen]),
            ("[N3,N2]", [chosen, N2]),
        ]:
            c = up.classify_line(L22, needles, "")
            poss = [(n, L22.find(n)) for n in needles if n in L22]
            pos = min((p for _, p in poss), default=-1) if poss else -1
            P("   cfg=%-14s present_pos=%s min_pos=%-4d role=%s" %
              (cfg_name, poss, pos, c["role"] if c else None))
        P("")
        P("=> adding N3 (which hits :22 EARLIER and OUTSIDE quotes) flips :22")
        P("   from REFUTING_QUOTE to a non-refuting role: reverse masking.")
    P("")

    # ---------------- Step 2(c): N-scaling empirical -----------------------
    P("=== STEP 2(c)  N-scaling: 2 -> 3 -> 4 needles ===")
    N4 = "与既有草案" if chosen != "与既有草案" else "暂编"
    for k, needles in [(2, [N1, N2]), (3, [N1, N2, chosen]), (4, [N1, N2, chosen, N4])]:
        sc2, h2, l2 = line_sets(needles)
        nonempty = len(l2)
        P("   N=%d needles=%s" % (k, needles))
        P("      union lines = %d ; per-needle line counts = %s ; nonempty hit-set patterns = %d (of %d)" %
          (nonempty, [len(h2[n]) for n in needles],
           len(set(h for h, _ in l2.values())), 2 ** k - 1))
    P("")
    P("NOTE: 2^k-1 is the number of DISTINCT hit-set patterns; the aggregate")
    P("      SELF_TEST still prints only 6 PASS/FAIL lines and 1 SELF_TEST verdict,")
    P("      independent of k. Proven information stays 1 bit while the claim")
    P("      'every needle works' needs k bits. Ambiguity grows as 2^k-1.")
    P("")

    io.open(os.path.join(HERE, "_me_analyze_out.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")

if __name__ == "__main__":
    main()
