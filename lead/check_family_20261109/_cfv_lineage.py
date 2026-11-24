"""Independent pairwise lineage / similarity evidence (verification only).

Usage: python -I -X utf8 <this> <ROOT> <OUT.json> <LIST.txt>
Own metrics: normalized line-multiset Jaccard, difflib ratio, LCS length,
ordered shared-line runs, AST function-body normalized similarity, and an
explicit asymmetry test (which file has unique lines). mtime is recorded but
NEVER used as a direction argument.
"""
import ast
import difflib
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()

CANDIDATES = {
    "d25": "lead/d25_ruling_20261106/check_d25.py",
    "d26": "lead/d26_ruling_20261106/check_d26.py",
    "d27": "lead/d27_ruling_20261106/check_d27.py",
    "d28": "lead/d28_ruling_20261106/check_d28.py",
    "d29": "lead/d29_ruling_20261106/check_d29.py",
    "d30": "lead/d30_ruling_20261106/check_d30.py",
    "d27_baseline": "lead/stale_pass_20261109/_sp_sandbox/check_d27_baseline.py",
    "d28_baseline": "lead/stale_pass_20261109/_sp_sandbox/d28/check_d28_baseline.py",
    "d29_baseline": "lead/stale_pass_20261109/_sp_sandbox/d29/check_d29_baseline.py",
    "d30_baseline": "lead/stale_pass_20261109/_sp_sandbox/d30/check_d30_baseline.py",
    "fileoffset_tpl": "out/re_work/qc/W3_20261001/docfix2/check_fileoffset_axiom.template.py",
}


def load(rel):
    p = ROOT / rel
    if not p.is_file():
        return None
    raw = p.read_bytes()
    txt = raw.decode("utf-8-sig")
    return {"rel": rel, "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "lines": txt.splitlines(),
            "mtime_ns": p.stat().st_mtime_ns,
            "text": txt}


def norm_lines(lines):
    """Keep stripped non-blank lines; this catches re-indented copies."""
    return [x.strip() for x in lines if x.strip()]


def lcs(a, b):
    # classic DP, lengths only
    if len(a) * len(b) > 4_000_000:
        return -1
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def longest_run(a, b):
    """Longest consecutive identical normalized-line run (order-sensitive)."""
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    best = 0
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            if x == y:
                v = prev[j] + 1
                best = max(best, v)
            else:
                v = 0
            cur.append(v)
        prev = cur
    return best


def func_bodies(text):
    try:
        t = ast.parse(text)
    except SyntaxError:
        return {}
    out = {}
    for n in t.body:
        if isinstance(n, ast.FunctionDef):
            out[n.name] = (n.lineno, norm_lines(ast.unparse(n).splitlines()))
    return out


