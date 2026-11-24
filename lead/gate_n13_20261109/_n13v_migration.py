# -*- coding: utf-8 -*-
r"""_n13v_migration.py — 第七步：把改后片段粘进最小样例，实跑「接口不变 + 删文件 FAIL」

两种删文件方式（都要真实删/移，不只是 raise ImportError）：
  M1 把 _n13_predicates.py 临时改名到写域内 _n13v_hidden.py，实跑改后片段；
  M2 把 _g7_predicates.py 的路径指向不存在文件（不移动只读件）。
两者跑完立即还原，并复算指纹确认只读件未改。

改后片段逐字摘自 GATE_N13_QUOTED_ASSERTION.md:124-133（唯一改写：把两处绝对路径
参数化，便于模拟缺文件；第 129/131-132 行逻辑一字未动）。
"""
import hashlib
import importlib.util
import json
import pathlib
import shutil

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_n13_20261109"
N13 = WD / "_n13_predicates.py"
HIDDEN = WD / "_n13v_hidden.py"
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
PUB = ROOT / "lead" / "ledger_bound_20261109" / "LEDGER_BOUND_VOLUME.md"
S609 = ROOT / "lead" / "s604_verdict_entry_20261109" / "_ve_DRAFT_S609.md"

# 改前 3 行（GATE_N13_QUOTED_ASSERTION.md:117-120）
def before(t):
    P = []
    for bad in ['已入账', '已追加', '已生效']:
        if bad in t:
            P.append('含越权断言 ' + bad)
    return {"ok": not P, "problems": P}


# 改后 5 行（GATE_N13_QUOTED_ASSERTION.md:124-133），n13_path/g7_path 可注入
def after(t, n13_path=None, g7_path=None):
    n13_path = str(n13_path or 'D:/Project/ra2-campaign-forge/lead/gate_n13_20261109/_n13_predicates.py')
    g7_path = str(g7_path or 'D:/Project/ra2-campaign-forge/lead/gate_fp7_20261108/_g7_predicates.py')
    P = []
    try:
        import importlib.util as _u
        import pathlib as _p
        if not (_p.Path(n13_path).is_file() and _p.Path(g7_path).is_file()):
            raise ImportError("谓词模块文件缺失")
        _s = _u.spec_from_file_location('_n13', n13_path); _m = _u.module_from_spec(_s); _s.loader.exec_module(_m)
        _g = _u.spec_from_file_location('_g7', g7_path); _g7 = _u.module_from_spec(_g); _g.loader.exec_module(_g7)
        for _p in _m.r13_assertions(t, ['已入账', '已追加', '已生效'], r10_scan=_g7.r10_scan, r12_scan=_g7.r12_scan)[0]:
            P.append(_p)
    except (ImportError, OSError, AttributeError):
        for bad in ['已入账', '已追加', '已生效']:
            if bad in t:
                P.append('含越权断言 ' + bad)
    return {"ok": not P, "problems": P}


