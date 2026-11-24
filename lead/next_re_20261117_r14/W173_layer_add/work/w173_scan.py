# -*- coding: utf-8 -*-
"""
W173 主扫描：
  chA  全 .text 扫 `call [reg+0x1C]`；回溯 reg 的 vptr 来源；给出完整上下文与溯源。
  chB  （不依赖 atlas entry+size 的站点发现）扫对 0x8A0360+k*0x18 (k=0..4) 的立即数/位移引用；
       归属用「函数区间包含」atlas 与 synth 双判。
  w94  全镜像 `mov dword [reg+0x94], imm/reg` 写点；按写入值分类；寄存器写入回溯。
所有输出写入 EVIDENCE/，不截断。
"""
from __future__ import annotations
import os
import sys
import bisect
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w173_common as C

E = C.EVID
BASES = {C.LAYER_BASE + k * C.LAYER_ELEM: k for k in range(C.LAYER_N)}
RANGE_LO, RANGE_HI = C.LAYER_BASE, C.LAYER_END   # [0x8A0360, 0x8A03D8)


def seg(v, ivs):
    """区间包含归属 -> 'XXXXXXXX+YYYY' 或 NONE"""
    o = C.owner(v, ivs)
    return ("%08X+%X" % (o[0], v - o[0])) if o else "NONE"


def writes_reg(rec, reg):
    """该指令是否写 reg（保守：op0 为 reg 且非只读 mnemonic）。"""
    mn = rec["mn"]
    if mn in ("cmp", "test", "push", "nop", "", ".byte"):
        return False
    ops = rec["ops"]
    if not ops:
        return False
    op0 = ops[0]
    if op0["kind"] == "reg" and op0["name"] == reg:
        return True
    return False


def find_writes(ins, lo, hi, reg):
    return [j for j in range(lo, hi) if writes_reg(ins[j], reg)]


def src_is_layer_const(op):
    """该操作数是否引用层数组常量。返回 (tag, value) 或 None。"""
    if op["kind"] == "imm":
        v = op["val"] & 0xFFFFFFFF
        if v in BASES:
            return ("imm", v)
        if RANGE_LO <= v <= RANGE_HI:
            return ("imm_range", v)
    if op["kind"] == "mem":
        d = op["disp"] & 0xFFFFFFFF
        if d in BASES:
            if op["base"] is None and op["index"] is None:
                return ("abs", d)
            return ("disp", d)
        if RANGE_LO <= d <= RANGE_HI:
            return ("disp_range", d)
    return None


def trace_reg(ins, lo, hi, reg, depth=0, maxdepth=4, seen=None):
    """回溯 reg 在 [lo,hi) 的写入链，输出文本行。遇 call 标注 caller-saved。"""
    if seen is None:
        seen = set()
    pad = "  " * depth
    if depth > maxdepth:
        return [pad + "... (depth limit)"]
    ws = find_writes(ins, lo, hi, reg)
    if not ws:
        # 是否由更早的 call 产生（返回值）
        return [pad + "%s: 函数区间内无写点（可能参数/进入前已置/返回值）" % reg]
    out = []
    # 取最后 6 个写点（覆盖全部但限制篇幅时会说明）
    for j in ws[-8:]:
        r = ins[j]
        line = pad + "W %08X  %s" % (r["va"], C.fmt(r).split("  ", 1)[-1])
        out.append(line)
        # 源操作数里的层常量
        for op in r["ops"]:
            t = src_is_layer_const(op)
            if t:
                out.append(pad + "    >> 层数组常量 %s=%08X (k=%s)" %
                           (t[0], t[1], (BASES.get(t[1]) if t[1] in BASES else "range")))
        # 源寄存器追一层
        if r["mn"] in ("mov", "lea", "add", "sub", "or", "and", "xor", "movzx", "movsx"):
            for op in r["ops"][1:]:
                if op["kind"] == "reg":
                    sr = op["name"]
                    if sr != reg and (sr, j) not in seen:
                        seen.add((sr, j))
                        out.extend(trace_reg(ins, lo, j, sr, depth + 1, maxdepth, seen))
                elif op["kind"] == "mem" and op["base"] and op["base"] != reg:
                    sr = op["base"]
                    if (sr, j) not in seen:
                        seen.add((sr, j))
                        out.append(pad + "  [mem base=%s]" % sr)
                        out.extend(trace_reg(ins, lo, j, sr, depth + 1, maxdepth, seen))
    # 标注写点与站点之间是否有 call（caller-saved 破坏）
    site_call = [j for j in ws[-1:] if any(ins[k]["mn"] == "call" for k in range(j + 1, hi))]
    if site_call:
        out.append(pad + "!! 最后写点之后存在 call：eax/ecx/edx 可能被 caller-saved 破坏")
    return out


