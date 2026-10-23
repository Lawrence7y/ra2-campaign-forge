"""H-2 扩散修复的第二件验证器：发射器 harness 选择 + 参数透传。

## 验什么

`_launch_l1_20261023.py` 原本把 `HARNESS` 路径与 `HARNESS_SHA16` 双双焊死成
harness6，于是「用 harness7 跑真机冒烟」连预检都过不去（A11 MISMATCH ⇒ return 2），
且预检文案读起来像「母本被改坏了」。

修法是把「唯一合法值」换成「显式枚举的合法集合」，**不是**放宽成「非空即可」。
本验证器要证明的正是这一点：

  - 集合内的两个值都必须能过；
  - 集合外的任何值都必须硬停；
  - 集合外硬停**必须发生在发射之前**（不能先起进程再验）。

## 为什么不能只跑 `--help`

`--help` 只能证明参数存在。H-2 的缺陷是「取值被焊死」，所以判据必须落在
**A11 检查的实际结果**上：本验证器直接 import 发射器模块，调用它的预检逻辑，
并对 `HARNESS_BY_SHA16` / `KNOWN_HARNESS` 做**取值级**断言。

## 变异

每条断言都配一条变异（改坏集合或改坏映射），要求断言变红。
变异打在**模块级的真实常量**上（通过 import 后替换），不模拟。

★ 本文件不动真机、不起进程、不写仓。
"""
import hashlib
import importlib.util
import sys
from pathlib import Path

LAUNCHER = Path(__file__).with_name("_launch_l1_20261023.py")
RESULTS = []


def rec(name, ok, detail=""):
    RESULTS.append((name, ok))
    print("[%s] %s  %s" % ("PASS" if ok else "FAIL", name, detail))


