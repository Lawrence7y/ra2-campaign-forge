#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""变异测试：证明 _drive_c2_x_probe_v2.py 的故障注入套件**能红**（不是装饰断言）。

★ 依据本轮铁律（gate-assert-values-not-existence 变种 E/M/O + REVIEW C26-08 第 35 条）：
  「ALL PASS」本身不是证据——必须证明每个 FT 对应一个真实控制流缺陷，注入该缺陷后该 FT 必红。
★ 方法：把 v2 驱动拷到临时文件，逐条应用**源码级回归**（改 fire_arm/finalize/tri），
  跑 `--faulttest`，断言**指定 FT 转红**（其余保持）。杀不掉的变异=该 FT 是装饰⇒本件红。
★ 零游戏、零真启动；只在临时副本上改，**不动交付件本体**。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

V2 = Path(r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\_drive_c2_x_probe_v2.py")
SRC = V2.read_text(encoding="utf-8")

# (标签, 目标 FT 关键词, 原串, 改后串)  —— 每条=一个真实缺陷注入
MUTATIONS = [
    # M1：fire_arm 返回 (dict,...) 元组而非 dict ⇒ FT1「返回单个 dict」必须红
    ("M1_return_tuple", "FT1",
     '    return rec\n\n\nAPPROVED_THIS_ROUND = False',
     '    return rec, rec\n\n\nAPPROVED_THIS_ROUND = False'),
    # M2：投递失败不 TripFail ⇒ FT2「投递失败⇒FAIL」必须红
    ("M2_ignore_post_fail", "FT2 投递失败⇒FAIL",
     '        if not ok_post:\n            raise TripFail("PostMessageW_failed err=%d" % err_post)',
     '        if False:\n            raise TripFail("PostMessageW_failed err=%d" % err_post)'),
    # M3：survivor 也照样删树 ⇒ FT3「残留⇒carrier_retained」必须红
    ("M3_delete_anyway", "FT3 残留⇒carrier_retained",
     '    if rem:\n        rec.update(carrier_retained=True, carrier_deleted=False,\n'
     '                   delete_reason="survivors_under_carrier")\n    else:',
     '    if False:\n        rec.update(carrier_retained=True, carrier_deleted=False,\n'
     '                   delete_reason="survivors_under_carrier")\n    else:'),
    # M4：299 一律当 page_absent（不做 vquery 分型）⇒ FT6b「read_fail 不冒充页缺失」红
    ("M4_299_always_absent", "FT6b",
     '    if mbi is not None and mbi[0] != MEM_COMMIT:\n        return ("page_absent", detail)',
     '    if True:\n        return ("page_absent", detail)'),
    # M5：证据异常不改 verdict（PASS 覆盖失败）⇒ FT11「PARTIAL 非 OK」红
    ("M5_no_partial", "FT11",
     '    if rec["verdict"] == "OK" and (rec.get("evidence_errors") or rec.get("cleanup_errors")):\n'
     '        rec["verdict"] = "PARTIAL"',
     '    if False:\n        rec["verdict"] = "PARTIAL"'),
    # M6：timeline 只写末 6 行（重犯 d09b 缺陷）⇒ FT12「close_rows 全量」红
    ("M6_tail_only", "FT12",
     '            json.dumps({"battle_tl": tl, "pre5": pre5, "close_rows": rows},',
     '            json.dumps({"battle_tl": tl, "pre5": pre5, "close_rows": rows[-6:]},'),
    # M7：menu 臂也跑战斗窗 play_s ⇒ FT7「play_s=0」红
    ("M7_menu_runs_battle", "FT7",
     '           "watch_s": watch_s, "play_s": play_s if arm["mode"] == "battle" else 0}',
     '           "watch_s": watch_s, "play_s": play_s}'),
    # M8：零 close 样本仍算普通不退 ⇒ FT10「零样本⇒FAIL」红
    ("M8_zero_ok", "FT10",
     '        rec["close_rows_n"] = len(rows)\n        if len(rows) == 0:\n            raise TripFail("zero_close_samples")',
     '        rec["close_rows_n"] = len(rows)\n        if False:\n            raise TripFail("zero_close_samples")'),
    # M9：删掉 mkdir 调用与 iterdir 断言（copy-before-mkdir 缺陷回归）。
    #      实测由 FT8 的 phase 断言拦下（copy 阶段 FileNotFoundError⇒phase=copy≠mkdir）。
    #      ⇒ 防线真实存在（间接但可杀）；本条 ft_key=FT8 如实归类，不谎称盲区也不谎称未杀。
    ("M9_copy_before_mkdir", "FT8",
     '        OPS["mkdir"](carrier)\n        made_carrier = True\n'
     '        if any(carrier.iterdir()):\n            raise TripFail("carrier_not_empty_after_mkdir")',
     '        made_carrier = True'),
    # M10：§445 pathlen 闸被短路（if False）⇒ FT13「越界⇒FAIL carrier_pathlen」必须红
    ("M10_pathlen_gate_off", "FT13",
     '        if len(str(carrier)) > CARRIER_PATH_MAX:\n'
     '            raise TripFail("carrier_pathlen:%d>%d" % (len(str(carrier)), CARRIER_PATH_MAX))',
     '        if False:\n'
     '            raise TripFail("carrier_pathlen")'),
]


def run_on(mutated_src):
    with tempfile.TemporaryDirectory(prefix="v2mut_") as td:
        f = Path(td) / "_drive_c2_x_probe_v2.py"
        f.write_text(mutated_src, encoding="utf-8")
        # 测试里 fire_arm 等靠 __file__? 不依赖；faulttest 只读源码常量+替身，可跑副本
        p = subprocess.run([sys.executable, str(f), "--faulttest"],
                           capture_output=True, text=True, timeout=120)
        return p.returncode, (p.stdout or "") + (p.stderr or "")


def main() -> int:
    print("== 交付件基线（应全绿）==")
    rc, out = run_on(SRC)
    print("baseline rc=%d %s" % (rc, out.strip().splitlines()[-1] if out else ""))
    if rc != 0:
        print("!! 基线不绿，变异测试无意义"); return 2

    kills, survivors, uncovered_ok = 0, [], []
    print("\n== 逐变异 ==")
    for label, ft_key, old, new in MUTATIONS:
        if old not in SRC:
            print("[SKIP] %s 原串不在源里（漂移）" % label)
            survivors.append(label + " (anchor-missing)")
            continue
        mutated = SRC.replace(old, new, 1)
        rc2, out2 = run_on(mutated)
        if ft_key is None:
            # 未覆盖变异：期望「套件仍绿」=承认盲区（诚实登记，不算杀）
            still_green = (rc2 == 0)
            note = "套件未拦(诚实盲区)" if still_green else "意外被别处拦"
            (uncovered_ok if still_green else survivors).append(label)
            print("[%s] %-24s rc=%d  %s" % ("NOTE" if still_green else "RED?", label, rc2, note))
            continue
        killed = (rc2 != 0) and any(ln.startswith("[RED]") and ft_key in ln for ln in out2.splitlines())
        if killed:
            kills += 1
            print("[KILL] %-24s 目标 FT「%s」转红 ✓" % (label, ft_key))
        else:
            survivors.append(label)
            redlines = [ln for ln in out2.splitlines() if ln.startswith("[RED]")]
            print("[DEAD] %-24s rc=%d 期望「%s」红，实际=%s ⇒ 该 FT 是装饰！" % (
                label, rc2, ft_key, redlines[:2]))
    print("\n== 变异结论：杀 %d / 存活(装饰) %d / 诚实盲区 %d ==" % (
        kills, len(survivors), len(uncovered_ok)))
    if survivors:
        print("!! 未杀变异=%s ⇒ v2 故障套件对这些缺陷失明，不得放行" % survivors)
        return 1
    print("✓ 每个注入的真实回归都被对应 FT 转红捕获（%d/%d killed，0 装饰，0 盲区）。"
          % (kills, len([m for m in MUTATIONS if m[1] is not None])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
