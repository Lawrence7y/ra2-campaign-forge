# -*- coding: utf-8 -*-
"""_rs_carrier_scan.py — reusable carrier/risk self-check (README).

Given one outdated expression, enumerate EVERY carrier under a root (default:
whole lead/, NO depth cap, NO write-domain filter, NO filename filter), and
classify each occurrence's ledger-entry risk. Prints to STDOUT ONLY; this
script NEVER writes a file (redirect stdout to the write domain if a record
is needed). Read-only, zero live-machine, zero sampling code, hashlib only.

Corrected scanning scope R1-R6:
 R1 Scope = content-addressed, not domain-addressed: walk the whole root,
    all text-like files, no depth cap; never take a prior report's file
    list as the scan universe. Report scanned-file count + each carrier's
    SHA256 so a re-run is reproducible.
 R2 Unit = SENTENCE/OCCURRENCE, not file. One sentence copied verbatim into
    N compilations/templates/sandboxes = N carriers. Per-file counting
    silently collapses them; per-line preserves block membership.
 R3 "Same sentence" requires explicit verbatim comparison (EQUAL /
    NOT-EQUAL + first differing codepoints). No eyeballing.
 R4 Entry risk = anchored marker-line pairs (START/END regex must match the
    WHOLE line, not a mere mention). Only open intervals count as
    "随整段进台账". Unpaired markers are an ERROR, never guessed.
 R5 Refuting quotes are NOT deleted from the report; they get a ROLE and a
    separate section. needs_fix requires BOTH assertion role AND real entry
    path. Silent dropping would hide §609:22 (inside an appendable block).
 R6 Negative controls: known assertions and known refutations must classify
    as ASSERTION / REFUTING_QUOTE, else EXIT=1.

Usage (PowerShell / Git Bash, from repo root):
  python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py" \
      --needle "只能判「不可复现」" --needle "不能定位当年错误步骤" \
      --canonical "<整行原文>" \
      --include-refuting \
      > "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan_out.txt"
"""
import os, re, sys, hashlib, argparse, unicodedata
from collections import Counter

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# --- path safety (read-only inputs) ------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))           # sole write domain
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))          # .../ra2-campaign-forge
DEFAULT_ROOT = os.path.join(REPO_ROOT, "lead")

def validated_root(p):
    """Normalize, require an existing directory, require containment inside
    REPO_ROOT via commonpath (no traversal outside the repository)."""
    raw = os.path.abspath(os.path.normpath(p))
    base = os.path.abspath(os.path.normpath(REPO_ROOT))
    if os.path.commonpath([raw, base]) != base:
        raise ValueError("--root must stay inside the repository: %s" % raw)
    if not os.path.isdir(raw):
        raise ValueError("--root is not an existing directory: %s" % raw)
    return raw

# --- R4: anchored marker lines (line MUST be a marker, not mention one) -----
START = re.compile(
    r"^\s*(?:"
    r"<!--[^>]*草案正文[^>]*逐字转录开始[^>]*-->"
    r"|#{1,6}\s*↓{2,}[^\n]*草案正文[^\n]*"
    r"|↓{3,}\s*草案正文\s*↓{3,}"
    r")\s*$")
END = re.compile(
    r"^\s*(?:"
    r"<!--[^>]*草案正文[^>]*逐字转录结束[^>]*-->"
    r"|#{1,6}\s*↑{2,}[^\n]*草案正文[^\n]*"
    r"|↑{3,}\s*草案正文[^\n]*↑{3,}"
    r")\s*$")

DECL_APPEND = re.compile(r"(可整段复制追加|整段复制追加|建议均.{0,6}整段追加|整段追加)")
DECL_NOTLEDGER = re.compile(r"(不是台账|不入台账|不构成台账内容)")
DECL_TERMINAL = re.compile(r"(撰写终件|定稿|调查报告|交付轮产物|仅出结论与依据)")