def byte_scan_1c():
    """字节通道：FF 5? 1C (call [reg+disp8=0x1C]) 与 FF 9? 1C000000 (disp32)。
    返回 [(va, reg_index, form, boundary_state, from_entry)]"""
    b = C.B()
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    hits = []
    for i in range(len(data) - 3):
        if data[i] != 0xFF:
            continue
        m = data[i + 1]
        if (m & 0x38) == 0x10 and (m & 0xC0) == 0x40:      # mod=01, reg=010, rm=reg
            if data[i + 2] == 0x1C:
                va = t["va"] + i
                hits.append((va, m & 7, "d8", None, None))
        if (m & 0x38) == 0x10 and (m & 0xC0) == 0x80:      # mod=10, disp32
            if data[i + 2:i + 6] == b"\x1c\x00\x00\x00" and i + 6 <= len(data):
                va = t["va"] + i
                hits.append((va, m & 7, "d32", None, None))
    # 用 atlas / synth 归属入口做边界验证（纪律：字节命中先验指令边界）
    out = []
    for va, ridx, form, _, _ in hits:
        states = []
        for which in ("atlas", "synth"):
            o = C.owner(va, which)
            if not o:
                states.append(which + ":NONE")
                continue
            ok, txt, why = C.boundary(b, o[0], va)
            states.append("%s:%s@%08X(%s)" % (which, ok, o[0], why[:40]))
        out.append((va, ridx, form, " | ".join(states)))
    return out


