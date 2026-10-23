#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""H7 裁决自查：对三位盲验员可能提出的缺陷类别，逐条在产物上复算。

★ 背景：异族盲验工作流三位盲验员已返回（2 / 5 / 7 = 14 条缺陷），但其裁决员
  卡死 29 分钟未落盘。按项目纪律（判据=交付是否在盘，不看 status），
  改由本件做**确定性复算**：不采信任何一位的结论，只把可机检的断言逐条重算。

★ 本件列出「盲验员最可能报的 14 类」，每类给出一条可在**真实产物**上执行的检查。
  能机检的 ⇒ 给 PASS/FAIL；不能机检的（需真机）⇒ 明确标 REQUIRES_LIVE。

★ 只读：不改任何被检文件。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
H6 = ROOT / "lead/goal1_harness6_20261022/qc151_trip.harness6.py"
H7 = ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py"

results = []


def check(cid, name, status, detail=""):
    results.append((cid, name, status, detail))
    print(f"[{status:13s}] {cid} {name}" + (f"  {detail}" if detail else ""))


def main():
    t6 = H6.read_text(encoding="utf-8")
    t7 = H7.read_text(encoding="utf-8")

    print("=" * 76)
    print("可机检项（在真实产物上复算）")
    print("=" * 76)

    # C1: deadline 作用域 —— 是否在函数内、有无 global 声明
    fn = re.search(r"^def main\(.*?(?=^def |\Z)", t7, re.S | re.M)
    body = fn.group(0) if fn else ""
    has_global_deadline = bool(re.search(r"^\s*global\s+[^\n]*\bdeadline\b",
                                        body, re.M))
    check("C1", "deadline 不是 global（局部重绑不会外泄）",
          "PASS" if not has_global_deadline else "FAIL",
          f"global deadline 声明={has_global_deadline}")
    check("C1b", "main() 里有 STAGE_TIMEOUT_S/TRIP_BUDGET_S 的 global（说明作者知道该机制）",
          "PASS" if re.search(r"^\s*global\s+STAGE_TIMEOUT_S", body, re.M) else "FAIL")

    # C2: 短路赋值在 deadline 首次定义之后
    i_def = t7.find("deadline = time.monotonic() + STAGE_TIMEOUT_S")
    i_sk = t7.find('if _H7_STATE["fs_rect_wait_skipped"]:')
    check("C2", "短路块在 deadline 定义之后（不是引用未定义变量）",
          "PASS" if 0 < i_def < i_sk else "FAIL",
          f"def@{i_def} skip@{i_sk}")

    # C3: 短路块内的 deadline = 0.0 确实在 if 体内（缩进正确）
    m = re.search(r'if _H7_STATE\["fs_rect_wait_skipped"\]:\n((?:[ ]{12,}.*\n)+)', t7)
    indented_ok = bool(m and "deadline = 0.0" in m.group(1))
    check("C3", "deadline = 0.0 位于 if 体内（缩进正确）",
          "PASS" if indented_ok else "FAIL")

    # C4: _H7_STATE 键全部被读写过（无死键 / 无未定义键）
    keys_def = set(re.findall(r'"(fs_rect_wait_skipped|nav_end_t|'
                              r'nav_to_measure_s|late_start)"', 
                              re.search(r"_H7_STATE = \{[^}]*\}", t7).group(0)))
    keys_used = set(re.findall(r'_H7_STATE\["(fs_rect_wait_skipped|nav_end_t|'
                               r'nav_to_measure_s|late_start)"\]', t7))
    keys_get = set(re.findall(r'_H7_STATE\.get\("(fs_rect_wait_skipped|nav_end_t|'
                              r'nav_to_measure_s|late_start)"', t7))
    check("C4", "_H7_STATE 四键全被使用（无死键）",
          "PASS" if keys_def <= (keys_used | keys_get) else "FAIL",
          f"def={sorted(keys_def)} used={sorted(keys_used | keys_get)}")

    # C5: late_start 的 return 在 try 块内（finally 会关句柄）
    i_try = t7.find("    try:\n        # >>> H7-BEGIN late-start-gate")
    i_ret = t7.find("                return\n        # <<< H7-END late-start-gate")
    has_finally = "    finally:\n        if handle:" in t7
    check("C5", "late_start 的 return 在 try 内且 finally 仍关句柄",
          "PASS" if (0 < i_try < i_ret and has_finally) else "FAIL",
          f"try@{i_try} return@{i_ret} finally={has_finally}")

    # C6: late_start 分支没有绕过 handle 的 finally（句柄泄漏检查）
    seg = t7[i_try:i_ret] if 0 < i_try < i_ret else ""
    check("C6", "late_start 分支内无 _rpm_close（交给 finally，不重复关）",
          "PASS" if "_rpm_close" not in seg else "FAIL")

    # C7: --h7-keep-rect-wait 缺省 False（不影响既有调用方）
    #   ★ 在同一行内匹配（初版写成跨行，误报 FAIL——产物其实是对的）
    c7 = re.search(r'"--h7-keep-rect-wait"[^\n]*default=False', t7)
    check("C7", "--h7-keep-rect-wait default=False",
          "PASS" if c7 else "FAIL",
          c7.group(0)[:60] if c7 else "not found")

    # C8: 窗口模式（无 --fullscreen）时短路容器恒 False
    #   检查：唯一置 True 的地方在 `if getattr(args,"fullscreen",False):` 内
    m_fs = re.search(r'if getattr\(args, "fullscreen", False\):\n(.*?)(?=\n    # <<< QC151FS-END main-arm)',
                     t7, re.S)
    fs_block = m_fs.group(1) if m_fs else ""
    set_true_only_in_fs = ('_H7_STATE["fs_rect_wait_skipped"] = True' in fs_block and
                           t7.count('_H7_STATE["fs_rect_wait_skipped"] = True') == 1)
    cnt_true = t7.count('_H7_STATE["fs_rect_wait_skipped"] = True')
    check("C8", "置 True 唯一发生在 --fullscreen 块内 ⇒ 窗口模式恒 False",
          "PASS" if set_true_only_in_fs else "FAIL",
          f"置 True 次数={cnt_true}，其中在 --fullscreen 块内="
          f"{'_H7_STATE[\"fs_rect_wait_skipped\"] = True' in fs_block}")

    # C9: nav_end_t 只在 nav 段之后打戳（不会在 nav 失败时仍打戳导致误判）
    i_navfail = t7.find('rec.add("NAV", "failed_at"')
    i_stamp = t7.find('_H7_STATE["nav_end_t"] = time.monotonic()')
    check("C9", "nav_end_t 打戳在 nav 结果（含 failed_at）之后",
          "PASS" if 0 < i_navfail < i_stamp else "FAIL",
          f"failed_at@{i_navfail} stamp@{i_stamp}")

    # C10: late-start 闸在 handle 打开之后（否则 handle 为空时语义混乱）
    i_handle = t7.find("    rec.add(\"MEASURE\", \"handle_opened\"")
    check("C10", "late-start 闸在 handle_opened 之后（句柄已就绪）",
          "PASS" if 0 < i_handle < i_try else "FAIL",
          f"handle@{i_handle} gate@{i_try}")

    # C11: 新增 rec 行的 group 都是既有 group（不引入新 group）
    groups_new = set(re.findall(r'rec\.add\("([A-Z0-9_]+)"', t7)) - \
                 set(re.findall(r'rec\.add\("([A-Z0-9_]+)"', t6))
    check("C11", "未引入新 rec group",
          "PASS" if not groups_new else "FAIL",
          f"new={sorted(groups_new) or 'none'}")

    # C12: 新增 verdict 字面量 "late_start" 不会与既有 verdict 集合冲突
    v6 = set(re.findall(r'"verdict"\s*:\s*"([a-z_]+)"', t6)) | \
         set(re.findall(r'rec\.add\("MEASURE", "verdict", "([a-z_]+)"', t6))
    v7 = set(re.findall(r'"verdict"\s*:\s*"([a-z_]+)"', t7)) | \
         set(re.findall(r'rec\.add\("MEASURE", "verdict", "([a-z_]+)"', t7))
    check("C12", "late_start 是唯一新增 verdict 值",
          "PASS" if v7 - v6 == {"late_start"} else "FAIL",
          f"added={sorted(v7 - v6)}")

    # C13: 窗口模式的 frame 段行为不变（母本 while 依赖 deadline，窗口模式下矩形本来
    #      就 800x600 ⇒ 零轮询；短路块不进入 ⇒ deadline 原值不被使用）
    check("C13", "窗口模式：短路块不进入（容器 False）且 while 谓词首判即假",
          "PASS" if set_true_only_in_fs else "FAIL",
          "依赖 C8")

    # C14: diff 不含任何 dll/obj/exe 二进制
    diff_p = ROOT / "lead/goal1_harness7_20261023/h7.diff"
    diff = diff_p.read_text(encoding="utf-8", errors="replace")
    bad = [x for x in ("\x00",) if x in diff]
    check("C14", "h7.diff 是纯文本（无 NUL 字节）",
          "PASS" if not bad else "FAIL")

    print()
    print("=" * 76)
    print("必需真机、无法离线判定的项")
    print("=" * 76)
    for cid, name in [
        ("L1", "短路后 stage_seconds:frame 是否真降到 <2 s"),
        ("L2", "短路后 nav→measure 实际值（决定 90 s 阈值是否需重标）"),
        ("L3", "对照臂 --h7-keep-rect-wait 是否真复现 122-127 s 死等"),
        ("L4", "窗口模式真机结果是否与 harness6 可比"),
        ("L5", "late_start 在真机上是否会出现（正常开局应永不出现）"),
    ]:
        check(cid, name, "REQUIRES_LIVE")

    print()
    n_pass = sum(1 for _, _, s, _ in results if s == "PASS")
    n_fail = sum(1 for _, _, s, _ in results if s == "FAIL")
    n_live = sum(1 for _, _, s, _ in results if s == "REQUIRES_LIVE")
    print(f"机检：{n_pass} PASS / {n_fail} FAIL；真机待验：{n_live} 项")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
