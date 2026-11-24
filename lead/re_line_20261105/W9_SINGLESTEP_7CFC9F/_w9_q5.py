# -*- coding: utf-8 -*-
"""W9 / Q5 定谳员自证探针（只读，零真机 / 零采样 / 零注入）。

独立运行：
  python -I -X utf8 D:\\Project\\ra2-campaign-forge\\lead\\re_line_20261105\\W9_SINGLESTEP_7CFC9F\\_w9_q5.py
产出：同目录 _w9_q5_out.txt（脚本自己写，不依赖 shell 重定向）

铁律：零真机 / 零采样注入 / 零活进程读取；只读 gamemd.exe + EXCEPT 件。
唯一写域 = W9_SINGLESTEP_7CFC9F/ 下的 _w9_q5_out.txt。
Engine：e.raw 是 bytes；读字节用 e.rd(va,n)；查指令起始用 va in e.by()；disasm 可能吞异常返回空。
自己实算两个 SHA256 + 自己用 ra2tool.Engine 真读字节 / 真反汇编，不采信前置回件文字结论。
"""
import sys
import hashlib
import datetime
from pathlib import Path

ROOT = r"D:\Project\ra2-campaign-forge"
SWARM = ROOT + r"\lead\goal3t_nightwatch_20261102\swarm_20261104"
EXE = ROOT + r"\ra2youli\gamemd.exe"
EXCEPT = ROOT + (
    r"\out\re_work\work_chain\CONTINUE_20261003\lead\boot_hang_triage_20261018"
    r"\EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt")
OUT = ROOT + r"\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\_w9_q5_out.txt"
VA = 0x7CFC9F

sys.path.insert(0, SWARM)
from ra2tool import Engine  # noqa: E402

_lines = []
def p(s):
    _lines.append(str(s))

# [A] 自己实算 SHA256 + 字节数
raw_exe = Path(EXE).read_bytes()
raw_exc = Path(EXCEPT).read_bytes()
p("[A] SHA256 / 字节数（hashlib 实算，非引用）")
p("  gamemd.exe SHA256 = %s" % hashlib.sha256(raw_exe).hexdigest())
p("  gamemd.exe bytes  = %d" % len(raw_exe))
p("  EXCEPT   SHA256 = %s" % hashlib.sha256(raw_exc).hexdigest())
p("  EXCEPT   bytes  = %d" % len(raw_exc))
p("  回件时刻 = %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# [B] Engine 真跑 + 覆盖率自证
e = Engine()
cov, nins, fails = e.coverage
p("[B] Engine 自证")
p("  e.sha == 自算 exe sha : %s" % (e.sha == hashlib.sha256(raw_exe).hexdigest()))
p("  IMAGEBASE = 0x%X" % e.IB)
p("  COVERAGE = %.12f%% / %d insns / %d resync-fails" % (cov, nins, fails))
p("  .text = [0x%X, 0x%X) raw=0x%X size=0x%X" % (e.TLO, e.THI, e.TB, e.TSZ))

# [C] 崩点字节：e.rd 真读，与 EXCEPT L17 逐字节比对
b = e.rd(VA, 32)
p("[C] 崩点真实字节（e.rd）")
p("  fo(0x7CFC9F) = 0x%X ; VA - 0x400000 = 0x%X" % (e.fo(VA), VA - 0x400000))
p("  e.rd(VA,32) = %s" % " ".join("%02X" % x for x in b))
txt = raw_exc.decode("latin-1")
l17 = [ln for ln in txt.splitlines() if "Bytes at CS:EIP" in ln][0]
hexpart = l17.rsplit(":", 1)[1].strip()
expect = bytes(int(x, 16) for x in hexpart.split()[:32])
p("  EXCEPT L17  = %s" % " ".join("%02X" % x for x in expect))
diffs = [i for i in range(32) if b[i] != expect[i]]
p("  逐字节差异索引 = %s  => %d/32 一致" % (diffs, 32 - len(diffs)))

# [D] 指令起始判定 + 真反汇编前 8 条
p("[D] 指令起始 / 反汇编（真 disasm + by()）")
p("  0x7CFC9F in e.by() = %s" % (VA in e.by()))
bi = e.by().get(VA)
if bi is not None:
    p("  by()[VA] bytes=%s size=%d %s %s" % (bi.bytes.hex(), bi.size, bi.mnemonic, bi.op_str))
ins = e.disasm(VA, 0x30)
p("  e.disasm(VA,0x30) 返回 %d 条" % len(ins))
for i, (a, by, mn, op) in enumerate(ins[:8]):
    p("    #%d 0x%X %-10s %s %s" % (i + 1, a, by, mn, op))

# [E] 函数边界（自己读序言 + func_rets）
p("[E] 函数边界（自己 e.rd 读序言 + e.func_rets）")
p("  e.rd(0x7CFB13,5) = %s" % " ".join("%02X" % x for x in e.rd(0x7CFB13, 5)))
p("  e.rd(0x7CFB12,1) = %s (相邻前一函数 ret)" % e.rd(0x7CFB12, 1).hex())
ret_list, _succ = e.func_rets(0x7CFB13, 0x7CFE1C)
p("  func_rets(0x7CFB13,0x7CFE1C) ret 数 = %d ; 地址 = %s" % (
    len(ret_list), ["0x%X" % r.address for r in ret_list]))
p("  e.rd(0x7CFE1B,1) = %s (唯一 ret)" % e.rd(0x7CFE1B, 1).hex())
p("  函数长度 = 0x%X B (含 ret) / 0x%X B (不含)" % (0x7CFE1C - 0x7CFB13, 0x7CFE1B - 0x7CFB13))

# [F] 崩点前序指令（trap 语义链）—— 真反汇编
p("[F] 崩点前序指令（0x7CFC98 起 0x10 字节）")
for a, by, mn, op in e.disasm(0x7CFC98, 0x10):
    p("    0x%X %-10s %s %s" % (a, by, mn, op))

p("PROBE DONE")
Path(OUT).write_text("\n".join(_lines) + "\n", encoding="utf-8")
print("\n".join(_lines))
print("PROBE DONE -- exit 0 -> " + OUT)
