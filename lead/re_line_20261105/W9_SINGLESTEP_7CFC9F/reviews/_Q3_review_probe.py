# -*- coding: utf-8 -*-
# 独立复核员·Q3 复核探针 —— 只读；不改既有文件；唯一写域 reviews/
# 运行：python -I -X utf8 D:\Project\ra2-campaign-forge\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\reviews\_Q3_review_probe.py
# 产出：同目录 _Q3_review_probe_out.txt（脚本自己写）
#
# 目的：亲自重跑 Q3 的关键字节读 / 反汇编 / SHA256 计算，而不是采信 Q3 的探针输出。
# 零真机 / 零活进程读取 / 零采样注入。
# 注：全仓 except_post_*.txt 哈希比对由独立 Bash 命令（GNU find + sha256sum）完成，
#     见复核正文；本探针不调用任何子进程。
import hashlib
import os
import re
import struct
import sys
import time
from pathlib import Path

ROOT = r"D:\Project\ra2-campaign-forge"
W9 = ROOT + r"\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F"
SWARM = ROOT + r"\lead\goal3t_nightwatch_20261102\swarm_20261104"
EXE = ROOT + r"\ra2youli\gamemd.exe"
EXCEPT = (ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\boot_hang_triage_20261018"
          + r"\EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt")
Q3MD = W9 + r"\Q3_MECHANISM.md"
OUT = W9 + r"\reviews\_Q3_review_probe_out.txt"

sys.path.insert(0, SWARM)
from ra2tool import Engine  # noqa: E402

_L = []
def p(s=""):
    _L.append(str(s))


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest(), os.path.getsize(path)