# --- R5: quotation spans + refutation lexicon -------------------------------
PAIRS = [("「", "」"), ("『", "』"), ("`", "`"), ("“", "”")]
NEG_LEX = [
    "不再成立", "过时", "已定谳", "已闭合", "已定位", "被推翻", "被超越",
    "被取代", "取代", "不成立", "否证", "自本节起", "改前", "改后",
    "建议改", "改为", "原句", "原文逐字", "逐字", "grep", "命中", "验收",
    "误读", "瑕疵", "不可引用", "不影响", "复核", "未验项", "说错",
    "更新：", "已由本定谳", "如何修订", "如何处置",
]
UPDATED_SAMPLE = re.compile(
    r"(2026-11-09 更新|错误步骤已定谳为|本句.{0,8}自该节起不再成立|改为：|建议改为)")

def spans_of_quotes(line):
    out = []
    for lo, hi in PAIRS:
        if lo == hi:
            idxs = [m.start() for m in re.finditer(re.escape(lo), line)]
            for x, y in zip(idxs[0::2], idxs[1::2]):
                out.append((x, y + len(hi), lo))
        else:
            pos = 0
            while True:
                x = line.find(lo, pos)
                if x < 0:
                    break
                y = line.find(hi, x + len(lo))
                if y < 0:
                    break
                out.append((x, y + len(hi), lo))
                pos = y + len(hi)
    return out

def quoted_containing(line, needle_pos):
    for x, y, d in spans_of_quotes(line):
        if x <= needle_pos < y:
            return (line[x:y], d)
    return None

def blocks_of(lines):
    stack, pairs, errors = [], [], []
    for i, L in enumerate(lines, 1):
        if START.match(L):
            stack.append(i)
        elif END.match(L):
            if stack:
                pairs.append((stack.pop(), i))
            else:
                errors.append("END-without-START@%d" % i)
    for s in stack:
        errors.append("START-without-END@%d" % s)
    return sorted(pairs), errors

def verbatim_cmp(a, b):
    """R3: explicit equality + differing codepoints."""
    if a == b:
        return True, []
    diffs = []
    for i in range(max(len(a), len(b))):
        ca = a[i] if i < len(a) else None
        cb = b[i] if i < len(b) else None
        if ca != cb:
            diffs.append((i, ca, cb))
    return False, diffs

def fmt_cp(c):
    if c is None:
        return "<EOS>"
    return "%r (U+%04X %s)" % (c, ord(c), unicodedata.name(c, "?")[:24])

def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def iter_files(root, exts, maxdepth):
    for dp, dn, fn in os.walk(root):
        rel = os.path.relpath(dp, root).replace("\\", "/")
        depth = 0 if rel == "." else rel.count("/") + 1
        if maxdepth is not None and depth > maxdepth:
            dn[:] = []
            continue
        for f in sorted(fn):
            if exts and not any(f.lower().endswith(e) for e in exts):
                continue
            p = os.path.join(dp, f)
            if os.path.isfile(p):
                yield p, os.path.relpath(p, root).replace("\\", "/"), depth

