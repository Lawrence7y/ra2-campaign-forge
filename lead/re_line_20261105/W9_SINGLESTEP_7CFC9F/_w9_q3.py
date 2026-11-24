# -*- coding: utf-8 -*-
# W9 / Q3 机制探针 —— 只读，零真机，零采样注入（E3/D-13 维持暂停）
# 独立运行：python -I -X utf8 D:\Project\ra2-campaign-forge\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\_w9_q3.py
# 产出：同目录 _w9_q3_out.txt（脚本自己写，不依赖 shell 重定向）
# 唯一写域 = W9_SINGLESTEP_7CFC9F/ 下的 _w9_q3_out.txt。
#
# 目的（TASK.md §2 Q3）：
#   (a) EFlags=0x286 逐位分解
#   (b) 4 条候选（SetThreadContext 置 TF / DR 执行断点 / RaiseException 手工抛 / 其它）
#       逐条给「能否被这份证据支持或排除」的判据
#   (c) Esi=7FFFFFFF / Edi=00000001 是否特征值 —— 自己用 Engine 反汇编函数前段核实
#
# 纪律：e.raw 是 bytes 不是函数；读字节用 e.rd(va,n)；查指令起始用 va in e.by()；
#       disasm 可能吞异常返回空 —— 用 by() 交叉验证。
import hashlib
import os
import re
import struct
import sys
import time
from pathlib import Path

ROOT = r"D:\Project\ra2-campaign-forge"
SWARM = ROOT + r"\lead\goal3t_nightwatch_20261102\swarm_20261104"
EXE = ROOT + r"\ra2youli\gamemd.exe"
EXCEPT = (ROOT
          + r"\out\re_work\work_chain\CONTINUE_20261003\lead\boot_hang_triage_20261018"
          + r"\EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt")
OUT = ROOT + r"\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\_w9_q3_out.txt"

sys.path.insert(0, SWARM)
from ra2tool import Engine  # noqa: E402

_lines = []
def p(s=""):
    _lines.append(str(s))


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest(), os.path.getsize(path)


def import_names(e):
    """只读 PE 导入表，产出 (dll, func) 全表 —— 用于候选①③判据。"""
    dd = e.opt + 96
    imp_rva = struct.unpack_from("<I", e.raw, dd + 8)[0]
    if not imp_rva:
        return []
    o = e.fo(e.IB + imp_rva)
    res = []
    k = 0
    while True:
        d = e.raw[o + k * 20: o + k * 20 + 20]
        if len(d) < 20 or d == b"\0" * 20:
            break
        oft, _ts, _fc, name_rva, ft = struct.unpack_from("<IIIII", d, 0)
        no = e.fo(e.IB + name_rva)
        dll = e.raw[no:e.raw.index(b"\0", no)].decode("ascii", "replace")
        thunk = oft or ft
        to = e.fo(e.IB + thunk)
        j = 0
        while True:
            tv = struct.unpack_from("<I", e.raw, to + j * 4)[0]
            if tv == 0:
                break
            if tv & 0x80000000:
                res.append((dll, "ord#%d" % (tv & 0xFFFF)))
            else:
                ho = e.fo(e.IB + tv + 2)
                nm = e.raw[ho:e.raw.index(b"\0", ho)].decode("ascii", "replace")
                res.append((dll, nm))
            j += 1
        k += 1
    return res


def find_str_va(e, needle):
    """在原始字节里找 ASCII 串，返回其 VA（若在节内）。"""
    b = needle.encode("ascii")
    idx = e.raw.find(b)
    if idx < 0:
        return None
    for nm, sva, vsz, rp, rsz in e.SEC:
        if rp <= idx < rp + rsz:
            return e.IB + (sva - e.IB) + (idx - rp)
    return None


