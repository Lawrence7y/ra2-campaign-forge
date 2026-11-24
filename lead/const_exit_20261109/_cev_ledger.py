# -*- coding: utf-8 -*-
"""_cev_ledger.py -- step ④: per-line ledger verification + orchestrator-rule
reproduction on the 4 production gates.

Read-only over the two ledgers.  Every marked line is enumerated with its
basenames and EACH basename's class from MY independent classifier (413 batch)
or from the kd census / unresolvable status.  "CONSTANT_EXIT rows in the two
ledgers" is answered per line, not as a bare count.
"""
import ast
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.dont_write_bytecode = True
ROOT = r"D:/Project/ra2-campaign-forge"
WD = os.path.join(ROOT, "lead", "const_exit_20261109")
os.chdir(ROOT)

PAT_PY = re.compile(r"([A-Za-z0-9_./\-]+\.py)")
MARK = re.compile(r"PASS|exit\s*=\s*0|EXIT=0|SELF_TEST")
LEDGERS = ["lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md"]

mybatch = json.load(open(os.path.join(WD, "_cev_batch_out.json"), encoding="utf-8"))
my_by_basename = {}
for r in mybatch["rows"]:
    my_by_basename.setdefault(r["basename"], []).append(r)
my_cls = {r["rel"]: r["cls"] for r in mybatch["rows"]}
kd = json.load(open("lead/k1bit_detect_20261109/_kd_detect_out.json", encoding="utf-8"))
census = {os.path.basename(r["rel"]) for r in kd["rows"]}

orch_raw = json.load(open(os.path.join(WD, "_ce_orchestrator_raw.json"), encoding="utf-8"))
orch_cls = {}
for r in orch_raw["const_or_noexit"]:
    orch_cls[os.path.basename(r["rel"])] = r["cls"]
for r in orch_raw["conditional"]:
    orch_cls[os.path.basename(r["rel"])] = "CONDITIONAL_EXIT"


def classify_basename(b):
    if b in census:
        return "IN_173_CENSUS_NOT_IN_413"
    if b in my_by_basename:
        return my_by_basename[b][0]["cls"]
    if b in orch_cls:
        return orch_cls[b]
    return "UNRESOLVED"


def reproduce_orchestrator_sites(tree):
    """Faithful copy of the orchestrator's sites() rule (draft :73-106), used
    only to answer 'what WOULD the rule say about the 4 gates'.  Pure AST,
    never executes a gate."""
    funcs = {x.name: x for x in ast.walk(tree) if isinstance(x, ast.FunctionDef)}
    out = []
    for n in tree.body:
        for c in ast.walk(n):
            if not isinstance(c, ast.Call):
                continue
            f = c.func
            if isinstance(f, ast.Attribute) and f.attr == "exit" and \
                    isinstance(f.value, ast.Name) and f.value.id == "sys":
                out.append((n.lineno, "sys.exit", c.args[0] if c.args else None))
            elif isinstance(f, ast.Name) and f.id == "exit":
                out.append((n.lineno, "exit", c.args[0] if c.args else None))
    res = []
    for ln, tag, arg in out:
        if arg is None:
            res.append((ln, tag, "CONSTANT_EXIT", "no-arg"))
        elif isinstance(arg, ast.Constant):
            res.append((ln, tag, "CONSTANT_EXIT", "literal " + repr(arg.value)))
        elif isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and \
                arg.func.id in funcs:
            fn = funcs[arg.func.id]
            rs = [x.value for x in ast.walk(fn) if isinstance(x, ast.Return)]
            kinds = set()
            for r in rs:
                if r is None:
                    kinds.add("none")
                elif isinstance(r, ast.Constant):
                    kinds.add("const")
                else:
                    kinds.add("expr")
            if (not rs) or kinds <= {"const", "none"}:
                res.append((ln, tag, "CONSTANT_EXIT", "all-literal returns %d" % len(rs)))
            else:
                res.append((ln, tag, "CONDITIONAL_EXIT", "non-literal returns %d" % len(rs)))
        else:
            res.append((ln, tag, "CONDITIONAL_EXIT", "non-literal expr"))
    return res


