# -*- coding: utf-8 -*-
"""W8-F8 探针 · 可见对象数 / 裁剪通过数（纯静态、只读、零真机）。

职责（TASK.md §2 F8）：
  1) 独立复核 D20_B_VISIBILITY_GAP.md 三条数字：
     a. call 0x5F4B10(DrawIfVisible) 全镜像直接调用 = 3 处；
     b. 渲染簇 0x6D8DB0..0x6DA1FB 内 call 0x5F4B10 = 0、全局 dword 写 = 0；
     c. call 0x6D2140(IsVisible) = 139 处、其后均无计数写。
  2) F8-Q2：0x5F4B10 全部直接调用者 + 各自所在函数，查有无循环内计数累加。
  3) F8-Q3 依据：vtable[65](+0x104) 虚调用点普查；IsVisible / 层容器 / 视口字段反汇编；
     GetCoords 槽解析；宽域 Tactical 渲染区 [0x6D3D10,0x6DA200) 计数器狩猎。

只读 gamemd.exe；唯一写 = 本目录 _w8_f8_out.txt。
运行：python -I -X utf8 _w8_f8.py
"""
import sys, os, struct, time, traceback
from collections import Counter

sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine, EXE
from capstone.x86 import X86_REG_ESP

OUT_PATH = r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\W8_STATIC_LOCATE\_w8_f8_out.txt"
OUT = []


def P(*a):
    OUT.append(" ".join(str(x) for x in a))