def sha(p):
    b = pathlib.Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def main():
    text = PUB.read_text(encoding="utf-8")
    checks = []

    # U1 接口形状：改前/改后都返回 {ok:bool, problems:list}，t/P 变量同名
    rb, ra = before(text), after(text)
    same = (set(rb) == set(ra) == {"ok", "problems"}
            and isinstance(rb["ok"], bool) and isinstance(ra["ok"], bool)
            and isinstance(rb["problems"], list) and isinstance(ra["problems"], list))
    checks.append(("U1 调用方接口不变（同 t / 同 P / 同输出形状）", same,
                   json.dumps({"before": rb, "after": ra}, ensure_ascii=False)))

    # U2 改前 FAIL / 改后 PASS
    checks.append(("U2 改前 FAIL、改后 PASS",
                   rb["ok"] is False and len(rb["problems"]) == 2
                   and ra["ok"] is True and ra["problems"] == [],
                   json.dumps({"before": rb, "after": ra}, ensure_ascii=False)))

    # U3 真断言在改后仍被抓（不放宽判据）
    t_bad = "本笔已于 §605 入账\ngrep 结果：已入账 0 命中"
    r_bad = after(t_bad)
    checks.append(("U4 真断言改后仍 FAIL", r_bad["ok"] is False,
                   json.dumps(r_bad, ensure_ascii=False)))

    # ---- M1：真删 _n13 文件（改名到写域内）----
    n13_before = sha(N13)
    g7_before = sha(G7)
    moved = False
    try:
        shutil.move(str(N13), str(HIDDEN))  # 写域内改名，不触碰只读件
        moved = True
        try:
            r_m1 = after(text)
            checks.append(("M1 删掉 _n13_predicates.py 后返回 ok=false 且 2 条全拦",
                           r_m1["ok"] is False and len(r_m1["problems"]) == 2,
                           json.dumps(r_m1, ensure_ascii=False)))
        except Exception as e:
            checks.append(("M1 删掉 _n13_predicates.py 后返回 ok=false 且 2 条全拦",
                           False, "未返回字典，抛出未捕获异常 %s: %s"
                           % (type(e).__name__, e)))
    finally:
        if moved:
            shutil.move(str(HIDDEN), str(N13))
    checks.append(("M1 还原后 N13 指纹未变", sha(N13) == n13_before,
                   "%s/%d" % sha(N13)))

    # ---- M1b：真删 _n13 文件，且调用方补包 OSError（看是否得到干净 FAIL）----
    moved = False
    try:
        shutil.move(str(N13), str(HIDDEN))
        moved = True
        try:
            r = after(text)
            out = json.dumps(r, ensure_ascii=False)
        except (ImportError, OSError) as e:
            out = "调用方额外捕获 %s: %s（此时门禁无 JSON 输出）" % (type(e).__name__, e)
        checks.append(("M1b 删文件后调用方补包异常的实际结果", True, out))
    finally:
        if moved:
            shutil.move(str(HIDDEN), str(N13))

    # ---- M2：g7 路径指向不存在文件（不移动只读件）----
    try:
        r_m2 = after(text, g7_path='D:/Project/ra2-campaign-forge/lead/gate_n13_20261109/_n13v_NO_SUCH_FILE.py')
        d2 = json.dumps(r_m2, ensure_ascii=False)
        ok2 = r_m2["ok"] is False
    except Exception as e:
        d2 = "未返回字典，抛出未捕获异常 %s: %s" % (type(e).__name__, e)
        ok2 = False
    checks.append(("M2 找不到 _g7_predicates.py 后返回 ok=false", ok2, d2))
    checks.append(("M2 只读 G7 指纹未变", sha(G7) == g7_before, "%s/%d" % sha(G7)))

    # ---- M3：模块存在但依赖缺失（真正抛 ImportError 的情形），看降级分支 ----
    fake = WD / "_n13v_bad_import.py"
    fake.write_text("import _n13v_no_such_dependency_xyz\n", encoding="utf-8")
    try:
        r_m3 = after(text, n13_path=str(fake))
        checks.append(("M3 真 ImportError 时降级全拦", r_m3["ok"] is False and
                       len(r_m3["problems"]) == 2, json.dumps(r_m3, ensure_ascii=False)))
    finally:
        fake.unlink()

    # ---- 只读件收尾指纹 ----
    for rel, expect in [
        ("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", "47bb594b90e1c49cbbd83086468cbadb4bda05458d82cb7808661f975daf0b70"),
        ("lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md", "7770da46b5c684add476ec286673d70d73f332fb5ac286d07cabcdaadc4eac43"),
        ("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", "724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e"),
        ("lead/gate_fp7_20261108/_g7_predicates.py", "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"),
        ("lead/PENDING_DECISIONS.md", "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7"),
        ("lead/GOAL_THREE_TARGETS_20261018.md", "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede"),
    ]:
        s, n = sha(ROOT / rel)
        checks.append(("收尾指纹 " + rel, s == expect, "%s/%d" % (s, n)))
    checks.append(("r9r12/_g9_gate.py 仍 MISSING",
                   not (ROOT / "lead/r9r12_20261109/_g9_gate.py").exists(), "MISSING"))
    checks.append(("§609 草案存在性（只记，不判定）", True,
                   "exists=%s" % S609.is_file()))

    print("=" * 78)
    print("迁移配方最小样例实跑（改后片段逐字粘贴，路径参数化）")
    print("=" * 78)
    for cid, ok, detail in checks:
        print(("PASS" if ok else "FAIL"), cid, "|", detail)
    ok = all(c[1] for c in checks)
    print("N13V_MIGRATION_ALL_PASS =", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