def pair(a, b):
    A, B = norm_lines(a["lines"]), norm_lines(b["lines"])
    ca, cb = Counter(A), Counter(B)
    inter = sum((ca & cb).values())
    union = sum((ca | cb).values())
    ja, jb = sum((ca - cb).values()), sum((cb - ca).values())
    # directed containment: fraction of a's normalized lines found in b
    contain_a_in_b = inter / len(A) if A else 0
    contain_b_in_a = inter / len(B) if B else 0
    seq = difflib.SequenceMatcher(None, A, B, autojunk=False)
    blocks = [m for m in seq.get_matching_blocks() if m.size > 0]
    fb_a, fb_b = func_bodies(a["text"]), func_bodies(b["text"])
    fb = []
    for name in sorted(set(fb_a) & set(fb_b)):
        la, lb = fb_a[name][1], fb_b[name][1]
        ca2, cb2 = Counter(la), Counter(lb)
        i2 = sum((ca2 & cb2).values())
        u2 = sum((ca2 | cb2).values())
        fb.append({"name": name, "line_a": fb_a[name][0], "line_b": fb_b[name][0],
                   "common": i2, "only_a": sum((ca2 - cb2).values()),
                   "only_b": sum((cb2 - ca2).values()),
                   "jaccard": round(i2 / u2, 4) if u2 else 1.0,
                   "identical": la == lb,
                   "nlines_a": len(la), "nlines_b": len(lb)})
    return {
        "a": a["rel"], "b": b["rel"],
        "sha256_a": a["sha256"], "sha256_b": b["sha256"],
        "bytes_a": a["bytes"], "bytes_b": b["bytes"],
        "mtime_ns_a": a["mtime_ns"], "mtime_ns_b": b["mtime_ns"],
        "norm_a": len(A), "norm_b": len(B),
        "common_norm": inter, "only_a": ja, "only_b": jb,
        "jaccard_norm": round(inter / union, 4) if union else 1.0,
        "difflib_ratio": round(difflib.SequenceMatcher(None, a["text"], b["text"]).ratio(), 4),
        "lcs_norm": lcs(A, B),
        "longest_ordered_run": longest_run(A, B),
        "n_matching_blocks": len(blocks),
        "largest_block": max((m.size for m in blocks), default=0),
        "contain_a_in_b": round(contain_a_in_b, 4),
        "contain_b_in_a": round(contain_b_in_a, 4),
        "shared_func_bodies": fb,
        "direction_hint": (
            "a_subset_of_b" if ja == 0 and jb > 0 else
            "b_subset_of_a" if jb == 0 and ja > 0 else
            "identical_bytes" if a["sha256"] == b["sha256"] else
            "neither_subset"),
    }


D = {k: load(v) for k, v in CANDIDATES.items()}
D = {k: v for k, v in D.items() if v is not None}
keys = sorted(D)
pairs = []
for i, x in enumerate(keys):
    for y in keys[i + 1:]:
        pairs.append(pair(D[x], D[y]))

# Which exact bytes are duplicated across the whole check_*.py corpus?
# The file list comes from the independent `find` (5th argv), NOT our own
# re-walk of the self-nested directory tree.
LIST = Path(sys.argv[3]).resolve()
sha_groups = {}
for line in LIST.read_text(encoding="utf-8").splitlines():
    rel = line.strip()
    if not rel:
        continue
    p = ROOT / rel
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    sha_groups.setdefault(h, []).append(rel)
dupes = {h: sorted(v) for h, v in sha_groups.items() if len(v) > 1}

out = {"root": ROOT.as_posix(),
       "candidates": {k: {"rel": v["rel"], "bytes": v["bytes"],
                           "sha256": v["sha256"], "mtime_ns": v["mtime_ns"],
                           "nlines": len(v["lines"])} for k, v in D.items()},
       "n_pairs": len(pairs), "pairs": pairs,
       "n_distinct_check_py": len(sha_groups),
       "duplicate_byte_groups": dupes,
       "n_duplicate_groups": len(dupes)}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

# compact console evidence
def short(r):
    return r.split("/")[-1]
for pr in pairs:
    a, b = short(pr["a"]), short(pr["b"])
    if pr["jaccard_norm"] >= 0.10 or a in ("check_d25.py", "check_d26.py", "check_d28.py") or b in ("check_d25.py", "check_d26.py", "check_d28.py"):
        fb = ";".join(f"{x['name']}:{x['jaccard']}{'=' if x['identical'] else ''}" for x in pr["shared_func_bodies"])
        print(f"{a}|{b}: common={pr['common_norm']} only={pr['only_a']}+{pr['only_b']} "
              f"J={pr['jaccard_norm']} difflib={pr['difflib_ratio']} "
              f"LCS={pr['lcs_norm']} run={pr['longest_ordered_run']} "
              f"blocks={pr['n_matching_blocks']}/{pr['largest_block']} "
              f"contain={pr['contain_a_in_b']}/{pr['contain_b_in_a']} "
              f"dir={pr['direction_hint']} funcs=[{fb}]")
print(f"n_distinct_check_py={out['n_distinct_check_py']} n_duplicate_groups={out['n_duplicate_groups']}")
