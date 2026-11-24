# -*- coding: utf-8 -*-
r"""_crv_ast_probe.py -- INDEPENDENT reviewer probe.

(1) AST-analyse _fnr_check.py:certificate_ok for ANY disk read / hash op.
(2) Independently check whether the ORIGINAL CERTS quotes are verbatim on
    their anchored lines (the design claims 5/5 are not).
(3) Independently run the ORIGINAL old checker against P1 forged anchors.

Everything is READ-ONLY w.r.t. existing files; no main() is ever called.
Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_crv_ast_probe.py
"""
from __future__ import annotations
import ast
import copy
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
FNR = ROOT / "lead" / "falsifiable_no_relax_20261109" / "_fnr_check.py"
R9S_DIR = ROOT / "lead" / "gate_r9sem_20261109"
WDIR = ROOT / "lead" / "cert_realcheck_20261109"
sys.path.insert(0, str(R9S_DIR))

OUT = {}


def ast_probe():
    src = FNR.read_text(encoding="utf-8")
    tree = ast.parse(src)
    ops = ("open", "read_bytes", "read_text", "is_file", "exists", "sha256",
           "hashlib", "write_text", "write_bytes", "Path", "stat")

    def calls_in(node):
        d = {k: 0 for k in ops}
        names = set()
        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                f = n.func
                if isinstance(f, ast.Attribute):
                    nm = f.attr
                    if isinstance(f.value, ast.Name):
                        names.add(f.value.id + "." + nm)
                    else:
                        names.add("." + nm)
                elif isinstance(f, ast.Name):
                    nm = f.id
                    names.add(nm)
                else:
                    nm = None
                if nm in d:
                    d[nm] += 1
            if isinstance(n, ast.Name) and n.id in ("hashlib", "sha256", "open"):
                if n.id in d:
                    d[n.id] += 1
        return d, sorted(names)

    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "certificate_ok")
    lines = src.splitlines()
    block = "\n".join(lines[fn.lineno - 1:fn.end_lineno])
    d, names = calls_in(fn)
    OUT["certificate_ok"] = {
        "lineno": fn.lineno, "end_lineno": fn.end_lineno,
        "ast_call_counts": d, "call_names": names,
        "block_text_counts": {k: block.count(k) for k in
                              ("open(", "read_bytes", "read_text", "hashlib",
                               "sha256", "is_file", "exists", "Path(")},
        "block_lines": len(block.splitlines()),
    }
    # whole-file counts
    wd, wnames = calls_in(tree)
    OUT["whole_file"] = {"n_lines": len(lines),
                         "ast_call_counts": wd,
                         "call_names": wnames,
                         "text_counts": {k: src.count(k) for k in
                                         ("open(", "read_bytes", "read_text",
                                          "hashlib", "sha256", "write_text",
                                          "write_bytes", "Path(")},
                         "hashlib_occurrences": [i + 1 for i, l in enumerate(lines)
                                                 if "hashlib" in l]}

    # same AST probe on the design's verifier, for contrast
    v = WDIR / "_cr_real_verify.py"
    vsrc = v.read_text(encoding="utf-8")
    vtree = ast.parse(vsrc)
    res = {}
    for nm in ("load_seal", "verify_one", "verify_all"):
        f = next(n for n in ast.walk(vtree)
                 if isinstance(n, ast.FunctionDef) and n.name == nm)
        dd, nn = calls_in(f)
        res[nm] = {"lineno": f.lineno, "end_lineno": f.end_lineno,
                   "ast_call_counts": dd,
                   "read_bytes_calls": dd["read_bytes"],
                   "sha256_calls": dd["sha256"],
                   "call_names": nn}
    OUT["design_verifier_ast"] = res
    return OUT


def load_fnr():
    spec = importlib.util.spec_from_file_location("fnr_crv", FNR)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def quote_probe():
    fnr = load_fnr()
    rows = []
    for key, c in fnr.CERTS.items():
        anchor = c.get("anchor", "")
        rel, _, ln = anchor.rpartition(":")
        p = ROOT / rel
        row = {"item": list(key), "anchor": anchor, "quote": c.get("quote", "")}
        if not p.is_file():
            row["file_exists"] = False
            rows.append(row)
            continue
        b = p.read_bytes()
        ls = b.decode("utf-8", errors="replace").splitlines()
        n = int(ln) if ln.isdigit() else -1
        row["file_exists"] = True
        row["n_lines"] = len(ls)
        row["anchor_line_text"] = ls[n - 1][:200] if 1 <= n <= len(ls) else None
        row["quote_verbatim_on_anchor_line"] = (
            c.get("quote", "") in ls[n - 1]) if 1 <= n <= len(ls) else False
        row["verbatim_matching_line_numbers"] = [
            i + 1 for i, l in enumerate(ls) if c.get("quote", "") in l]
        row["ellipsis_in_quote"] = ("…" in c.get("quote", "")
                                    or "..." in c.get("quote", ""))
        rows.append(row)
    OUT["original_CERTS_quote_probe"] = rows
    OUT["original_CERTS_quote_probe_summary"] = {
        "n": len(rows),
        "n_on_anchor_line": sum(1 for r in rows
                                if r.get("quote_verbatim_on_anchor_line")),
        "n_anywhere_in_file": sum(1 for r in rows
                                  if r.get("verbatim_matching_line_numbers")),
    }