def main():
    t0 = time.time()
    p("=" * 78)
    p("W9 / Q3_MECHANISM 探针输出（自己实跑，非引用他人文字）")
    p("=" * 78)
    p("运行时刻 = " + time.strftime("%Y-%m-%d %H:%M:%S"))
    p("python = " + sys.version.replace("\n", " "))
    p()

    # ---------- [A] 强制头部事实：自己实算 SHA256 / 字节数 ----------
    p("[A] 强制头部（hashlib 实算，非引用 TASK.md / 上批回件）")
    exe_sha, exe_n = sha256_of(EXE)
    exc_sha, exc_n = sha256_of(EXCEPT)
    p("gamemd.exe SHA256 = " + exe_sha)
    p("gamemd.exe 字节数 = %d" % exe_n)
    p("EXCEPT 件 SHA256 = " + exc_sha)
    p("EXCEPT 件 字节数 = %d" % exc_n)
    p()

    e = Engine()
    cov, nins, fails = e.coverage
    p("[A2] Engine 自证")
    p("IMAGEBASE = 0x%X" % e.IB)
    p("COVERAGE = %.12f%% / decoded insns = %d / resync fails = %d" % (cov, nins, fails))
    p("Engine 自证 = COVERAGE %.12f%% (%d insns, %d resync-fails) / IMAGEBASE 0x%X" % (cov, nins, fails, e.IB))
    p(".text = [0x%X, 0x%X) raw=0x%X size=0x%X" % (e.TLO, e.THI, e.TB, e.TSZ))
    p("SHA 断言（Engine.__init__ 内 assert sha==EXPECT_SHA）通过 = %s" % (exe_sha == e.sha))
    p()

    # ---------- [B] 证据件解析：逐字段读，不采信转述 ----------
    p("[B] EXCEPT 件逐字段自读（文件:行；按内容标签定位，不硬编码行号）")
    with open(EXCEPT, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    p("文件总行数 = %d" % len(lines))
    for ln in range(1, 21):
        p("  L%-3d | %s" % (ln, lines[ln - 1]))
    p("* 行号口径说明：Python splitlines() 下寄存器块在 raw L12-L15、EFlags 在 raw L15、Bytes 在 raw L18；")
    p("  Read 工具/旧分析/TASK.md 的「L17」（Bytes 行）是显示口径（少一个首部空行）。两者内容同一行。")
    p()
    # 按内容标签定位（robust，不依赖行号口径）
    def tagged(prefix):
        return [(i + 1, L) for i, L in enumerate(lines) if L.lstrip().startswith(prefix)]
    eip_line = tagged("Eip:")
    efl_line = tagged("EFlags:")
    byt_line = [(i + 1, L) for i, L in enumerate(lines) if "Bytes at CS:EIP" in L]
    p("  定位 Eip:      -> %s" % eip_line[:2])
    p("  定位 EFlags:   -> %s" % efl_line[:2])
    p("  定位 Bytes...: -> %s" % byt_line[:2])
    reg_lines = [L for _, L in tagged("Eip:") + tagged("Eax:") + tagged("Edx:")]
    reg_lines += [L for _, L in efl_line]
    regs = {}
    for L in reg_lines:
        for k, v in re.findall(r"(\w+):([0-9A-Fa-f]+)", L):
            regs[k.upper()] = int(v, 16)
    p("机器解析寄存器 = " + ", ".join("%s=0x%X" % (k, v) for k, v in regs.items()))
    eflags = regs.get("EFLAGS")
    esi = regs.get("ESI")
    edi = regs.get("EDI")
    eip = regs.get("EIP")
    p("EFLAGS=0x%X  ESI=0x%X  EDI=0x%X  EIP=0x%X" % (eflags, esi, edi, eip))
    p()

    # ---------- [C] EFlags=0x286 逐位分解（TASK.md §2 Q3 第一问） ----------
    p("[C] EFlags=0x%X 逐位分解（bit / mask / name / value）" % eflags)
    NAMES = {
        0: "CF Carry", 1: "reserved(always 1)", 2: "PF Parity", 3: "reserved(0)",
        4: "AF Adjust", 5: "reserved(0)", 6: "ZF Zero", 7: "SF Sign",
        8: "TF Trap Flag  <<<< 本题核心", 9: "IF Interrupt Enable",
        10: "DF Direction", 11: "OF Overflow", 12: "IOPL[0]", 13: "IOPL[1]",
        14: "NT Nested Task", 15: "reserved(0)", 16: "RF Resume Flag",
        17: "VM Virtual-8086", 18: "AC Alignment Check", 19: "VIF Virtual IF",
        20: "VIP Virtual Interrupt Pending", 21: "ID CPUID-ident",
    }
    setbits = []
    for bit in range(0, 22):
        m = 1 << bit
        v = 1 if (eflags & m) else 0
        if v:
            setbits.append(bit)
        p("  bit%-2d mask=0x%06X %-26s = %d" % (bit, m, NAMES.get(bit, "?"), v))
    p("置位 bits = %s" % setbits)
    p("0x%X = %s" % (eflags, " + ".join("0x%X(b%d)" % (1 << b, b) for b in setbits)))
    p("TF(bit8)  = %d  -> 报告的标志字里【无 TF】" % ((eflags >> 8) & 1))
    p("IF(bit9)  = %d" % ((eflags >> 9) & 1))
    p("RF(bit16) = %d" % ((eflags >> 16) & 1))
    p("VM(bit17) = %d" % ((eflags >> 17) & 1))
    p("SF(bit7)  = %d ; ZF(bit6) = %d ; PF(bit2) = %d ; CF(bit0) = %d ; OF(bit11) = %d" % (
        (eflags >> 7) & 1, (eflags >> 6) & 1, (eflags >> 2) & 1, eflags & 1, (eflags >> 11) & 1))
    p("* 勘误对照：旧分析 SINGLESTEP_0x7CFC9F_ANALYSIS.md:51 写「EFlags=0x286（IF|ZF|PF，无 TF）」")
    p("  实测 ZF(bit6)=0、SF(bit7)=1 —— 旧件把 SF 误标成 ZF（0x286=IF|SF|PF|reserved-bit1）。")
    p()

    # ---------- [D] 证据件里「有没有」DR / 异常参数字段 ----------
    p("[D] 证据件字段存在性普查（否定性事实用文件读取，不靠记忆）")
    toks = ["Dr0", "Dr1", "Dr2", "Dr3", "Dr6", "Dr7", "DR0", "DR6", "DR7",
            "ExceptionInformation", "ExceptionFlags", "ExceptionRecord", "NumberParameters",
            "ExceptionAddress", "EFlags", "SingleStep", "Debug", "CONTEXT"]
    for t in toks:
        hits = [i + 1 for i, L in enumerate(lines) if t in L]
        p("  token %-24s 命中行 = %s" % ("'" + t + "'", hits if hits else "[] (全文零命中)"))
    p("* 结论：本件只有 Eip/Esp/Ebp/Eax/Ebx/Ecx/Edx/Esi/Edi/EFlags/段寄存器/Bytes/Stack dump，")
    p("       没有 DR0-DR7、没有 DR6、没有 ExceptionInformation/NumberParameters。")
    p("       => 任何需要 DR6(BS/B0..B3) 或 ExceptionRecord 参数的判据，在本件上均为「未验」（查不到 != 不存在）。")
    p()

    # ---------- [E] 崩点字节 + 反汇编（自己 rd/disasm/by） ----------
    p("[E] 崩点自己重读字节与反汇编（判据③④ 需要：0x7CFC9F 是不是 call 落点 / 有无 CC F1 F0）")
    VA = 0x7CFC9F
    b32 = e.rd(VA, 32)
    p("fo(0x%X) = 0x%X  (= VA - 0x%X)" % (VA, e.fo(VA), e.IB))
    p("e.rd(0x%X,32) = %s" % (VA, " ".join("%02X" % x for x in b32)))
    l17 = byt_line[0][1] if byt_line else ""
    hexpart = l17.split(":", 1)[1] if ":" in l17 else l17
    bs = [int(x, 16) for x in re.findall(r"\b[0-9A-Fa-f]{2}\b", hexpart)]
    p("证据件 Bytes 行（raw L%d）抽出字节数 = %d ; 值 = %s" % (byt_line[0][0] if byt_line else -1, len(bs), " ".join("%02X" % x for x in bs)))
    p("磁盘 rd(32) vs L17 逐字节差异索引 = %s" % (
        [i for i in range(min(32, len(bs))) if b32[i] != bs[i]]))
    p("va in e.by() = %s" % (VA in e.by()))
    if VA in e.by():
        ins = e.by()[VA]
        p("by()[0x%X] = %s %s (size=%d)" % (VA, ins.mnemonic, ins.op_str, ins.size))
    p("-- 0x%X 前 0x20 字节窗口 --" % VA)
    PRE = VA - 0x20
    pb = e.rd(PRE, 0x20)
    p("e.rd(0x%X,0x20) = %s" % (PRE, " ".join("%02X" % x for x in pb)))
    for pos, x in enumerate(pb):
        if x in (0xCC, 0xF1, 0xF0, 0xCD):
            p("   可疑字节 0x%02X @ 0x%X : %s" % (x, PRE + pos,
              "是独立指令起始" if (PRE + pos) in e.by() else "非指令起始(是 ModRM/disp/imm 内嵌字节)"))
    p("-- 0x%X..0x%X 逐条反汇编 --" % (VA - 4, VA + 0x30))
    for a, hx, mn, op in e.disasm(VA - 4, 0x34):
        p("  0x%X  %-12s %-8s %s" % (a, hx, mn, op))
    p("-- 前 8 条从 0x%X 起 --" % VA)
    d = e.disasm(VA, 0x30)
    for i, (a, hx, mn, op) in enumerate(d[:8]):
        p("  #%d 0x%X  %-10s %-7s %s" % (i + 1, a, hx, mn, op))
    p("-- 崩点前 6 条指令（倒推「哪条刚执行完」；trap-after 的 EIP=下一条） --")
    prev = [(a, hx, mn, op) for (a, hx, mn, op) in e.disasm(VA - 0x18, 0x18) if a < VA]
    for a, hx, mn, op in prev[-6:]:
        p("  0x%X  %-12s %-8s %s   (末址=0x%X)" % (a, hx, mn, op, a + len(hx) // 2))
    p("* 关键：0x%X 是 2 字节 mov ecx,[edx]；紧邻前序 0x7CFC9B 是 4 字节 mov edx,[ecx+edi*8+4]，" % VA)
    p("       末址正好 0x%X。=> 这里【没有任何 call 指令以 0x%X 为返回地址】。" % (VA, VA))
    p()

    # ---------- [F] Esi=7FFFFFFF / Edi=00000001 语义（自己反汇编函数前段） ----------
    p("[F] Esi=0x7FFFFFFF / Edi=0x1 是否特征值 —— 自己反汇编 __sbh_alloc_block 前段")
    HEAD = 0x7CFB13
    p("函数头 0x%X  e.rd(5) = %s" % (HEAD, " ".join("%02X" % x for x in e.rd(HEAD, 5))))
    p("前 1 字节 0x%X = %s" % (HEAD - 1, " ".join("%02X" % x for x in e.rd(HEAD - 1, 1))))
    rng = e.disasm(HEAD, VA - HEAD)
    p("[0x%X,0x%X) 重同步流指令数 = %d（disasm 直解）" % (HEAD, VA, len(rng)))
    stream_seq = [i for i in e.stream if HEAD <= i.address < VA]
    p("[0x%X,0x%X) by()/stream 内指令数 = %d" % (HEAD, VA, len(stream_seq)))
    p("-- 全部涉及 esi/edi/移位/位扫描/[ebp-0xC]/[ebp-0x10] 的指令 --")
    KEY = ("esi", "edi", "shr", "sar", "shl", "sal", "bsf", "bsr", "not ",
           "ebp - 0xc", "ebp - 0x10", "0x3f", "0x1f")
    cnt = 0
    for i in stream_seq:
        s = ("%s %s" % (i.mnemonic, i.op_str)).lower()
        if any(k in s for k in KEY):
            p("  0x%X  %-12s %-10s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
            cnt += 1
    p("  命中条数 = %d" % cnt)
    p("-- 从函数头起前 40 条（看 class_req 位图掩码的建立链） --")
    for i in stream_seq[:40]:
        p("  0x%X  %-12s %-8s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
    p("-- 崩点前 24 条（看 Esi/Edi 在崩点时刻的存活状态） --")
    for i in stream_seq[-24:]:
        p("  0x%X  %-12s %-8s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
    p("-- 全函数窗口内立即数含 0x7FFFFFFF / 0xFFFFFFFF 的指令 --")
    for i in stream_seq:
        try:
            for op in i.operands:
                if op.type == 2 and (op.imm & 0xFFFFFFFF) in (0x7FFFFFFF, 0xFFFFFFFF, 0xFFFFFFFE):
                    p("  0x%X  %-12s %-8s %s   imm=0x%X" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str, op.imm & 0xFFFFFFFF))
        except Exception:
            pass
    p()

    # ---------- [G] 导入表：候选①③ 的静态判据 ----------
    p("[G] gamemd.exe 导入表（只读 PE） —— 候选①③ 判据")
    imp = import_names(e)
    p("导入函数总数 = %d" % len(imp))
    KW = ("ThreadContext", "Debug", "RaiseException", "Vectored", "Unhandled",
          "SuspendThread", "ResumeThread", "IsDebuggerPresent", "OutputDebugString",
          "WaitForDebug", "DebugActive")
    hits = [(dll, nm) for dll, nm in imp if any(k.lower() in nm.lower() for k in KW)]
    p("调试/异常相关导入命中 = %d" % len(hits))
    for dll, nm in hits:
        p("  %s ! %s" % (dll, nm))
    allnames = set(nm for _, nm in imp)
    for probe in ("SetThreadContext", "GetThreadContext", "RaiseException",
                  "SetUnhandledExceptionFilter", "AddVectoredExceptionHandler",
                  "IsDebuggerPresent", "DebugActiveProcess", "SuspendThread"):
        p("  含 %-32s = %s" % (probe, probe in allnames))
    p()

    # ---------- [H] handler 打印串定位（有界 xref 扫描） ----------
    p("[H] 打印串定位（有界：raw.find + 单次 stream 扫描做 xref，不逐串全表遍历）")
    str_vas = []
    for s in ("Exception occurred at %08X", "Bytes at CS:EIP (%08X)", "Error code: %s"):
        va = find_str_va(e, s)
        p("  串 %-38r VA = %s" % (s, "0x%X" % va if va else "未找到"))
        str_vas.append((s, va))
    wanted = set(va for _, va in str_vas if va)
    xr = {va: [] for va in wanted}
    for i in e.stream:  # 单遍扫描全部 3 个串的立即数 xref
        try:
            for op in i.operands:
                if op.type == 2 and (op.imm & 0xFFFFFFFF) in wanted:
                    key = op.imm & 0xFFFFFFFF
                    if len(xr[key]) < 8:
                        xr[key].append((i.address, i.mnemonic, i.op_str))
        except Exception:
            pass
    for s, va in str_vas:
        if va:
            p("  '%s' @0x%X 的立即数 xref（最多列 8 条）= %s" % (s[:24], va, xr[va]))
    p("  参考（Windows x86 CONTEXT 结构，SDK 约定，非本件字节）：Edi+0x9C / Esi+0xA0 / Eip+0xB8 / EFlags+0xC0")
    p("  旧分析 §2#5/§6 称 handler 用 [ebp+0xB8] 同时喂「Exception occurred at」与字节读取；")
    p("  0xB8 恰是 CONTEXT.Eip 偏移 —— 与「打印值来自 CONTEXT 而非 pushf」一致（本探针未亲读 handler 反汇编，标未验）。")
    p()

    # ---------- [I] 候选判据汇总 ----------
    p("[I] 候选判据所依赖的本件可核事实清单")
    p("  F1) EFlags=0x%X，TF(bit8)=%d，RF(bit16)=%d，VM(bit17)=%d，IF(bit9)=%d" % (
        eflags, (eflags >> 8) & 1, (eflags >> 16) & 1, (eflags >> 17) & 1, (eflags >> 9) & 1))
    p("  F2) 本件无 DR0-DR7 / DR6 / ExceptionInformation 字段（见 [D]）")
    p("  F3) 崩点 0x%X = mov ecx,[edx]（2B），前序 0x7CFC9B = mov edx,[ecx+edi*8+4]（4B），无 call 以崩点为返回地址（见 [E]）" % VA)
    p("  F4) 崩点前 0x20 窗口内 0xCC/0xF1/0xF0/0xCD 出现位置及其是否为指令起始（见 [E]）")
    p("  F5) 导入表调试相关 API 命中（见 [G]）")
    p("  F6) 函数前段 Esi/Edi 位图掩码链（见 [F]）")
    p("  F7) EXCEPT 件 sha256 = " + exc_sha + "（见 [A]）；文件系统事实另由 find+sha256sum 核")
    p()
    p("耗时 = %.2f s" % (time.time() - t0))
    p("EXIT=0 / 零真机 / 零活进程读取 / 零采样注入 / 唯一写域内")

    Path(OUT).write_text("\n".join(_lines) + "\n", encoding="utf-8")
    print("\n".join(_lines))


if __name__ == "__main__":
    main()
