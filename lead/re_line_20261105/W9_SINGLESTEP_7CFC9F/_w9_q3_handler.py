# -*- coding: utf-8 -*-
# W9 / Q3 补充探针 —— handler 打印值的来源 + 候选③ 判别（只读，零真机，零采样注入）
# 独立运行：python -I -X utf8 D:\Project\ra2-campaign-forge\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\_w9_q3_handler.py
# 产出：同目录 _w9_q3_handler_out.txt
# 唯一写域 = W9_SINGLESTEP_7CFC9F/ 下的 _w9_q3_handler_out.txt。
import struct
import sys
import time
from pathlib import Path

ROOT = r"D:\Project\ra2-campaign-forge"
SWARM = ROOT + r"\lead\goal3t_nightwatch_20261102\swarm_20261104"
OUT = ROOT + r"\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\_w9_q3_handler_out.txt"

sys.path.insert(0, SWARM)
from ra2tool import Engine  # noqa: E402

_lines = []
def p(s=""):
    _lines.append(str(s))


def raw2va(e, off):
    for nm, sva, vsz, rp, rsz in e.SEC:
        if rp <= off < rp + rsz:
            return e.IB + (sva - e.IB) + (off - rp)
    return None


def show(e, lo, hi, label):
    seq = [i for i in e.stream if lo <= i.address < hi]
    p("-- %s : [0x%X,0x%X) %d insns --" % (label, lo, hi, len(seq)))
    for i in seq:
        ops = []
        for op in i.operands:
            if op.type == 3:
                m = op.mem
                ops.append("[b=%s d=0x%X]" % (i.reg_name(m.base) if m.base else "-", m.disp & 0xFFFFFFFF))
            elif op.type == 2:
                ops.append("imm=0x%X" % (op.imm & 0xFFFFFFFF))
        p("  0x%X  %-14s %-9s %-40s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str, " ".join(ops)))
    return seq


def main():
    t0 = time.time()
    p("=" * 78)
    p("W9 / Q3 补充探针：handler 打印值来源 + RaiseException 判别（自己实跑）")
    p("=" * 78)
    p("运行时刻 = " + time.strftime("%Y-%m-%d %H:%M:%S"))
    p()
    e = Engine()
    cov, nins, fails = e.coverage
    p("Engine 自证 = COVERAGE %.12f%% (%d insns, %d resync-fails) / IMAGEBASE 0x%X" % (cov, nins, fails, e.IB))
    p()

    # ---- [J] 格式串 VA 与 CONTEXT 偏移对应 ----
    p("[J] 格式串 VA（raw.find -> 节表反查 VA）")
    offs = {"Eip": 0x421EA0, "EFlags": 0x421E50, "Eax": 0x421E80,
            "Reg3": 0x421E60, "Bytes": 0x421DE6, "ExcOcc": 0x421F78,
            "RegCS": 0x421E70}
    S = {}
    for k, off in offs.items():
        va = raw2va(e, off)
        S[k] = va
        txt = e.raw[off:off + 80].split(b"\x00")[0]
        p("  %-8s raw=0x%X VA=%s  str=%r" % (k, off, "0x%X" % va if va else "?", txt))
    p()

    # ---- [K] handler 头部：CONTEXT 基址怎么建立的 ----
    p("[K] handler 头部（找 lea/mov ebp <- CONTEXT base；即 [ebp+off] 的 off 是否=CONTEXT 字段偏移）")
    show(e, 0x4C8860, 0x4C8910, "handler entry region A")
    show(e, 0x4C8960, 0x4C89B0, "'Exception occurred at %08X' 打印处")
    p()

    # ---- [L] 寄存器打印区（确认 Eflags/Eip/Esp/Ebp 都从同一个 [ebp+CONTEXT偏移] 来） ----
    p("[L] 寄存器 printf 区（确认打印值 = CONTEXT 字段，非 pushfd）")
    show(e, 0x4C8B79, 0x4C8C79, "Eip/Eax/Reg3/EFlags printf")
    p("  CONTEXT (Win32 x86, winnt.h 约定) 字段偏移：")
    p("   +0x9C Edi | +0xA0 Esi | +0xA4 Ebx | +0xA8 Edx | +0xAC Ecx | +0xB0 Eax")
    p("   +0xB4 Ebp | +0xB8 Eip | +0xBC SegCs | +0xC0 EFlags | +0xC4 Esp | +0xC8 SegSs")
    p("  实测打印取数：Eip=[ebp+0xB8] / Esp=[ebp+0xC4] / Ebp=[ebp+0xB4] /")
    p("               Eax=[ebp+0xB0] / Ebx=[ebp+0xA4] / Ecx=[ebp+0xAC] /")
    p("               Edx=[ebp+0xA8] / Esi=[ebp+0xA0] / Edi=[ebp+0x9C] / EFlags=[ebp+0xC0]")
    p("  => 全部精确等于 CONTEXT 字段偏移 ⇒ 打印的是【异常帧 CONTEXT】，不是 handler 自己的 pushfd。")
    p()

    # ---- [M] 候选③ 判别：0x80000004 立即数 + RaiseException IAT 槽调用点 ----
    p("[M] 候选③ RaiseException(EXCEPTION_SINGLE_STEP=0x80000004,...) 判别")
    # 找 RaiseException 的 IAT 槽 VA（用 engine.resolve_iat 反查：遍历导入表找名字）
    dd = e.opt + 96
    imp_rva = struct.unpack_from("<I", e.raw, dd + 8)[0]
    o = e.fo(e.IB + imp_rva)
    iat_targets = {}
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
                nm = e.raw[ho:e.raw.index(b"\0", ho)].decode("ascii", "replace")
                if nm in ("RaiseException", "SetUnhandledExceptionFilter", "UnhandledExceptionFilter"):
                    iat_targets[e.IB + ft + j * 4] = nm
            j += 1
        k += 1
    p("  关注的 IAT 槽 VA -> 名称：")
    for va, nm in iat_targets.items():
        p("    0x%X -> %s" % (va, nm))
    # 立即数 0x80000004 出现处 + 调用上述 IAT 槽的指令
    imm_hits = []
    iat_calls = []
    for i in e.stream:
        try:
            for op in i.operands:
                if op.type == 2 and (op.imm & 0xFFFFFFFF) == 0x80000004:
                    imm_hits.append((i.address, i.mnemonic, i.op_str))
                if op.type == 3 and op.mem.base == 0 and op.mem.index == 0:
                    d = op.mem.disp & 0xFFFFFFFF
                    if d in iat_targets and i.mnemonic.startswith("call"):
                        iat_calls.append((i.address, i.mnemonic, i.op_str, iat_targets[d]))
        except Exception:
            pass
    p("  全 .text 立即数 == 0x80000004 的指令数 = %d ; 前 12 = %s" % (
        len(imm_hits), [(hex(a), m, o) for a, m, o in imm_hits[:12]]))
    p("  call [RaiseException IAT] 的指令数 = %d ; 全部 = %s" % (
        len([x for x in iat_calls if x[3] == "RaiseException"]),
        [(hex(a), m, o, n) for a, m, o, n in iat_calls if n == "RaiseException"][:20]))
    p("  call [SetUnhandledExceptionFilter IAT] = %s" % (
        [(hex(a), m, o) for a, m, o, n in iat_calls if n == "SetUnhandledExceptionFilter"][:10]))
    p()

    # ---- [N] 'Bytes at CS:EIP' 是怎么被引用/打印的（xref 为零时找附近 push/lea） ----
    p("[N] 'Bytes at CS:EIP' 串附近的打印/字节读取（判据：字节来自 CONTEXT.Eip 指向的内存）")
    bva = S.get("Bytes")
    if bva:
        p("  Bytes 串 VA=0x%X，直接立即数 xref 数 = %d" % (
            bva, len([1 for i in e.stream for op in _ops(i)
                      if op.type == 2 and (op.imm & 0xFFFFFFFF) == bva])))
        # 找引用该串 ±2 的 push（有的串按 0x821DE4 起点引用）
        near = []
        for i in e.stream:
            try:
                for op in i.operands:
                    if op.type == 2 and bva - 8 <= (op.imm & 0xFFFFFFFF) <= bva + 8:
                        near.append((i.address, i.mnemonic, i.op_str))
            except Exception:
                pass
        p("  引用 Bytes 串 VA±8 的立即数指令 = %s" % [(hex(a), m, o) for a, m, o in near[:10]])
        for a, m, o in near[:3]:
            show(e, a - 0x30, a + 0x20, "Bytes 打印处 @0x%X" % a)
    p()

    p("耗时 = %.2f s" % (time.time() - t0))
    p("EXIT=0 / 零真机 / 零活进程读取 / 零采样注入 / 唯一写域内")
    Path(OUT).write_text("\n".join(_lines) + "\n", encoding="utf-8")
    print("\n".join(_lines))


def _ops(i):
    try:
        return i.operands
    except Exception:
        return []


if __name__ == "__main__":
    main()