def classify_line(line, needles, canonical):
    pos = min((line.find(n) for n in needles if n in line), default=-1)
    if pos < 0:
        return None
    q = quoted_containing(line, pos)
    negs = [k for k in NEG_LEX if k in line]
    prefix = line.lstrip().startswith((">", "|"))
    if UPDATED_SAMPLE.search(line) and not q:
        role = "UPDATED_SAMPLE"       # 改后样例：旧串在括注里
    elif q and negs:
        role = "REFUTING_QUOTE"       # 引该句来否定它
    elif (q or prefix) and negs:
        role = "NEGATED_CITATION"
    elif q:
        role = "QUOTED"               # 逐字引文，未判否定
    elif negs:
        role = "ANALYSIS_MENTION"     # 分析件提及（grep 命令 / 过时登记）
    else:
        role = "ASSERTION"            # 裸断言：真正的过时载体
    v_eq, v_diff = verbatim_cmp(canonical, line) if canonical else (None, [])
    q_eq = None
    if q:
        q_eq, _ = verbatim_cmp(canonical, q[0]) if canonical else (None, [])
    return {"role": role, "quote_delim": q[1] if q else None,
            "neg": negs, "verbatim_line_equal": v_eq,
            "verbatim_quote_equal": q_eq, "diff": v_diff[:3]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--needle", action="append", required=True)
    ap.add_argument("--canonical", default="")
    ap.add_argument("--ext", default=".md,.txt,.py,.json")
    ap.add_argument("--max-depth", type=int, default=None)
    ap.add_argument("--include-refuting", action="store_true")
    ap.add_argument("--no-self-test", action="store_true")
    a = ap.parse_args()
    root = validated_root(a.root)
    exts = [e.strip() for e in a.ext.split(",") if e.strip()]
    out = []
    def P(s=""):
        out.append(s)

    P("### CORRECTED SCOPE RULE (R1-R6) — executable, reproducible")
    P("R1 root = %s ; max-depth = %s ; exts = %s" %
      (root, a.max_depth if a.max_depth is not None else "NONE (whole tree)", ",".join(exts)))
    P("R2 unit = occurrence(file,line) ; files are a derived grouping only")
    P("R3 canonical SHA256 = %s ; len = %d" %
      (sha(a.canonical) if a.canonical else "-", len(a.canonical)))
    P("R3 canonical text = %r" % a.canonical[:120])
    P("R4 START/END must match the WHOLE line; unpaired markers = ERROR")
    P("R5 refuting quotes get ROLE + separate section, never silently dropped")
    P("needles = %s" % [n for n in a.needle])
    P("")

    carriers, scanned = [], 0
    for p, rel, depth in iter_files(root, exts, a.max_depth):
        try:
            b = open(p, "rb").read()
        except OSError:
            continue
        if b"\x00" in b:
            continue
        scanned += 1
        txt = b.decode("utf-8", "replace")
        if not any(n in txt for n in a.needle):
            continue
        ls = txt.splitlines()
        bl, berr = blocks_of(ls)
        decl_append = any(DECL_APPEND.search(L) for L in ls)
        decl_notledger = any(DECL_NOTLEDGER.search(L) for L in ls)
        decl_terminal = bool(ls) and bool(DECL_TERMINAL.search(ls[0]))
        placeholder = "@@BODY_" in txt
        for i, L in enumerate(ls, 1):
            c = classify_line(L, a.needle, a.canonical)
            if not c:
                continue
            inside = [(s, e) for s, e in bl if s < i < e]
            if inside:
                entry = "APPENDABLE_BLOCK %s" % inside
                risk = "HIGH: 随整段进台账"
            elif placeholder and bl:
                entry = "TEMPLATE_GENERATED (placeholder @@BODY_n@@)"
                risk = "INDIRECT: 重建时由源件注入"
            elif berr:
                entry = "BLOCK_PARSE_ERROR %s" % berr
                risk = "UNKNOWN: 需人工复核"
            elif decl_terminal or (not bl and not decl_append):
                entry = "STANDALONE_DOC (no appendable block)"
                risk = "NONE: 不随段进台账"
            else:
                entry = "OUTSIDE_BLOCK (e.g. §6.3 未验项 / 索引 / 校核)"
                risk = "NONE: 不随段进台账（仅草案自洽）"
            assertion = c["role"] == "ASSERTION"
            needs_fix = assertion and risk.startswith("HIGH")
            carriers.append(dict(rel=rel, line=i, depth=depth,
                                 sha=hashlib.sha256(b).hexdigest(), bytes=len(b),
                                 role=c["role"], entry=entry, risk=risk,
                                 needs_fix=needs_fix,
                                 quote_delim=c["quote_delim"],
                                 vline=c["verbatim_line_equal"],
                                 vquote=c["verbatim_quote_equal"],
                                 diff=c["diff"], neg=c["neg"], text=L,
                                 decl_append=decl_append, decl_notledger=decl_notledger))
    P("scanned files = %d ; carrier occurrences = %d ; distinct files = %d" %
      (scanned, len(carriers), len({c["rel"] for c in carriers})))
    P("")
    P("=== A. FULL CARRIER MAP (every file, every line, risk-classified) ===")
    byfile = {}
    for c in carriers:
        byfile.setdefault(c["rel"], []).append(c)
    for rel in sorted(byfile):
        cs = byfile[rel]
        P("")
        P("FILE %s  bytes=%d  sha256=%s  hits=%d  decl_append=%s decl_notledger=%s" %
          (rel, cs[0]["bytes"], cs[0]["sha"], len(cs),
           cs[0]["decl_append"], cs[0]["decl_notledger"]))
        for c in cs:
            P("  :%-4d role=%-17s needs_fix=%-5s %s" %
              (c["line"], c["role"], c["needs_fix"], c["risk"]))
            P("         entry=%s" % c["entry"])
            P("         verbatim(canonical==line)=%s verbatim(canonical==quote)=%s quote_delim=%s" %
              (c["vline"], c["vquote"], c["quote_delim"]))
            if c["diff"]:
                P("         first diffs (canonical vs line): " + "; ".join(
                    "%d: %s -> %s" % (i, fmt_cp(x), fmt_cp(y)) for i, x, y in c["diff"]))
            if c["neg"]:
                P("         refutation/analysis signals: " + ",".join(c["neg"][:8]))
            P("         text: %s" % c["text"][:200])
    P("")
    P("=== B. STRICT INTERSECTION (needs_fix = ASSERTION AND HIGH entry risk) ===")
    strict = [c for c in carriers if c["needs_fix"]]
    P("occurrences = %d ; distinct files = %d" %
      (len(strict), len({c["rel"] for c in strict})))
    for c in strict:
        P("   %s:%d  %s  [%s]" % (c["rel"], c["line"], c["risk"], c["entry"]))
    P("")
    P("=== C. NON-FIX OCCURRENCES (refuting / quoted / analysis / no entry path) ===")
    ref = [c for c in carriers if not c["needs_fix"]]
    P("occurrences = %d ; distinct files = %d" % (len(ref), len({c["rel"] for c in ref})))
    P("role histogram: %s" % dict(Counter(c["role"] for c in ref)))
    if a.include_refuting:
        for c in ref:
            P("   %s:%d role=%s neg=%s" %
              (c["rel"], c["line"], c["role"], ",".join(c["neg"][:5])))
    else:
        P("   (use --include-refuting to expand)")
    P("")
    P("=== D. HOW REFUTING QUOTES ARE EXCLUDED FROM THE FIX LIST (R5) ===")
    P("1) needle inside a paired quote span (「」『』``) AND a negation/update")
    P("   lexicon hit on the SAME line => role != ASSERTION => needs_fix=False.")
    P("2) '改后' samples with 更新：/已定谳为/自该节起不再成立 but no quote => UPDATED_SAMPLE.")
    P("3) grep/命中/验收/逐字/原文逐字/改前/建议改 => ANALYSIS_MENTION, never ASSERTION.")
    P("4) A refuting quote INSIDE an appendable block (e.g. §609 :22) is KEPT in")
    P("   section A with risk=HIGH but role=REFUTING_QUOTE: full audit trail,")
    P("   without inflating the fix count. It is NOT silently dropped.")
    P("5) needs_fix requires BOTH role=ASSERTION AND risk=HIGH.")
    P("   Outside-block assertions (:215 §6.3) and standalone terminal docs")
    P("   get risk=NONE, matching MINHARD_SET_CHECK.md §3.2/§3.3.")
    P("")
    ok = True
    if not a.no_self_test:
        P("=== E. NEGATIVE-CONTROL SELF-TEST (R6) ===")
        def role_of(rel, n):
            for c in carriers:
                if c["rel"].endswith(rel) and c["line"] == n:
                    return c["role"]
            return "<not-scanned>"
        checks = [
            ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123, "ASSERTION"),
            ("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25, "ASSERTION"),
            ("ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 196, "ASSERTION"),
            ("ledger_bound_20261109/_lb_BOUND_VOLUME.md", 129, "ASSERTION"),
            ("s604_verdict_entry_20261109/_ve_DRAFT_S609.md", 22, "REFUTING_QUOTE"),
            ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215, "ASSERTION"),
        ]
        for rel, n, want in checks:
            got = role_of(rel, n)
            good = got == want
            ok &= good
            P("  %-5s %s:%d want=%-16s got=%s" %
              ("PASS" if good else "FAIL", rel, n, want, got))
        P("SELF_TEST = %s" % ("PASS" if ok else "FAIL"))

    print("\n".join(out))
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
