# -*- coding: utf-8 -*-
"""_auditprobe_a4_mutations.py — 审计自加变异（A4）。

用临时副本（不动被审件），复用其 _fixture 造「清洁控制组」，
再各造一个探针原变异面**未覆盖**的变异，直接调 judge_artifacts，看指定 ID 是否红。
未红 ⇒ BLIND-SPOT 记录。

变异清单（M1–M8）：
  M1 win_pid≠gamemd_pid                 ⇒ 期望 C4 红（任务指定）
  M2 删 post_close_end 段               ⇒ 期望 C9 红（任务指定）
  M3 verdict=FAIL                       ⇒ 期望 C2 红
  M4 close_delivery.post_err=5 而 post_ok=True ⇒ 期望 C3 红
  M5 timeline.json 删 pre5 键           ⇒ 期望 C6 红
  M6 close_rows 行删 "tick" 键          ⇒ 期望 C7 红
  M7 exit_kind=natural 但删 final_exitcode ⇒ 期望 C10 红
  M8 shots=[]（空段）                    ⇒ 期望 S1 红（验 vacuous-pass）
  M9 C5 尾6精确：rows 截到 6 且 close_rows_n 同步改 6 ⇒ 期望 **不红**（A6 盲区实证）
  M10 battle_tl=[] 且 battle_tl_n 同步改 0 ⇒ 期望不红（登记口径）
  M11 真实 v2 行形态：哨兵不可读 ⇒ row[k]={"state":"page_absent"} dict ⇒ C7 应仍绿（分型正确性）
"""
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

PROBE = Path(r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\_x_channel_probe_20261027.py")
spec = importlib.util.spec_from_file_location("_probe_copy", str(PROBE))
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)

root = Path(tempfile.mkdtemp(prefix="aud_mut_"))
rows_all = []


def fresh(name):
    out, rec = P._fixture(root / name)
    return out, rec


def j(out, rec):
    return {c: ok for c, _, ok, _ in P.judge_artifacts(out, rec)}


def case(name, cid, expect_red, fn):
    out, rec = fresh(name)
    fn(out, rec)
    rr = j(out, rec)
    red = rr.get(cid) is False
    verdict = "OK-抓" if red == expect_red else "BLIND"
    print("[%s] %-10s 期望 %s=%s 实得 red=%s" % (
        "OK " if verdict == "OK-抓" else "!! ", name, cid,
        "红" if expect_red else "不红", red))
    if verdict == "BLIND":
        print("     ⇒ 全表=%s" % rr)
    return verdict == "OK-抓"


def main():
    ok = True
    ok &= case("M1_winpid", "C4", True,
               lambda o, r: r["close_delivery"].update(win_pid=9999))
    def m2(o, r):
        r["shots"] = [s for s in r["shots"] if s["tag"] != "post_close_end"]
    ok &= case("M2_delshot", "C9", True, m2)
    ok &= case("M3_verdict", "C2", True, lambda o, r: r.update(verdict="FAIL"))
    ok &= case("M4_posterr", "C3", True,
               lambda o, r: r["close_delivery"].update(post_err=5))
    def m5(o, r):
        tl = json.loads((o / "timeline.json").read_text(encoding="utf-8"))
        del tl["pre5"]
        (o / "timeline.json").write_text(json.dumps(tl), encoding="utf-8")
    ok &= case("M5_nopre5", "C6", True, m5)
    def m6(o, r):
        tl = json.loads((o / "timeline.json").read_text(encoding="utf-8"))
        for row in tl["close_rows"]:
            row.pop("tick", None)
        (o / "timeline.json").write_text(json.dumps(tl), encoding="utf-8")
    ok &= case("M6_notick", "C7", True, m6)
    ok &= case("M7_naturalnoexit", "C10", True,
               lambda o, r: (r.update(exit_kind="natural"), r.pop("final_exitcode", None)))
    ok &= case("M8_emptyshots", "S1", True, lambda o, r: r.update(shots=[]))
    # M9：A6 盲区实证 —— 期望「不红」（探针确实不红 ⇒ 记录 BLIND-SPOT）
    def m9(o, r):
        P._rewrite_rows(o, r, 6)
    out, rec = fresh("M9_tail6exact")
    m9(out, rec)
    rr = j(out, rec)
    print("[%s] M9_tail6exact 期望 C5=不红(盲区) 实得 red=%s (rows_n=%s)"
          % ("OK " if rr.get("C5") is True else "!! ", rr.get("C5") is False, rec["close_rows_n"]))
    # M10：battle_tl=[] 且计数同步 0 ⇒ 期望 C6 不红（登记口径）
    def m10(o, r):
        tl = json.loads((o / "timeline.json").read_text(encoding="utf-8"))
        tl["battle_tl"] = []
        (o / "timeline.json").write_text(json.dumps(tl), encoding="utf-8")
        r["battle_tl_n"] = 0
    out, rec = fresh("M10_btlempty")
    m10(out, rec)
    rr = j(out, rec)
    print("[%s] M10_btlempty 期望 C6=不红(登记口径) 实得 red=%s"
          % ("OK " if rr.get("C6") is True else "!! ", rr.get("C6") is False))
    # M11：真实 v2 形态哨兵不可读 ⇒ C7 应仍绿（键仍在，值变 dict）
    def m11(o, r):
        tl = json.loads((o / "timeline.json").read_text(encoding="utf-8"))
        tl["close_rows"][5]["frame"] = {"state": "page_absent"}
        tl["close_rows"][6]["hwnd"] = {"state": "read_fail", "detail": {"rpm_err": 299}}
        (o / "timeline.json").write_text(json.dumps(tl), encoding="utf-8")
    out, rec = fresh("M11_triform")
    m11(out, rec)
    rr = j(out, rec)
    print("[%s] M11_triform 期望 C7=不红(键仍在,形态合法) 实得 red=%s"
          % ("OK " if rr.get("C7") is True else "?? ", rr.get("C7") is False))
    print("总计指定必红变异全抓=%s" % ok)
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        rc = main()
    finally:
        shutil.rmtree(root, ignore_errors=True)
    sys.exit(rc)
