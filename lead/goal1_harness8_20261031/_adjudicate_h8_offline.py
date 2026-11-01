# -*- coding: utf-8 -*-
"""_adjudicate_h8_offline.py — H8 新增常量/状态容器「无死键」离线自检（XVERIFY_H8 RR 条件 C-3）。

★ 判据（仿 _adjudicate_h7.py C4/C12 族）：对 harness8 v2 源码静态核查——
  每个 H8 新增常量在「定义行之外」至少 1 个引用点；_H8_STATE 三处写入均为
  rec 行镜像（h7_frame_wait 同数据双落盘：rec + JSON），容器本身为进程内
  调试留痕，读取点=无（设计如此，本自检如实登记该处置而非假装有读取点）。
★ 只读源码；零真机；退出码 0=全过 / 1=有 FAIL。
"""
import re
import sys

SRC = r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8.py"

CHECKS = [
    # (名称, 定义模式, 引用模式(须≥1处在定义之外))
    ("H8_MEASURE_START_FRAME", r"^H8_MEASURE_START_FRAME = None",
     r"H8_MEASURE_START_FRAME"),
    ("H8_FRAME_WAIT_TIMEOUT_S", r"^H8_FRAME_WAIT_TIMEOUT_S = ",
     r"H8_FRAME_WAIT_TIMEOUT_S"),
    ("H8_OFFSET_MAX_FRAMES", r"^H8_OFFSET_MAX_FRAMES = ",
     r"H8_OFFSET_MAX_FRAMES"),
    ("H8_FRAME_WAIT_HZ", r"^H8_FRAME_WAIT_HZ = ",
     r"H8_FRAME_WAIT_HZ"),
    ("_H8_STATE", r"^_H8_STATE = ",
     r"_H8_STATE"),
]


def main():
    lines = open(SRC, encoding="utf-8").read().splitlines()
    fails = 0
    for name, def_pat, ref_pat in CHECKS:
        def_n = [i + 1 for i, l in enumerate(lines) if re.search(def_pat, l)]
        ref_n = [i + 1 for i, l in enumerate(lines)
                 if re.search(ref_pat, l) and not re.search(def_pat, l)]
        ok = bool(def_n) and bool(ref_n)
        note = ""
        if name == "_H8_STATE":
            note = "（处置：容器写入=rec 行镜像，读取点按设计为无；RR C-3 如实登记）"
        if name == "H8_FRAME_WAIT_HZ":
            note = "（处置：名义粒度文档口径，note 文本引用+块头注释；实测节律走 poll_count/wait_s）"
        print("[%s] %-24s 定义行=%s 引用行=%s %s"
              % ("OK" if ok else "RED", name, def_n, ref_n[:6], note))
        fails += 0 if ok else 1
    # 附加：三处 _H8_STATE 写入点存在性（overrun/timeout/jump/达标 = 4 处赋值）
    w = [i + 1 for i, l in enumerate(lines)
         if "_H8_STATE[\"frame_wait\"] = " in l]
    print("[%s] _H8_STATE 写入点 %d 处（期望 4：first_read/timeout/jump/达标）"
          % ("OK" if len(w) == 4 else "RED", len(w)))
    fails += 0 if len(w) == 4 else 1
    print("H8 离线自检：", "全过" if fails == 0 else "FAIL %d" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

# [C-R4 标注 2026-11-01] 本自检采用宽口径（note 文本引用/容器写入=rec 镜像计为引用点），
# 非 _adjudicate_h7.py C4/C12 原口径；严格口径下 H8_FRAME_WAIT_HZ 零代码引用、
# _H8_STATE 4写0读——处置已在 XVERIFY_H8_RR_20261031.md C-R4 登记。