def main():
    eng = Engine()
    raw = eng.raw

    DRAWHIV = 0x5F4B10          # ObjectClass::DrawIfVisible (vtable[65] 基实现)
    ISVIS = 0x6D2140            # TacticalClass::IsVisible
    R_LO, R_HI = 0x6D8DB0, 0x6DA1FC   # D20 渲染簇区间 [0x6D8DB0..0x6DA1FB] 闭开

    def call_imm(ins):
        try:
            if ins.operands and ins.operands[0].type == 2:
                return ins.operands[0].imm
        except Exception:
            pass
        return None

    def va_of_off(off):
        for nm, sva, vsz, rp, rsz in eng.SEC:
            if rp <= off < rp + rsz:
                return sva + (off - rp)
        return None

    # ---------------- S0 自证 ----------------
    P("=== S0 SELF PROOF ===")
    P("RUN_TIMESTAMP", time.strftime("%Y-%m-%d %H:%M:%S"))
    P("EXE", EXE)
    P("SHA256", eng.sha)
    P("FILE_BYTES", os.path.getsize(EXE), "len(raw)=", len(raw))
    cov, nins, fails = eng.coverage
    P("COVERAGE pct=%.14f insns=%d resync=%d .text_size=%d" % (cov, nins, fails, eng.TSZ))
    P("IMAGEBASE", hex(eng.IB))
    for nm, sva, vsz, rp, rsz in eng.SEC:
        P("  SEC", nm, hex(sva), hex(vsz), hex(rp), hex(rsz))

    stream = eng.stream
    by = eng.by()
    idxmap = {i.address: k for k, i in enumerate(stream)}

    def seq_from(a, n):
        out, cur = [], a
        for _ in range(n):
            i = by.get(cur)
            if i is None:
                break
            out.append(i)
            cur += i.size
        return out

    def func_head2(addr, back=0x600):
        """回走找函数头：候选 = ret/int3 之后那条；取「向前解码到 addr 且途中无 int3」的最小者。"""
        k = idxmap[addr]
        lo = addr - back
        cands = []
        j = k - 1
        while j >= 0 and stream[j].address >= lo:
            i = stream[j]
            if i.mnemonic == "int3" or i.mnemonic.startswith("ret"):
                if j + 1 < len(stream):
                    cands.append(stream[j + 1].address)
            j -= 1
        for p in sorted(cands):
            if p not in idxmap:
                continue
            cur, ok, steps = p, True, 0
            while cur < addr and steps < 4000:
                i = by.get(cur)
                if i is None or i.mnemonic == "int3":
                    ok = False
                    break
                cur += i.size
                steps += 1
            if ok and cur == addr:
                return p
        return None

    def func_end(addr):
        k = idxmap[addr]
        j = k
        while j < len(stream) and stream[j].address < addr + 0x2000:
            if stream[j].mnemonic == "int3":
                return stream[j].address
            j += 1
        return addr + 0x2000

    def mem_kind(op):
        m = op.mem
        if m.base == 0 and m.index == 0:
            return "ABS"
        if m.base == X86_REG_ESP:
            return "STACK"
        return "REG+DISP"

    def mem_counter_ops(ins_iter):
        out = []
        for i in ins_iter:
            if i.mnemonic in ("inc", "dec", "add", "sub"):
                try:
                    ops = i.operands
                except Exception:
                    continue
                if ops and ops[0].type == 3:
                    out.append((hex(i.address), i.mnemonic, i.op_str, mem_kind(ops[0])))
        return out

    # ---------------- S1 复核 D20-1 ----------------
    P("")
    P("=== S1 RECHECK D20-1: direct calls to 0x5F4B10 in whole .text ===")
    dc = [i.address for i in stream if i.mnemonic == "call" and call_imm(i) == DRAWHIV]
    P("S1 DIRECT_CALL_COUNT", len(dc), [hex(a) for a in dc])
    for a in dc:
        P("   site=%s bytes=%s" % (hex(a), eng.rd(a, 5).hex()))
    jc = [i.address for i in stream if i.mnemonic == "jmp" and call_imm(i) == DRAWHIV]
    P("S1 DIRECT_JMP_COUNT(tail-call)", len(jc), [hex(a) for a in jc])
    tb = raw[eng.TB: eng.TB + eng.TSZ]
    e8hits, e9hits = [], []
    for off in range(len(tb) - 5):
        b = tb[off]
        if b == 0xE8 or b == 0xE9:
            rel = struct.unpack_from("<i", tb, off + 1)[0]
            va = eng.TLO + off
            if va + 5 + rel == DRAWHIV:
                (e8hits if b == 0xE8 else e9hits).append(hex(va))
    P("S1 RAW_E8_UPPERBOUND", len(e8hits), e8hits)
    P("S1 RAW_E9_UPPERBOUND", len(e9hits), e9hits)

    # ---------------- S2 复核 D20-2 ----------------
    P("")
    P("=== S2 RECHECK D20-2: render cluster [%s,%s) ===" % (hex(R_LO), hex(R_HI)))
    rin = [i for i in stream if R_LO <= i.address < R_HI]
    P("S2 INSNS_IN_RANGE", len(rin))
    P("S2 CALL_DRAWHIV_IN_RANGE",
      sum(1 for i in rin if i.mnemonic == "call" and call_imm(i) == DRAWHIV))
    gw = []
    for i in rin:
        try:
            ops = i.operands
        except Exception:
            continue
        for op in ops:
            if op.type == 3 and op.mem.base == 0 and op.mem.index == 0 and (op.access & 2):
                gw.append((hex(i.address), i.mnemonic, i.op_str, op.size))
    P("S2 GLOBAL_DWORD_WRITES", len(gw))
    for t in gw:
        P("   ", t)
    indec = [(hex(i.address), i.mnemonic, i.op_str) for i in rin if i.mnemonic in ("inc", "dec")]
    P("S2 INC_DEC_TOTAL", len(indec))
    for t in indec:
        P("   ", t)
    mc = mem_counter_ops(rin)
    P("S2 MEM_INC_DEC_ADD_SUB(any-mem)", len(mc))
    for t in mc:
        P("   ", t)

    # ---------------- S3 复核 D20-3 ----------------
    P("")
    P("=== S3 RECHECK D20-3: calls to 0x6D2140 (IsVisible) ===")
    dv = [i.address for i in stream if i.mnemonic == "call" and call_imm(i) == ISVIS]
    P("S3 CALL_ISVIS_COUNT", len(dv))
    P("S3 FIRST_LAST", hex(dv[0]) if dv else None, hex(dv[-1]) if dv else None)
    jv = [i.address for i in stream if i.mnemonic == "jmp" and call_imm(i) == ISVIS]
    P("S3 JMP_ISVIS_COUNT", len(jv), [hex(a) for a in jv])
    rawv = []
    for off in range(len(tb) - 5):
        if tb[off] == 0xE8:
            rel = struct.unpack_from("<i", tb, off + 1)[0]
            va = eng.TLO + off
            if va + 5 + rel == ISVIS:
                rawv.append(hex(va))
    P("S3 RAW_E8_UPPERBOUND", len(rawv))
    nm1 = Counter()
    flagged = []
    for a in dv:
        seq = seq_from(a, 9)
        if len(seq) < 2:
            continue
        nm1[seq[1].mnemonic] += 1
        for k, i in enumerate(seq[1:], 1):
            if i.mnemonic in ("inc", "dec", "add", "sub"):
                try:
                    ops = i.operands
                except Exception:
                    continue
                if ops and ops[0].type == 3:
                    flagged.append((hex(a), k, hex(i.address), i.mnemonic, i.op_str, mem_kind(ops[0])))
    P("S3 NEXT_INSN_DIST", dict(nm1))
    P("S3 MEM_COUNTER_OPS_WITHIN_8_INSN_AFTER_CALL", len(flagged))
    for t in flagged:
        P("   ", t)
    P("S3 SITES", " ".join(hex(a) for a in dv))

    # ---------------- S4 F8-Q2 直接调用者所在函数 ----------------
    # 函数头由 S6 转储铁证人工确认（前邻 >=4 字节 90/cc 填充 + 序言形态）：
    #   0x422c8e -> 0x422c70（0x422c65..6f nop 填充；0x422c70 mov eax,[ecx+0x184] 序言）
    #   0x73b132 -> 0x73b0b0（0x73b0b0 push esi/push edi/mov edi,ecx 序言，线性解码直达站点）
    #   0x749b5b -> 0x749b20（0x749b14..1f nop 填充；0x749b20 sub esp,0xc 序言；0x749b64 ret 0xc）
    S4_HEADS = {0x422C8E: 0x422C70, 0x73B132: 0x73B0B0, 0x749B5B: 0x749B20}
    P("")
    P("=== S4 F8-Q2: containing function of each direct caller of 0x5F4B10 ===")
    for a in dc:
        head = S4_HEADS.get(a)
        end = None
        seq = seq_from(a + 5, 12)
        for i in seq:
            if i.mnemonic.startswith("ret"):
                end = i.address + i.size
                break
        P("CALLER site=%s head=%s fn_end=%s span=%s" %
          (hex(a), hex(head) if head else None, hex(end) if end else None,
           hex(end - head) if (head and end) else None))
        if not head:
            continue
        # vtable 归属：全文件找 slot65 dword == head 的 .rdata 位置
        vts = []
        pat = struct.pack("<I", head)
        off = 0
        while True:
            off = raw.find(pat, off)
            if off < 0:
                break
            va = va_of_off(off)
            if va is not None and 0x7E1000 <= va < 0x812000:
                vts.append(va)
            off += 1
        P("   VTABLE_SLOTS65_AT", [hex(v) for v in vts],
          "vtbases=", [hex(v - 0x104) for v in vts])
        seg = [i for i in stream if head <= i.address < (end or a + 0x40)]
        be = eng.loop_backedges(head, end or a + 0x40)
        P("   INSNS_IN_FN", len(seg))
        P("   LOOP_BACKEDGES_IN_FN", len(be), [(hex(x), hex(y), m) for x, y, m in be][:12])
        mc2 = mem_counter_ops(seg)
        P("   MEM_INC_DEC_ADD_SUB_IN_FN", len(mc2))
        for t in mc2:
            P("     ", t)
        gw2 = []
        for i in seg:
            try:
                ops = i.operands
            except Exception:
                continue
            for op in ops:
                if op.type == 3 and op.mem.base == 0 and op.mem.index == 0 and (op.access & 2):
                    gw2.append((hex(i.address), i.mnemonic, i.op_str))
        P("   GLOBAL_WRITES_IN_FN", len(gw2))
        for t in gw2:
            P("     ", t)

    # ---------------- S5 vtable[65] (+0x104) 虚调用点 ----------------
    P("")
    P("=== S5 F8: virtual dispatch call/jmp [reg+0x104] (vtable slot 65) ===")
    vs = []
    for i in stream:
        if i.mnemonic not in ("call", "jmp"):
            continue
        try:
            ops = i.operands
        except Exception:
            continue
        if ops and ops[0].type == 3:
            m = ops[0].mem
            if m.base != 0 and m.index == 0 and m.disp == 0x104:
                vs.append((i.address, i.mnemonic, i.op_str))
    P("S5 COUNT", len(vs))
    for a, mn, o in vs:
        head = func_head2(a)
        P("   site=%s %s %s head=%s(earliest-wins,参考值)" %
          (hex(a), mn, o, hex(head) if head else "?"))
    for a, mn, o in vs:
        P("   window around site %s:" % hex(a))
        for x, b, m, oo in eng.disasm(a - 0x24, 0x30):
            P("     %s %s %s %s" % (hex(x), b, m, oo))
        nb = [i for i in stream if a - 0x100 <= i.address < a + 0x100]
        nbm = mem_counter_ops(nb)
        P("   near-scan +-0x100 MEM_INC_DEC_ADD_SUB", len(nbm))
        for t in nbm:
            P("     ", t)
    fl = []
    for a, mn, o in vs:
        seq = seq_from(a, 9)
        for k, i in enumerate(seq[1:], 1):
            if i.mnemonic in ("inc", "dec", "add", "sub"):
                try:
                    ops = i.operands
                except Exception:
                    continue
                if ops and ops[0].type == 3:
                    fl.append((hex(a), k, hex(i.address), i.mnemonic, i.op_str, mem_kind(ops[0])))
    P("S5 MEM_COUNTER_OPS_WITHIN_8_INSN_AFTER", len(fl))
    for t in fl:
        P("   ", t)

    # ---------------- S6 关键反汇编转储 ----------------
    P("")
    P("=== S6 KEY DISASM DUMPS ===")

    def dump(va, n, title):
        P("--- %s ---" % title)
        for x, b, m, o in eng.disasm(va, n):
            P("  %s %s %s %s" % (hex(x), b, m, o))

    dump(DRAWHIV, 0x88, "ObjectClass::DrawIfVisible head 0x5F4B10 +0x88")
    dump(0x5F4CE0, 0x30, "DrawIfVisible tail 0x5F4CE0 +0x30")
    dump(ISVIS, 0x138, "TacticalClass::IsVisible 0x6D2140 +0x138")
    dump(0x6D8F0F, 0x51, "render loop layer walk 0x6D8F0F +0x51")
    dump(0x6D9080, 0x40, "render loop DrawIfVisible call site 0x6D9080 +0x40")
    dump(0x6D93F0, 0x48, "render loop tail 0x6D93F0 +0x48")
    dump(0x73B0B0, 0x40, "claimed UnitClass::DrawIfVisible head 0x73B0B0 +0x40")
    dump(0x422C70, 0x28, "AnimClass::DrawIfVisible head 0x422C70 +0x28")
    dump(0x749B55, 0x28, "tail of fn containing 0x749B5B (head 0x749B20)")
    dump(0x6D8DA0, 0x30, "boundary check before render cluster head 0x6D8DB0")
    for a in dc:
        dump(a - 0x70, 0x78, "window before direct-call site %s" % hex(a))

    # ---------------- S7 宽域计数器狩猎 ----------------
    P("")
    P("=== S7 WIDE SCAN [0x6D3D10,0x6DA200): Tactical render region ===")
    wide = [i for i in stream if 0x6D3D10 <= i.address < 0x6DA200]
    wl = mem_counter_ops(wide)
    P("S7 INSNS", len(wide), "MEM_INC_DEC_ADD_SUB", len(wl))
    for t in wl:
        P("   ", t)

    # ---------------- S8 代理/容器全局证据 ----------------
    P("")
    P("=== S8 DISP_HITS for proxy & container globals ===")
    for va in (0xB0CE30, 0xB0CE34, 0xB0CE88, 0x887324):
        h = eng.disp_hits(va)
        P("DISP_HITS %s count=%d" % (hex(va), len(h)))
        for t in h[:14]:
            P("   %s %s %s %s" % (hex(t[0]), t[1], t[2], t[3]))

    # ---------------- S9 GetCoords 槽解析（推导规格用） ----------------
    P("")
    P("=== S9 GETCOORDS (slot43=+0xAC) via vtable refs of DrawIfVisible impls ===")
    for nd in (0x005F4B10, 0x0073B0B0, 0x00422C70):
        pat = struct.pack("<I", nd)
        off = 0
        hits = []
        while True:
            off = raw.find(pat, off)
            if off < 0:
                break
            hits.append((off, va_of_off(off)))
            off += 1
        P("REFS of %s : %d" % (hex(nd), len(hits)))
        for off, va in hits:
            sec = None
            if va is not None:
                for nm, sva, vsz, rp, rsz in eng.SEC:
                    if sva <= va < sva + vsz:
                        sec = nm
                        break
            P("   file_off=%s va=%s sec=%s" % (hex(off), hex(va) if va is not None else None, sec))
            if sec in (".rdata", ".data"):
                vt = va - 0x104
                gc = eng.u32(vt + 0xAC)
                P("      vtbase=%s GetCoords=%s" % (hex(vt), hex(gc)))
                if eng.fo(gc) is not None:
                    for x, b, m, o in eng.disasm(gc, 0x20):
                        P("        %s %s %s %s" % (hex(x), b, m, o))

    P("")
    P("=== S10 COORDS CHAIN (slot18=+0x48) of Unit/Anim vtables ===")
    for tag, vt in (("UnitClass? vt@0x7f5c70", 0x7F5C70), ("AnimClass? vt@0x7e3354", 0x7E3354)):
        co = eng.u32(vt + 0x48)
        P("S10 %s Coords=0x%x" % (tag, co))
        if eng.fo(co) is not None:
            for x, b, m, o in eng.disasm(co, 0x24):
                P("   %s %s %s %s" % (hex(x), b, m, o))

    P("")
    P("=== DONE exit=0 ===")


try:
    main()
    ok = True
except Exception:
    ok = False
    P("!!! PROBE EXCEPTION !!!")
    P(traceback.format_exc())

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(OUT) + "\n")
print("WROTE %s lines=%d ok=%s" % (OUT_PATH, len(OUT), ok))
sys.exit(0 if ok else 1)