def main():
    ins = C.text_insns()
    st = C.stats()
    print("text stats:", st)
    L = []

    # ---------------- chA ----------------
    sites = []
    for j, r in enumerate(ins):
        if r["mn"] != "call":
            continue
        ops = r["ops"]
        if not ops:
            continue
        op = ops[0]
        if op["kind"] != "mem":
            continue
        # call [reg+0x1C]：disp==0x1C，base 为寄存器
        if (op["disp"] & 0xFFFFFFFF) != C.ADD_SLOT or op["base"] is None:
            continue
        reg = op["base"]
        va = r["va"]
        oa = C.owner(va, "atlas")
        osy = C.owner(va, "synth")
        lo = bisect.bisect_left(C.vas(), oa[0]) if oa else max(0, j - 80)
        hi = j
        tr = trace_reg(ins, lo, hi, reg)
        # 最近常量引用（前 60 条）
        consts = []
        for k in range(max(0, j - 60), j + 1):
            for op2 in ins[k]["ops"]:
                t = src_is_layer_const(op2)
                if t:
                    consts.append("%08X %s=%08X(%s)" %
                                  (ins[k]["va"], t[0], t[1],
                                   BASES.get(t[1], "range")))
        sites.append(dict(j=j, va=va, reg=reg, op=op, oa=oa, osy=osy,
                          tr=tr, consts=consts))
    L.append("=" * 100)
    L.append("W173 通道A — 全 .text `call dword [reg+0x1C]` 站点")
    L.append("反汇编统计: %r" % st)
    L.append("站点总数: %d" % len(sites))
    L.append("站点清单: VA | reg | base+index | atlas归属 | synth归属 | 前60条层常量引用数")
    for s in sites:
        L.append("%08X | %-4s | %s%s | %s | %s | %d" % (
            s["va"], s["reg"], s["op"]["base"],
            ("*" + s["op"]["index"]) if s["op"]["index"] else "",
            seg(s["va"], "atlas"), seg(s["va"], "synth"), len(s["consts"])))
    L.append("")
    for s in sites:
        L.append("-" * 100)
        L.append("SITE %08X  %s" % (s["va"], C.fmt(ins[s["j"]])))
        L.append("  reg=%s  mem=%r" % (s["reg"], s["op"]))
        L.append("  atlas=%r" % (s["oa"],))
        L.append("  synth=%r" % (s["osy"],))
        if s["consts"]:
            L.append("  前60条中层数组常量引用 (%d):" % len(s["consts"]))
            L.extend("    " + x for x in s["consts"])
        L.append("  回溯 %s 写入链:" % s["reg"])
        L.extend("    " + x for x in s["tr"])
        L.append("  上下文 (前60 / 后8，逐条打完):")
        L.extend("    " + x for x in C.context(s["va"], 60, 8))
    C.write_text(os.path.join(E, "w173_chA_detail.txt"), L)

    # 字节通道交叉
    bh = byte_scan_1c()
    L2 = ["=" * 100, "W173 通道A 字节交叉 — 原始字节 FF 5? 1C / FF 9? 1C000000",
          "命中总数: %d" % len(bh),
          "VA | rm(reg) | form | boundary(atlas/synth)"]
    for va, ridx, form, bs in bh:
        L2.append("%08X | %d | %s | %s" % (va, ridx, form, bs))
    C.write_text(os.path.join(E, "w173_chA_bytescan.txt"), L2)

    # ---------------- chB ----------------
    L3 = ["=" * 100, "W173 通道B — 对 0x8A0360+k*0x18 (k=0..4) 的立即数/位移引用",
          "站点发现不依赖 function_atlas.tsv；归属用区间包含，atlas/synth 双判",
          "反汇编统计: %r" % st]
    chb = []
    for j, r in enumerate(ins):
        hits = []
        for op in r["ops"]:
            t = src_is_layer_const(op)
            if t and (t[1] in BASES or t[0] in ("imm_range", "disp_range")):
                hits.append(t)
        if not hits:
            continue
        va = r["va"]
        chb.append(dict(j=j, va=va, hits=hits))
    L3.append("引用站点总数(含范围附加): %d" % len(chb))
    L3.append("VA | 指令 | 命中(类型=值/k) | atlas归属 | synth归属 | 边界(atlas入口)")
    bnd = {}
    for c in chb:
        va = c["va"]
        oa = C.owner(va, "atlas")
        bd = "NONE"
        if oa:
            ok, txt, why = C.boundary(C.B(), entry=oa[0], target=va)
            bd = "%s(%s)" % (ok, why[:30])
        bnd[va] = bd
        hs = ",".join("%s=%08X/k%s" % (t[0], t[1], BASES.get(t[1], "r")) for t in c["hits"])
        L3.append("%08X | %s | %s | %s | %s | %s" % (
            va, C.fmt(ins[c["j"]]), hs, seg(va, "atlas"), seg(va, "synth"), bd))
    L3.append("")
    for c in chb:
        L3.append("-" * 100)
        L3.append("REF %08X  %s" % (c["va"], C.fmt(ins[c["j"]])))
        L3.append("  hits=%r" % c["hits"])
        L3.append("  atlas=%s  synth=%s  boundary=%s" %
                  (seg(c["va"], "atlas"), seg(c["va"], "synth"), bnd[c["va"]]))
        L3.extend("    " + x for x in C.context(c["va"], 12, 6))
    C.write_text(os.path.join(E, "w173_chB_detail.txt"), L3)

    # ---------------- w94 ----------------
    L4 = ["=" * 100, "W173 任务3 — 全 .text `mov dword ptr [reg+0x94], src` 写点",
          "反汇编统计: %r" % st]
    w94 = []
    for j, r in enumerate(ins):
        if r["mn"] != "mov":
            continue
        ops = r["ops"]
        if len(ops) < 2:
            continue
        d, s = ops[0], ops[1]
        if d["kind"] != "mem" or d["base"] is None:
            continue
        if d["disp"] != C.W94_OFF:
            continue
        width = d["size"]
        va = r["va"]
        oa = C.owner(va, "atlas")
        osy = C.owner(va, "synth")
        lo = bisect.bisect_left(C.vas(), oa[0]) if oa else max(0, j - 100)
        if s["kind"] == "imm":
            v = s["val"] & 0xFFFFFFFF
            if v == 0xFFFFFFFF:
                cls = "-1"
            elif 0 <= v <= 4:
                cls = "0..4"
            else:
                cls = "other_imm"
        elif s["kind"] == "reg":
            cls = "reg"
        elif s["kind"] == "mem":
            cls = "mem"
        else:
            cls = "other"
        tr = []
        if s["kind"] == "reg":
            tr = trace_reg(ins, lo, j, s["name"])
        w94.append(dict(j=j, va=va, dst=d, src=s, width=width, cls=cls,
                        oa=oa, osy=osy, tr=tr))
    from collections import Counter
    cnt = Counter(x["cls"] for x in w94)
    L4.append("写点总数: %d" % len(w94))
    L4.append("分类计数: %r" % dict(cnt))
    L4.append("VA | 指令 | 宽度 | 分类 | atlas归属 | synth归属")
    for x in w94:
        L4.append("%08X | %s | %s | %s | %s | %s" % (
            x["va"], C.fmt(ins[x["j"]]), x["width"], x["cls"],
            seg(x["va"], "atlas"), seg(x["va"], "synth")))
    L4.append("")
    for x in w94:
        L4.append("-" * 100)
        L4.append("W94 %08X  %s" % (x["va"], C.fmt(ins[x["j"]])))
        L4.append("  dst=%r src=%r width=%s cls=%s" % (x["dst"], x["src"], x["width"], x["cls"]))
        L4.append("  atlas=%r synth=%r" % (x["oa"], x["osy"]))
        if x["tr"]:
            L4.append("  源寄存器写入回溯:")
            L4.extend("    " + t for t in x["tr"])
        L4.extend("    " + t for t in C.context(x["va"], 18, 6))
    C.write_text(os.path.join(E, "w173_w94_detail.txt"), L4)

    # ---------------- 交集（函数级/站点级）----------------
    asites = {s["va"] for s in sites}
    bsites = {c["va"] for c in chb}
    afuncs = set()
    bfuncs = set()
    for s in sites:
        if s["oa"]:
            afuncs.add(s["oa"][0])
    for c in chb:
        o = C.owner(c["va"], "atlas")
        if o:
            bfuncs.add(o[0])
    L5 = ["=" * 100, "W173 两通道交集统计（函数级，atlas 归属）",
          "chA 站点数: %d" % len(sites),
          "chB 站点数(含范围附加): %d" % len(chb),
          "chB 站点数(仅 k=0..4 精确基址): %d" % sum(
              1 for c in chb if any(t[1] in BASES for t in c["hits"])),
          "chA 函数集: %d" % len(afuncs),
          "chB 函数集: %d" % len(bfuncs),
          "函数级交集: %d -> %s" % (len(afuncs & bfuncs),
                                 sorted("%08X" % x for x in (afuncs & bfuncs))),
          "站点级交集(同一VA): %d -> %s" % (len(asites & bsites),
                                     sorted("%08X" % x for x in (asites & bsites))),
          "w94 写点总数: %d  分类: %r" % (len(w94), dict(cnt)),
          ]
    C.write_text(os.path.join(E, "w173_summary.txt"), L5)
    print("\n".join(L5))


if __name__ == "__main__":
    main()
