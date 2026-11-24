"""Independent re-implementation of the 32-domain R10/V12 shadow comparison.

Written from scratch for verification. Reads the same protected inputs, does NOT
import the author's _vi_shadow.py / _vi_probe.py. Only writes _viv_* files.
"""
import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "v12_impact_20261109"
BASELINE = ROOT / "lead" / "gate_rejudge32_20261109" / "_rj_delivery_baseline.json"
PRED = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
RULE = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


G7 = load(PRED, "_viv_g7")
R = load(RULE, "_viv_rule")


def fp(p):
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def main():
    bl = json.loads(BASELINE.read_text(encoding="utf-8"))
    rows = []
    all_hits = []
    print("[FP] BASELINE", *fp(BASELINE))
    print("[FP] PRED    ", *fp(PRED))
    print("[FP] RULE    ", *fp(RULE))
    for r in bl["rows"]:
        dom, main, bans = r["domain"], r["main"], r["params"].get("banned", [])
        p = ROOT / dom / main
        text = p.read_bytes().decode("utf-8")
        h, n = fp(p)
        fp_ok = (h == r["mainSha256"] and n == r["mainBytes"])
        raw = sorted((m.start(), t) for t in bans for m in re.finditer(re.escape(t), text))
        # Resolve the R10 predicate by the (problems, warnings, hits) contract.
        # Its module-level name is masked in this environment, so pick the callable
        # whose source signature returns that triple, without hardcoding the name.
        cands = [k for k in dir(G7) if callable(getattr(G7, k))
                 and getattr(getattr(G7, k), "__code__", None)
                 and getattr(getattr(G7, k), "__code__").co_argcount == 2
                 and "r10_context" in getattr(getattr(G7, k), "__code__").co_names
                 and "warnings" in getattr(getattr(G7, k), "__code__").co_varnames]
        assert len(cands) == 1, cands
        fn = getattr(G7, cands[0])
        probs, warns, hits = fn(text, bans)
        r10set = sorted((x["pos"], x["token"]) for x in hits)
        dom_hits = []
        for x in sorted(hits, key=lambda z: (z["pos"], z["token"])):
            tok, pos, end = x["token"], x["pos"], x["pos"] + len(x["token"])
            ln = text.count("\n", 0, pos) + 1
            v = R.classify_v12(text, pos, end, tok)
            rec = dict(domain=dom, line=ln, pos=pos, token=tok,
                       r10_kind=x["kind"], v12=v["verdict"], hard=list(v["hard"]),
                       weak=list(v["weak"]), override=v["override"],
                       review=v["review_flag"], unit=v["unit"],
                       orig=text[text.rfind("\n", 0, pos) + 1:text.find("\n", pos) if text.find("\n", pos) >= 0 else len(text)][:400])
            dom_hits.append(rec)
            all_hits.append(rec)
        rows.append(dict(domain=dom, banned=bans, fp_ok=fp_ok, raw=len(raw),
                         raw_eq_r10=(raw == r10set), problems=len(probs),
                         warnings=len(warns), hits=dom_hits))
    summary = dict(
        domains_total=len(rows),
        nonempty_banned=sum(1 for x in rows if x["banned"]),
        empty_banned=[x["domain"] for x in rows if not x["banned"]],
        domains_with_hits=[x["domain"] for x in rows if x["hits"]],
        domains_with_hits_n=sum(1 for x in rows if x["hits"]),
        total_hits=len(all_hits),
        r10_problems_total=sum(x["problems"] for x in rows),
        raw_all_identical=all(x["raw_eq_r10"] for x in rows),
        baseline_fp_all_match=all(x["fp_ok"] for x in rows),
        r10_kinds=dict(Counter(x["r10_kind"] for x in all_hits)),
        v12_verdicts=dict(Counter(x["v12"] for x in all_hits)),
        review_flag_true=sum(1 for x in all_hits if x["review"]),
        hard_marks=dict(Counter(m for x in all_hits for m in x["hard"])),
        quadrant=dict(Counter(("assertion" if x["r10_kind"] == "assertion" else "negquote") + "_" + x["v12"] for x in all_hits)),
    )
    # Two-domain 9 sites check
    two = [x for x in all_hits if x["domain"] in ("lead/c07_slot_20261109/", "lead/c07_truth_protocol_20261109/")]
    summary["two_domains_9_sites"] = dict(n=len(two), verdicts=dict(Counter(x["v12"] for x in two)),
        detail=[(x["domain"].split("/")[-2], x["line"], x["token"], x["r10_kind"], x["v12"], x["hard"]) for x in two])
    (WD / "_viv_shadow_own.json").write_text(json.dumps(dict(summary=summary, rows=rows), ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