def main():
    lines = []
    for name in LEDGERS:
        t = open(name, encoding="utf-8", errors="replace").read()
        for i, l in enumerate(t.split("\n"), 1):
            if not MARK.search(l):
                continue
            bs = []
            for m in PAT_PY.finditer(l):
                b = os.path.basename(m.group(1).replace("\\", "/"))
                bs.append(b)
            if not bs:
                continue
            cls = {b: classify_basename(b) for b in bs}
            # exit=0 subject = basename nearest to the exit=0 / EXIT=0 token
            toks = [(m.start(), m.group(0)) for m in
                    re.finditer(r"exit\s*=\s*0|EXIT\s*=\s*0|EXIT=0", l)]
            # approximate: last .py token before the first exit token, else first
            pys = [(m.start(), os.path.basename(m.group(1).replace("\\", "/")))
                   for m in PAT_PY.finditer(l)]
            subj = ""
            if toks:
                tx = toks[0][0]
                before = [b for p, b in pys if p < tx]
                subj = before[-1] if before else (pys[0][1] if pys else "")
            lines.append(dict(file=name, line=i, text=l.strip(),
                              basenames=bs, classes=cls,
                              any_constant_flat=any(c == "CONSTANT_EXIT" for c in cls.values()),
                              any_zero_info_flat=any(c in ("CONSTANT_EXIT", "NO_EXIT_AT_ALL")
                                                     for c in cls.values()),
                              exit_subject=subj,
                              exit_subject_cls=classify_basename(subj) if subj else "NO_SUBJECT",
                              exit_subject_zero_info=(classify_basename(subj) in
                                                      ("CONSTANT_EXIT", "NO_EXIT_AT_ALL"))
                                                     if subj else False))

    constant_flat = [x for x in lines if x["any_constant_flat"]]
    constant_subject = [x for x in lines if x["exit_subject_cls"] == "CONSTANT_EXIT"]
    zero_flat = [x for x in lines if x["any_zero_info_flat"]]
    zero_subject = [x for x in lines if x["exit_subject_zero_info"]]

    # 4 gates under orchestrator's rule
    gates = ["lead/d27_ruling_20261106/check_d27.py",
             "lead/d28_ruling_20261106/check_d28.py",
             "lead/d29_ruling_20261106/check_d29.py",
             "lead/d30_ruling_20261106/check_d30.py"]
    gate_res = []
    for g in gates:
        tree = ast.parse(open(g, "rb").read().decode("utf-8-sig", errors="replace"))
        ss = reproduce_orchestrator_sites(tree)
        cls = "NO_EXIT_AT_ALL" if not ss else ("CONDITIONAL_EXIT" if any(
            x[2] == "CONDITIONAL_EXIT" for x in ss) else "CONSTANT_EXIT")
        gate_res.append(dict(rel=g, in_173_census=os.path.basename(g) in census,
                             orchestrator_rule_sites=[[a, b, c, d] for a, b, c, d in ss],
                             orchestrator_rule_cls=cls))

    out = dict(n_marked_lines=len(lines), lines=lines,
               n_constant_flat=len(constant_flat),
               n_constant_subject=len(constant_subject),
               n_zero_info_flat=len(zero_flat),
               n_zero_info_subject=len(zero_subject),
               constant_flat=[(x["file"], x["line"], x["basenames"], x["classes"]) for x in constant_flat],
               zero_info_subject=[(x["file"], x["line"], x["exit_subject"], x["exit_subject_cls"])
                                 for x in zero_subject],
               gates_under_orchestrator_rule=gate_res)
    with open(os.path.join(WD, "_cev_ledger_out.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("n_marked_lines", len(lines))
    print("n_constant_flat", len(constant_flat), "n_constant_subject", len(constant_subject))
    print("n_zero_info_flat", len(zero_flat), "n_zero_info_subject", len(zero_subject))
    print("\n== ZERO-INFO SUBJECT lines (per-line, my classifier) ==")
    for x in zero_subject:
        print("  %s:%d subj=%s cls=%s | %s" %
              (x["file"], x["line"], x["exit_subject"], x["exit_subject_cls"],
               x["text"][:150]))
    print("\n== ALL marked lines: file:line | basenames -> classes | flat_zero | subject_cls ==")
    for x in lines:
        print("  %s:%d | %s | flat0=%s subj=%s/%s" %
              (x["file"].split("/")[-1], x["line"],
               ",".join("%s:%s" % (b, x["classes"][b]) for b in x["basenames"]),
               x["any_zero_info_flat"], x["exit_subject"], x["exit_subject_cls"]))
    print("\n== 4 gates under the orchestrator sites() rule (what WOULD it say) ==")
    for g in gate_res:
        print("  ", g["rel"], "in_173_census", g["in_173_census"],
              "->", g["orchestrator_rule_cls"], "sites", g["orchestrator_rule_sites"])


if __name__ == "__main__":
    main()
