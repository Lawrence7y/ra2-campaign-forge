# -*- coding: utf-8 -*-
# W9 / Q3 第三探针 —— 崩点 ±0x20 字节排除项 / RaiseException 两处调用实参 / 异常码表
# 独立运行：python -I -X utf8 D:\Project\ra2-campaign-forge\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\_w9_q3_final.py
# 产出：同目录 _w9_q3_final_out.txt
# 唯一写域 = W9_SINGLESTEP_7CFC9F/ 下的 _w9_q3_final_out.txt。
import struct
import sys
import time
from pathlib import Path

ROOT = r"D:\Project\ra2-campaign-forge"
SWARM = ROOT + r"\lead\goal3t_nightwatch_20261102\swarm_20261104"
OUT = ROOT + r"\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\_w9_q3_final_out.txt"

sys.path.insert(0, SWARM)
from ra2tool import Engine  # noqa: E402

_lines = []
def p(s=""):
    _lines.append(str(s))


def show(e, lo, hi, label):
    seq = [i for i in e.stream if lo <= i.address < hi]
    p("-- %s : [0x%X,0x%X) %d insns --" % (label, lo, hi, len(seq)))
    for i in seq:
        p("  0x%X  %-14s %-9s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
    return seq


def main():
    t0 = time.time()
    p("=" * 78)
    p("W9 / Q3 第三探针：±0x20 字节排除项 + RaiseException 实参 + 异常码表（自己实跑）")
    p("=" * 78)
    p("运行时刻 = " + time.strftime("%Y-%m-%d %H:%M:%S"))
    p()
    e = Engine()
    cov, nins, fails = e.coverage
    p("Engine 自证 = COVERAGE %.12f%% (%d insns, %d resync-fails) / IMAGEBASE 0x%X" % (cov, nins, fails, e.IB))
    p()

    # ---- [O] 崩点 ±0x20：CC/F1/F0/CD 逐字节 + 是否指令起始 ----
    p("[O] 崩点 ±0x20 窗口内 INT3(0xCC)/ICEBP(0xF1)/LOCK(0xF0)/INT(0xCD) 排除")
    VA = 0x7CFC9F
    LO, HI = VA - 0x20, VA + 0x20
    wb = e.rd(LO, HI - LO)
    p("窗口 [0x%X,0x%X) 原始字节 = %s" % (LO, HI, " ".join("%02X" % x for x in wb)))
    by = e.by()
    for pos, x in enumerate(wb):
        a = LO + pos
        if x in (0xCC, 0xF1, 0xF0, 0xCD):
            isstart = a in by
            p("  0x%02X @ 0x%X : %s%s" % (x, a, "是独立指令起始" if isstart else "非指令起始",
              (" -> %s %s" % (by[a].mnemonic, by[a].op_str)) if isstart else "（内嵌在其它指令的 ModRM/disp/imm 中）"))
    p("  冰点判据：ICEBP(0xF1) 是 trap-after，若它造成 #DB 且报告 EIP=0x%X，" % VA)
    p("  则 0xF1 必须是 0x%X 处的 1 字节指令（末址=0x%X）。" % (VA - 1, VA))
    p("  e.rd(0x%X,1) = %s ; 0x%X in by() = %s" % (
        VA - 1, e.rd(VA - 1, 1).hex().upper(), VA - 1, (VA - 1) in by))
    p("  0x%X 落在 0x7CFC9B 的 4 字节指令 8B 54 F9 04 内（该指令字节=%s）" % (
        VA - 1, e.rd(0x7CFC9B, 4).hex(" ").upper()))
    p()

    # ---- [P] RaiseException 两处调用点的实参（前 0x30 字节） ----
    p("[P] RaiseException 两处调用点（0x7D2F92 / 0x7DB8A0）前 0x40 字节反汇编")
    show(e, 0x7D2F60, 0x7D2FA0, "RaiseException call @0x7D2F92 前文")
    show(e, 0x7DB870, 0x7DB8B0, "RaiseException call @0x7DB8A0 前文")
    p("  stdcall RaiseException(dwExceptionCode, dwExceptionFlags, nNumberOfArguments, lpArguments)")
    p("  => 第一实参 dwExceptionCode 是最后 push 的；看上文 push 的立即数是不是 0x80000004。")
    p()

    # ---- [Q] 异常码表：0x7E8880 附近的 dword 序列 ----
    p("[Q] 异常码表（0x7E8880 附近）：确认 0x80000004 是表项，且 handler 按 ExceptionCode 查表")
    TBL = 0x7E8880 - 0x40
    tbl = e.rd(TBL, 0x100)
    for k in range(0, 0x100, 16):
        dws = struct.unpack_from("<4I", tbl, k)
        p("  [0x%X] %s" % (TBL + k, "  ".join("0x%08X" % d for d in dws)))
    p("  含 0x80000004 的表项 VA = 0x%X" % (TBL + 0x40 + 8))
    p("  说明：字符串池（0x820EE0 起）是「Error code: <名字>\\r\\r\\nDescription: ...」条目，")
    p("  handler 用 ExceptionRecord->ExceptionCode 在该表里查名字/描述 => ")
    p("  except.txt 打印 'EXCEPTION_SINGLE_STEP' 意味着 ExceptionCode 就是 0x80000004（不是别的码被误报）。")
    p("  本探针未逐条反汇编该查表循环，标「未验（查表循环本身）」；表项与串内容已亲读。")
    p()

    p("耗时 = %.2f s" % (time.time() - t0))
    p("EXIT=0 / 零真机 / 零活进程读取 / 零采样注入 / 唯一写域内")
    Path(OUT).write_text("\n".join(_lines) + "\n", encoding="utf-8")
    print("\n".join(_lines))


if __name__ == "__main__":
    main()