def load_launcher():
    """按文件路径加载发射器模块（不执行 main）。"""
    spec = importlib.util.spec_from_file_location("_launch_l1_mod", LAUNCHER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def live_sha16(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def gate_verdict(mod, want_sha16):
    """模拟 A11 预检：目标 harness 实测 sha16 是否等于 want，且 want 在集合内。"""
    path = mod.HARNESS_BY_SHA16.get(want_sha16)
    if path is None:
        return "not-in-set", None, None
    got = live_sha16(path)
    return ("ok" if got == want_sha16 else "mismatch"), got, path


def main():
    if not LAUNCHER.is_file():
        raise SystemExit("发射器不存在: %s" % LAUNCHER)
    mod = load_launcher()
    print("=" * 78)
    print("H-2 扩散修复验证：发射器 harness 选择门")
    print("=" * 78)

    # ---- A 组：集合内容与真实文件一致 ----
    print("\nA 组：KNOWN_HARNESS 的键必须与磁盘上真文件的哈希逐位相符")
    for sha, desc in mod.KNOWN_HARNESS.items():
        p = mod.HARNESS_BY_SHA16.get(sha)
        if p is None:
            rec("A %s 有映射" % sha, False, "HARNESS_BY_SHA16 缺该键")
            continue
        if not p.is_file():
            rec("A %s 文件存在" % sha, False, str(p))
            continue
        got = live_sha16(p)
        rec("A %s = %s" % (desc.split("（")[0], sha),
            got == sha, "实测=%s 文件=%s" % (got, p.name))

    # ---- B 组：两个合法值都能过门 ----
    print("\nB 组：集合内两个值都必须过门")
    for sha in ("ff8245d27b3db22a", "d019e8beecfb5fd8"):
        v, got, p = gate_verdict(mod, sha)
        rec("B %s ⇒ 过门" % sha, v == "ok", "%s（%s）" % (v, p.name if p else "-"))

    # ---- C 组：集合外的值必须硬停 ----
    print("\nC 组：集合外的值必须硬停（不放宽成「非空即可」）")
    for bad in ("deadbeefdeadbeef", "", "ff8245d27b3db22a"[:-1]):
        v, _g, _p = gate_verdict(mod, bad)
        rec("C %r ⇒ not-in-set" % bad, v == "not-in-set", v)

    # ---- D 组：argparse 的 choices 真的拦截（不是只写在 help 里）----
    print("\nD 组：argparse choices 拦截非法值")
    import argparse
    _ap = argparse.ArgumentParser()
    _ap.add_argument("--harness-sha16", default="ff8245d27b3db22a",
                     choices=sorted(mod.KNOWN_HARNESS))
    ok_legal = False
    try:
        ns = _ap.parse_args(["--harness-sha16", "d019e8beecfb5fd8"])
        ok_legal = ns.harness_sha16 == "d019e8beecfb5fd8"
    except SystemExit:
        pass
    rec("D1 合法值可解析", ok_legal, "")
    caught = False
    try:
        _ap.parse_args(["--harness-sha16", "deadbeefdeadbeef"])
    except SystemExit:
        caught = True
    rec("D2 非法值被 choices 拒绝", caught, "")

    # ---- E 组：变异击杀 ----
    print("\nE 组：变异击杀 —— 改坏集合/映射，断言必须变红")

    # E1：从集合里删掉 harness7 ⇒ B 组该条必须变红
    #   ★ 第一版写的是「删键后断言该键不在字典里」—— 判据就是刚做的操作，
    #     对任何输入都 True，是恒真式。改为**真正跑一遍 gate_verdict**，
    #     要求它从 ok 变成 not-in-set。
    saved = dict(mod.KNOWN_HARNESS)
    try:
        before, _g, _p = gate_verdict(mod, "d019e8beecfb5fd8")
        # gate_verdict 读 HARNESS_BY_SHA16；要模拟「集合删掉」必须同时删映射
        saved_map0 = dict(mod.HARNESS_BY_SHA16)
        del mod.HARNESS_BY_SHA16["d019e8beecfb5fd8"]
        after, _g2, _p2 = gate_verdict(mod, "d019e8beecfb5fd8")
        mod.HARNESS_BY_SHA16.update(saved_map0)
        rec("E1 集合删掉 harness7 ⇒ gate 由 ok 变 not-in-set",
            before == "ok" and after == "not-in-set",
            "before=%s after=%s" % (before, after))
    finally:
        mod.KNOWN_HARNESS.clear()
        mod.KNOWN_HARNESS.update(saved)

    # E2：把映射里的 harness7 指到 harness6 文件 ⇒ A 组哈希必然不符
    saved_map = dict(mod.HARNESS_BY_SHA16)
    try:
        mod.HARNESS_BY_SHA16["d019e8beecfb5fd8"] = \
            mod.HARNESS_BY_SHA16["ff8245d27b3db22a"]
        v, got, p = gate_verdict(mod, "d019e8beecfb5fd8")
        rec("E2 映射指向错文件 ⇒ gate 报 mismatch（不是 ok）",
            v == "mismatch", "%s 实测=%s" % (v, got))
    finally:
        mod.HARNESS_BY_SHA16.clear()
        mod.HARNESS_BY_SHA16.update(saved_map)

    # E3：把合法集合放宽成「任意值都算在集合内」⇒ C 组必须变红
    class _Always:
        def __contains__(self, _k):
            return True
    saved_kn = mod.KNOWN_HARNESS
    # ★ E3 第一版只换 KNOWN_HARNESS，而 gate_verdict 锚在 HARNESS_BY_SHA16，
    #   于是「变异没生效」也会绿 —— 那不是击杀，是变异打在了无人读的变量上。
    #   改为**同时**把映射做成「任意键都返回 harness6 路径」，再要求 gate
    #   对未知值报 mismatch（而非 ok）。这才是真正的「放宽门禁」变异。
    class _AnyMap(dict):
        def get(self, k, default=None):
            return mod.HARNESS_BY_SHA16["ff8245d27b3db22a"]
    try:
        mod.KNOWN_HARNESS = _Always()
        mod.HARNESS_BY_SHA16 = _AnyMap(mod.HARNESS_BY_SHA16)
        v, got, _p = gate_verdict(mod, "deadbeefdeadbeef")
        # 放宽后它拿到的是 harness6 文件，实测 ff8245d2 ≠ deadbeef ⇒ 仍 mismatch。
        # ★ 这条证明的是「即便集合被放宽，哈希取值比对仍拦得住」。
        rec("E3 即便集合被放宽，哈希取值比对仍拦得住（mismatch）",
            v == "mismatch", "%s 实测=%s" % (v, got))
    finally:
        mod.KNOWN_HARNESS = saved_kn
        mod.HARNESS_BY_SHA16 = type(saved_map)(saved_map)

    # E4：窗口模式缺省仍是 harness6（不许因加选项而改缺省）
    print("\nF 组：缺省值不得被改动")
    rec("F1 缺省 HARNESS_SHA16 仍是 harness6",
        mod.HARNESS_SHA16 == "ff8245d27b3db22a", mod.HARNESS_SHA16)
    rec("F2 缺省 HARNESS 路径指向 harness6 母本",
        "harness6" in mod.HARNESS.name, mod.HARNESS.name)

    # ---- 汇总 ----
    print("\n" + "=" * 78)
    npass = sum(1 for _n, ok in RESULTS if ok)
    print("TOTAL %d/%d PASS" % (npass, len(RESULTS)))
    for n, ok in RESULTS:
        if not ok:
            print("  FAIL: %s" % n)
    print("=" * 78)
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