def old_p1_probe():
    """Reproduce P1 against the ORIGINAL old checker, importing as module."""
    import re
    fnr = load_fnr()
    import _r9s_predicates as R9S
    REF = json.loads((R9S_DIR / "_r9s_regress_out.json").read_text(encoding="utf-8"))
    dom = REF["domains32"]

    def pred(text, token):
        ok, layer, detail = R9S.r9s_element_present(text, token)
        if not ok:
            return (False, layer, detail)
        if re.search(r"待判|待定|尚需|尚未|不另下结论|暂不作判定|本件不重录|"
                     r"见台账|详见台账|详见附件|并非【|是否【|不可重建|"
                     r"输出数据待补|返回值详见附件", text):
            return (False, "", {"rejected_by": "pending/pointer guard"})
        return (ok, layer, detail)

    items = [{"domain": row["domain"], "token": el["token"]}
             for row in dom["rows"] if not row.get("main_missing")
             for el in row["per_element"]]
    flips = [{"domain": x["domain"], "token": x["token"]} for x in dom["flips"]]
    whitelist = [tuple(x) for x in dom["whitelist"]]
    certs = copy.deepcopy(fnr.CERTS)
    for v in certs.values():
        v["oracle_author"] = "independent_blind_adjudicator"
        v["predicate_author"] = "author_of_V1"
        v["oracle_truth"] = True
        v["oracle_sealed"] = True
    forged = copy.deepcopy(certs)
    for i, c in enumerate(forged.values()):
        c["anchor"] = "cfaa/NO_SUCH_%d.md:999999" % i
        c["quote"] = "本复核凭空编造的引文，未见于任何交付件。"
    kw = dict(items=items, flips=flips, whitelist=whitelist,
              registered_tokens=set(R9S.SPECS.keys()),
              spec_keys=set(R9S.SPECS.keys()) | {"额外预留要素"},
              certificates=forged, spec_roles=fnr.SPEC_ROLES,
              predicate=pred, adversarial_corpus=list(fnr.ADVERSARIAL),
              predicate_author="author_of_V1",
              whitelist_author="independent", whitelist_sealed=True)
    r = fnr.no_relaxation_check(**kw)
    OUT["old_P1_forgery"] = {
        "VERDICT": r["VERDICT"],
        "L1_ok": r["L1"]["ok"], "L2_ok": r["L2"]["ok"], "L3_ok": r["L3"]["ok"],
        "L1_problems": list(r["L1"]["problems"]),
        "L3_caught": r["L3"]["detail"]["n_adversarial_caught"],
        "anchor_files_exist": [(ROOT / c["anchor"].split(":")[0]).exists()
                               for c in forged.values()],
        "certificate_ok_direct": fnr.certificate_ok(
            next(iter(forged.values())), list(fnr.SPEC_ROLES.values())[0]),
    }
    # direct: verify certificate_ok does not look at the file at all
    c = next(iter(forged.values()))
    OUT["old_P1_forgery"]["anchor_is_nonexistent_file"] = (
        not (ROOT / c["anchor"].split(":")[0]).exists())


def main():
    ast_probe()
    quote_probe()
    old_p1_probe()
    (WDIR / "_crv_ast_out.json").write_text(
        json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8",
        newline="\n")
    print(json.dumps({
        "certificate_ok": OUT["certificate_ok"],
        "whole_file_hashlib_occurrences": OUT["whole_file"]["hashlib_occurrences"],
        "whole_file_text_counts": OUT["whole_file"]["text_counts"],
        "design_verifier_ast": OUT["design_verifier_ast"],
        "original_CERTS_quote_probe_summary":
            OUT["original_CERTS_quote_probe_summary"],
        "old_P1_forgery": OUT["old_P1_forgery"],
    }, ensure_ascii=False, indent=1))
    print("WROTE _crv_ast_out.json")


if __name__ == "__main__":
    main()
