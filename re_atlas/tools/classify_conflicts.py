"""R0-c: classify VA symbol conflicts into real disputes vs. noise.

For every address carrying more than one candidate name, decide:
  NOISE      every name but one is structural noise (returns 0, .text, v[52])
  ALIAS      names are prefix/qualifier variants of the same entity
  REAL       two substantively different entities claim the same address

Read-only. Human summary by default; JSON when REATLAS_JSON=1.
"""

import json
import os
import re
import sys

MAP = r"D:\Project\ra2-campaign-forge\re_atlas\evidence\symbol_map.json"

NOISE_PAT = re.compile(
    r"^(?:\.[a-z]+|return\b|mov\b|call\b|.*\bv\[\d+\]|.*\bvfunc\[\d+\].*|.*空桩.*|.*残留.*|"
    r".*段首.*|.*无\s*raw.*|.*BSS.*|.*空间桶.*|.*间接入口.*|.*间接分发.*)$",
    re.I,
)
# same entity described at different granularity: qualifier suffixes that
# authors add or drop freely, plus known co-name pairs for the same routine
QUAL_SUFFIX = re.compile(r"(?:地表贴图|二次回落|炮弹剔除|剔除|入口|序言|桩)$")


def norm(s):
    s = s.strip()
    s = re.sub(r"\s*[\(（].*?[\)）]\s*$", "", s)
    s = QUAL_SUFFIX.sub("", s)
    s = re.sub(r"\s+0x[0-9A-Fa-f]{8}\s*$", "", s)          # trailing address echo
    s = re.sub(r"\s*(?:读取|写入|检查|调用|入口|退出|序言|平栈|分支|比较点|槽|闸|点)\s*\d*$", "", s)
    s = QUAL_SUFFIX.sub("", s)
    s = s.replace("Class::", "::")
    s = re.sub(r"^([A-Za-z_][A-Za-z0-9_]*?)Class$", r"\1", s) if "::" not in s else s
    s = re.sub(r"::.*::", "::", s)
    return s.strip(" -–—:")


def core_class(s):
    """RadarClass::DrawMap -> ('Radar','DrawMap'); Can_Enter_Cell -> 'Can_Enter'"""
    s = norm(s)
    c, leaf = split_qual(s)
    if c is not None:
        c = re.sub(r"Class$", "", c)
    if leaf:
        # docs abbreviate the leaf inconsistently; _Cell is the only suffix
        # that is dropped by some authors but kept by others
        leaf = re.sub(r"_Cell$", "", leaf)
    return c, leaf


def split_qual(s):
    if "::" in s:
        i = s.rfind("::")
        return s[:i], s[i + 2:]
    return None, s


def classify(syms):
    names = [s for s in syms if not NOISE_PAT.match(s)]
    if len(names) <= 1:
        return "NOISE", names

    groups = {}
    for n in names:
        groups.setdefault(norm(n), []).append(n)
    if len(groups) == 1:
        return "ALIAS", names

    cores = set(groups)
    leaves = {norm(split_qual(n)[1]) for n in names}
    if cores & leaves:
        return "ALIAS", names

    base = {norm(n) for n in names if split_qual(n)[0] is None}
    for n in names:
        c, _l = split_qual(n)
        if c is not None and norm(c) in base:
            return "ALIAS", names

    # same owning class, method-name variant (Can_Enter vs Can_Enter_Cell):
    # docs disagree on whether the leaf is abbreviated, not on the entity
    classes = {norm(split_qual(n)[0]) for n in names if split_qual(n)[0]}
    leafs = {core_class(n)[1] for n in names}
    if len(classes) == 1 and len(leafs) == 1:
        return "ALIAS", names
    # a bare method name versus its qualified form
    if None in {split_qual(n)[0] for n in names} and len(leafs) == 1:
        return "ALIAS", names

    return "REAL", names


def main():
    d = json.load(open(MAP, encoding="utf-8"))
    m = d["map"]
    out = {"NOISE": [], "ALIAS": [], "REAL": []}
    for va, rec in sorted(m.items()):
        names = list(rec["symbols"])
        if len(names) < 2:
            continue
        kind, kept = classify(names)
        out[kind].append({"va": va, "symbols": kept, "raw": names})

    if os.environ.get("REATLAS_JSON") == "1":
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0

    for k in ("REAL", "ALIAS", "NOISE"):
        print(f"# {k}: {len(out[k])}")
    print()
    print("## REAL DISPUTES (needs adjudication)")
    for r in out["REAL"]:
        print(f'  {r["va"]}  ' + "  |  ".join(r["symbols"]))
    print()
    print("## ALIAS SETS (same entity, different granularity)")
    for r in out["ALIAS"][:60]:
        print(f'  {r["va"]}  ' + "  |  ".join(r["symbols"]))
    print()
    print("## NOISE-DOMINATED")
    for r in out["NOISE"][:40]:
        print(f'  {r["va"]}  ' + "  |  ".join(r["raw"]))
    return 0


sys.exit(main())
