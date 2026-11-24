# -*- coding: utf-8 -*-
# _siv_fixtest.py — 复核③：三修复方案片段是否可跑、行为是否正确（沙盒建在我的写域 _siv_sandbox）。
# 同时核 §5.4 的 Windows sorted(Path) normcase 序断言。只读历史件；写仅限 _siv_sandbox。
import json, sys
from pathlib import Path
from importlib import util

WD = Path(r"D:\Project\ra2-campaign-forge\lead\gate_subject_id_20261109")
SAN = WD / "_siv_sandbox"
if SAN.exists():
    for p in sorted(SAN.rglob("*"), reverse=True):
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            p.rmdir()
else:
    SAN.mkdir()

spec = util.spec_from_file_location("_si_fix_lib", str(WD / "_si_fix_lib.py"))
lib = util.module_from_spec(spec)
spec.loader.exec_module(lib)
GateFail = lib.GateFail

results = []
def check(name, cond, detail=""):
    results.append({"name": name, "ok": bool(cond), "detail": detail})
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  | " + detail))

def mk(sub, name, size):
    d = SAN / sub
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text("x" * size, encoding="utf-8")
    return p

# 方案A
main_a = mk("A", "MAIN_FIX.md", 100)
mk("A", "_draft.md", 200)
try:
    got = lib.pick_deliverable_explicit(SAN / "A", "MAIN_FIX.md")
    check("A1 explicit picks named main (ignores bigger underscore)", got.name == "MAIN_FIX.md", got.name)
except GateFail as e:
    check("A1", False, repr(e))
try:
    lib.pick_deliverable_explicit(SAN / "A", "MISSING_FIX.md")
    check("A2 missing expected -> GateFail", False, "no exception")
except GateFail as e:
    check("A2 missing expected -> GateFail", True, str(e))

# 方案B
b1 = mk("B1", "SOLO.md", 100)
mk("B1", "_d1.md", 500)
mk("B1", "_d2.md", 50)
try:
    got = lib.pick_deliverable_unique_bare(SAN / "B1")
    check("B1 unique bare picked despite bigger underscore", got.name == "SOLO.md", got.name)
except GateFail as e:
    check("B1", False, repr(e))
mk("B2", "_only1.md", 10)
mk("B2", "_only2.md", 20)
try:
    lib.pick_deliverable_unique_bare(SAN / "B2")
    check("B2 zero bare -> GateFail", False, "no exception")
except GateFail as e:
    check("B2 zero bare -> GateFail", True, str(e))
mk("B3", "FIRST.md", 10)
mk("B3", "SECOND.md", 900)
try:
    lib.pick_deliverable_unique_bare(SAN / "B3")
    check("B3 two bare -> GateFail (fail-closed)", False, "no exception")
except GateFail as e:
    check("B3 two bare -> GateFail (fail-closed)", True, str(e)[:120])

# 方案C（对旧门禁 cands 列表打补丁）
cands = sorted((SAN / "B1").glob("*.md"))
try:
    got = lib.pick_deliverable_largest_bare(cands)
    check("C1 patch on cands picks unique bare", got.name == "SOLO.md", got.name)
except GateFail as e:
    check("C1", False, repr(e))
try:
    lib.pick_deliverable_largest_bare(sorted((SAN / "B3").glob("*.md")))
    check("C2 two bare -> GateFail", False, "no exception")
except GateFail as e:
    check("C2 two bare -> GateFail", True, str(e)[:120])
try:
    lib.pick_deliverable_largest_bare(sorted((SAN / "B2").glob("*.md")))
    check("C3 zero bare -> GateFail", False, "no exception")
except GateFail as e:
    check("C3 zero bare -> GateFail", True, str(e)[:120])

# overshadow_warning
ow = lib.overshadow_warning(SAN / "B1", SAN / "B1" / "SOLO.md")
check("D overshadow_warning flags bigger underscore", ow == ["_d1.md"], repr(ow))
ow2dom = mk("A2", "MAIN_FIX.md", 100)
mk("A2", "_small_note.md", 50)
ow2 = lib.overshadow_warning(SAN / "A2", ow2dom)
check("D2 no underscore bigger -> empty", ow2 == [], repr(ow2))

# §5.4 断言：Windows sorted(Path) 用 normcase 序；同字节 max 取序首
names = ["GATE_SUBJECT_ID_FIX.md", "_si_SUBJECT_ID_DEFECT.md"]
str_sorted = sorted(names)
path_sorted = [p.name for p in sorted([WD / n for n in names])]
check("E1 str-sort puts GATE first", str_sorted[0] == "GATE_SUBJECT_ID_FIX.md", repr(str_sorted))
check("E2 Path-sort(normcase) puts _si first", path_sorted[0] == "_si_SUBJECT_ID_DEFECT.md", repr(path_sorted))
g1 = (WD / names[0]).stat().st_size
g2 = (WD / names[1]).stat().st_size
picked = max([WD / n for n in path_sorted], key=lambda p: p.stat().st_size)
check("E3 old max on own WD picks _si twin (equal bytes, first of sorted)", picked.name == "_si_SUBJECT_ID_DEFECT.md",
      "sizes " + str(g1) + "/" + str(g2) + " picked=" + picked.name)

npass = sum(1 for r in results if r["ok"])
print("SUMMARY: " + str(npass) + "/" + str(len(results)) + " asserts passed")
out = {"asserts": results, "passed": npass, "total": len(results)}
w = WD / "_siv_fixtest_out.json"
w.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("written=" + str(w))