def main():
    t0 = time.time()
    p("=" * 78)
    p("独立复核员·Q3 复核探针（自己实跑，非引用 Q3 探针输出）")
    p("运行时刻 = " + time.strftime("%Y-%m-%d %H:%M:%S"))
    p("python = " + sys.version.replace("\n", " "))
    p("=" * 78)

    # ---------- [1] 两个 SHA256 自己实算 ----------
    p("[1] 两个 SHA256 / 字节数（hashlib 实算，绝对路径）")
    es, en = sha256_of(EXE)
    xs, xn = sha256_of(EXCEPT)
    p("gamemd.exe  sha256 = " + es + " ; bytes = " + str(en))
    p("EXCEPT 件   sha256 = " + xs + " ; bytes = " + str(xn))
    p()

    # ---------- [2] 回件头部是否含两个哈希 + 字节数 + COVERAGE ----------
    p("[2] 回件头部（Q3_MECHANISM.md:1-5 逐行读，检查两个 SHA 是否真在头部）")
    q3lines = Path(Q3MD).read_text(encoding="utf-8").splitlines()
    for i in range(0, 6):
        p("  Q3_MECHANISM.md:%d | %s" % (i + 1, q3lines[i]))
    head = "\n".join(q3lines[:5])
    p("  头部含 gamemd.exe SHA256  = " + str(es in head))
    p("  头部含 EXCEPT 件 SHA256    = " + str(xs in head))
    p("  头部含 字节数 4825360       = " + str("4825360" in head))
    p("  头部含 字节数 26405         = " + str("26405" in head))
    p("  头部含 COVERAGE             = " + str("COVERAGE" in head))
    p("  头部含 IMAGEBASE 0x400000   = " + str("0x400000" in head))
    p("  头部含 回件时刻             = " + str("回件时刻" in head))
    p()

    # ---------- [3] Engine 自证 + 崩点原始字节/反汇编 ----------
    e = Engine()
    cov, nins, fails = e.coverage
    p("[3] Engine 自证（自己实例化）")
    p("  IMAGEBASE = 0x%X ; COVERAGE = %.12f%% ; insns = %d ; resync fails = %d" % (
        e.IB, cov, nins, fails))
    p("  .text = [0x%X,0x%X) raw=0x%X size=0x%X" % (e.TLO, e.THI, e.TB, e.TSZ))
    VA = 0x7CFC9F
    p("[3a] 崩点原始字节（自己 e.rd）")
    b32 = e.rd(VA, 32)
    p("  fo(0x7CFC9F) = 0x%X" % e.fo(VA))
    p("  e.rd(0x7CFC9F,32) = " + " ".join("%02X" % x for x in b32))
    exc_lines = Path(EXCEPT).read_text(encoding="utf-8", errors="replace").splitlines()
    byt = next(L for L in exc_lines if "Bytes at CS:EIP" in L)
    hexpart = byt.split(":", 1)[1]
    ev = [int(x, 16) for x in re.findall(r"\b[0-9A-Fa-f]{2}\b", hexpart)]
    p("  EXCEPT Bytes 行抽出 %d 字节 = %s" % (len(ev), " ".join("%02X" % x for x in ev)))
    p("  磁盘 vs 证据件逐字节差异索引 = %s" % [i for i in range(32) if b32[i] != ev[i]])
    p("  0x7CFC9F in e.by() = %s" % (VA in e.by()))
    p("  by()[0x7CFC9F] = %s %s (size=%d)" % (
        e.by()[VA].mnemonic, e.by()[VA].op_str, e.by()[VA].size))
    p("[3b] 崩点前 6 条指令（自己 e.disasm）—— 检查 0x7CFC9B 末址 = 0x7CFC9F")
    d = e.disasm(VA - 0x18, 0x18)
    for a, hx, mn, op in d:
        p("  0x%X  %-12s %-8s %s  (末址=0x%X)" % (a, hx, mn, op, a + len(hx) // 2))
    p()

    # ---------- [4] EFlags=0x286 逐位（自己算） + 证据件字段普查 ----------
    p("[4] EFlags=0x286 逐位（自己位运算，不采信旧件）")
    eflags = 0x286
    p("  置位 bits = %s" % [b for b in range(22) if (eflags >> b) & 1])
    p("  TF(bit8)=%d IF(bit9)=%d RF(bit16)=%d VM(bit17)=%d SF(bit7)=%d ZF(bit6)=%d" % (
        (eflags >> 8) & 1, (eflags >> 9) & 1, (eflags >> 16) & 1,
        (eflags >> 17) & 1, (eflags >> 7) & 1, (eflags >> 6) & 1))
    p("[4b] 证据件字段普查（DR6/DR0/ExceptionInformation/ExceptionAddress/CONTEXT）")
    toks = ["Dr0", "Dr1", "Dr2", "Dr3", "Dr6", "Dr7", "DR0", "DR6", "DR7",
            "ExceptionInformation", "ExceptionFlags", "ExceptionRecord", "NumberParameters",
            "ExceptionAddress", "CONTEXT", "EFlags"]
    for t in toks:
        hits = [i + 1 for i, L in enumerate(exc_lines) if t in L]
        p("  %-24s -> %s" % (t, hits if hits else "[] (全文零命中)"))
    p()

    # ---------- [5] 决定性：handler 打印 EFlags 从 [ebp+0xC0] 取（自己 e.disasm） ----------
    p("[5] handler EFlags printf 取数指令（自己 e.disasm(0x4C8C63,0x18)，不用 Q3 探针输出）")
    for a, hx, mn, op in e.disasm(0x4C8C63, 0x18):
        p("  0x%X  %-12s %-8s %s" % (a, hx, mn, op))
    p("[5b] 全组 10 个寄存器取数指令（自己 e.disasm(0x4C8B79,0xE0) 抓 [ebp+disp]）")
    regmap = {}
    for a, hx, mn, op in e.disasm(0x4C8B79, 0xE0):
        m = re.search(r"\[ebp \+ 0x([0-9a-f]+)\]", op)
        if m and mn == "mov":
            d = int(m.group(1), 16)
            if d not in regmap:
                regmap[d] = (a, hx, mn, op)
    for d in sorted(regmap):
        a, hx, mn, op = regmap[d]
        p("  +0x%03X : 0x%X  %-12s %-8s %s" % (d, a, hx, mn, op))
    p("  [ebp+0xC0] 是否出现 = " + str(0xC0 in regmap) + " -> " + str(regmap.get(0xC0)))
    p("[5c] 格式串亲读")
    p("  e.rd(0x821E50,16) = " + repr(e.rd(0x821E50, 16)))
    p("  e.rd(0x820F74,110) = " + repr(e.rd(0x820F74, 110)))
    p("[5d] IAT 解析（自己 e.resolve_iat）")
    for va in (0x7E115C, 0x7E1160, 0x7E11B4, 0x7E12C0):
        p("  0x%X -> %s" % (va, e.resolve_iat(va)))
    p()

    # ---------- [6] 异常码表 0x7E8880 + 0x80000003 独立表项 ----------
    p("[6] 异常码表亲读（自己 e.rd）")
    p("  e.rd(0x7E8840,8)  = " + e.rd(0x7E8840, 8).hex(" ").upper()
      + "  (dwords = " + " ".join("0x%08X" % x for x in struct.unpack_from("<2I", e.rd(0x7E8840, 8), 0)) + ")")
    p("  e.rd(0x7E8880,8)  = " + e.rd(0x7E8880, 8).hex(" ").upper()
      + "  (dwords = " + " ".join("0x%08X" % x for x in struct.unpack_from("<2I", e.rd(0x7E8880, 8), 0)) + ")")
    p("  证据件 :1-3 = " + repr(exc_lines[0:3]))
    p()

    # ---------- [7] 候选④ ICEBP：0x7CFC9E 字节 + ±0x20 窗口 F0/F1 位置 ----------
    p("[7] ICEBP/0xF1 排除（自己 e.rd + e.by）")
    p("  e.rd(0x7CFC9E,1) = " + e.rd(0x7CFC9E, 1).hex().upper()
      + " ; 0x7CFC9E in by() = " + str(0x7CFC9E in e.by()))
    p("  e.rd(0x7CFC9B,4) = " + e.rd(0x7CFC9B, 4).hex(" ").upper())
    LO, HI = VA - 0x20, VA + 0x20
    wb = e.rd(LO, HI - LO)
    p("  窗口 [0x%X,0x%X) = %s" % (LO, HI, " ".join("%02X" % x for x in wb)))
    for pos, x in enumerate(wb):
        if x in (0xCC, 0xF0, 0xF1, 0xCD):
            a = LO + pos
            p("  0x%02X @ 0x%X : in by() = %s" % (x, a, a in e.by()))
    p()

    # ---------- [8] 候选③ RaiseException：IAT 调用点 / 全 .text 立即数 0x80000004 ----------
    p("[8] 候选③（自己单遍 stream 扫描，不采信 Q3 探针输出）")
    imm_hits = []
    iat_calls = []
    for i in e.stream:
        try:
            for op in i.operands:
                if op.type == 2 and (op.imm & 0xFFFFFFFF) == 0x80000004:
                    imm_hits.append((i.address, i.mnemonic, i.op_str))
                if op.type == 3 and op.mem.base == 0 and op.mem.index == 0 \
                        and (op.mem.disp & 0xFFFFFFFF) == 0x7E12C0 and i.mnemonic.startswith("call"):
                    iat_calls.append((i.address, i.mnemonic, i.op_str))
        except Exception:
            pass
    p("  全 .text 立即数 == 0x80000004 的指令数 = %d ; %s" % (len(imm_hits), imm_hits[:12]))
    p("  call [0x7E12C0] 的指令数 = %d ; %s" % (len(iat_calls), [(hex(a), m, o) for a, m, o in iat_calls]))
    p("  e.rd(0x7F9928,32) = " + e.rd(0x7F9928, 32).hex(" ").upper())
    p("  首 dword = 0x%08X" % struct.unpack_from("<I", e.rd(0x7F9928, 4), 0)[0])
    p("  e.rd(0x7C9484,8) = " + e.rd(0x7C9484, 8).hex(" ").upper())
    for a, hx, mn, op in e.disasm(0x7C9484, 8):
        p("    0x%X  %-12s %-8s %s" % (a, hx, mn, op))
    p("[8b] 全 .text 直接 call/jmp 落点 == 0x7CFC9F（自己单遍 stream）")
    targets = []
    for i in e.stream:
        try:
            if i.mnemonic.startswith("call") or i.mnemonic.startswith("jmp"):
                if i.operands and i.operands[0].type == 2 \
                        and (i.operands[0].imm & 0xFFFFFFFF) == VA:
                    targets.append((i.address, i.mnemonic, i.op_str))
        except Exception:
            pass
    p("  direct call/jmp targets == 0x7CFC9F : %d %s" % (len(targets), targets))
    p()

    # ---------- [9] 导入表调试/异常相关项（自己解析，不采信 Q3） ----------
    p("[9] 导入表（自己 PE 解析）")
    dd = e.opt + 96
    imp_rva = struct.unpack_from("<I", e.raw, dd + 8)[0]
    o = e.fo(e.IB + imp_rva)
    names = []
    k = 0
    while True:
        d = e.raw[o + k * 20: o + k * 20 + 20]
        if len(d) < 20 or d == b"\0" * 20:
            break
        oft, _ts, _fc, name_rva, ft = struct.unpack_from("<IIIII", d, 0)
        thunk = oft or ft
        to = e.fo(e.IB + thunk)
        j = 0
        while True:
            tv = struct.unpack_from("<I", e.raw, to + j * 4)[0]
            if tv == 0:
                break
            if not (tv & 0x80000000):
                ho = e.fo(e.IB + tv + 2)
                names.append(e.raw[ho:e.raw.index(b"\0", ho)].decode("ascii", "replace"))
            j += 1
        k += 1
    p("  导入函数总数 = %d" % len(names))
    for probe in ("SetThreadContext", "GetThreadContext", "RaiseException",
                  "SetUnhandledExceptionFilter", "UnhandledExceptionFilter",
                  "AddVectoredExceptionHandler", "IsDebuggerPresent",
                  "DebugActiveProcess", "SuspendThread"):
        p("  %-32s = %s" % (probe, probe in names))
    p()

    # ---------- [10] Esi/Edi 语义链（自己反汇编） ----------
    p("[10] Esi/Edi 语义（自己 e.disasm 函数头 + 立即数扫描限定窗口）")
    p("  e.rd(0x7CFB13,5) = " + e.rd(0x7CFB13, 5).hex(" ").upper()
      + " ; e.rd(0x7CFB12,1) = " + e.rd(0x7CFB12, 1).hex().upper())
    for a, hx, mn, op in e.disasm(0x7CFB33, 0x20):
        p("  0x%X  %-12s %-8s %s" % (a, hx, mn, op))
    imm7f = []
    immff = []
    for i in e.stream:
        if not (0x7CFB13 <= i.address < VA):
            continue
        try:
            for op in i.operands:
                if op.type == 2:
                    v = op.imm & 0xFFFFFFFF
                    if v == 0x7FFFFFFF:
                        imm7f.append((i.address, i.mnemonic, i.op_str))
                    if v == 0xFFFFFFFF:
                        immff.append((i.address, i.mnemonic, i.op_str))
        except Exception:
            pass
    p("  窗口 [0x7CFB13,0x7CFC9F) 内立即数 0x7FFFFFFF = %d %s" % (len(imm7f), imm7f))
    p("  窗口 [0x7CFB13,0x7CFC9F) 内立即数 0xFFFFFFFF = %d %s" % (
        len(immff), [(hex(a), m, o) for a, m, o in immff]))
    p()

    # ---------- [11] 回件「反汇编地址 + 原始字节」支撑普查 ----------
    p("[11] 回件结论支撑抽样：逐条检查是否有「反汇编地址 + 原始字节」")
    checks = [
        ("3.2 EFlags 取数", ["0x4C8C63", "8b8dc0000000", "0x4C8C6E", "68501e8200"]),
        ("4.3 EIP 退化性", ["0x7CFC98", "8b4df4", "0x7CFC9B", "8b54f904", "0x7CFC9F", "8b0a"]),
        ("6.1 Esi 链", ["0x7CFB45", "83ceff", "0x7CFB48", "d3ee"]),
        ("6.2 Edi 链", ["0x7CFC68", "33ff", "0x7CFC95", "47"]),
        ("4.1 异常码表", ["0x7E8880", "04 00 00 80"]),
        ("5(3) RaiseException 模板", ["0x7F9928", "0xE06D7363", "0x7D2F92"]),
        ("5(3) 返回链", ["0x7C9484", "E8 8A 66 00 00"]),
        ("5(4) ICEBP", ["0x7CFC9E", "0xF0@0x7CFCA3", "0xF1@0x7CFCA5"]),
    ]
    body = "\n".join(q3lines)
    for label, needles in checks:
        p("  %-24s : %s" % (label, {n: (n in body) for n in needles}))
    p()

    p("耗时 = %.2f s" % (time.time() - t0))
    p("EXIT=0 / 零真机 / 零活进程读取 / 零采样注入 / 唯一写域 reviews/")
    Path(OUT).write_text("\n".join(_L) + "\n", encoding="utf-8")
    print("\n".join(_L))


if __name__ == "__main__":
    main()
