# -*- coding: utf-8 -*-
"""
W173 公共库（只读 gamemd.exe）
 - 全 .text 线性反汇编，capstone 5.0.7 必须 skipdata=True
 - 轻量指令记录（可序列化），供通道 A/B 与 [+0x94] 写点分析复用
 - 函数区间两套：
     atlas  : function_atlas.tsv 的 (entry, size) —— size 为十进制
     synth  : 入口 = 全 .text 中 call/jmp 的直接目标，区间到下一入口/text_end
              ★ 完全不依赖 atlas（纪律 1 的第二通道）
 - 站点归属一律用「函数区间包含」（entry <= site < end），不用 entry_at_or_before
 - boundary_check 的 max_bytes 超限返回 'unknown'（纪律 2）
"""
from __future__ import annotations
import os
import sys
import bisect
import capstone

sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import audit_lib

EXE   = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ROOT  = r"D:\Project\ra2-campaign-forge"
OUT   = os.path.join(ROOT, "lead", "next_re_20261117_r14", "W173_layer_add")
EVID  = os.path.join(OUT, "EVIDENCE")
WORK  = os.path.join(OUT, "work")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

IB         = 0x400000
LAYER_BASE = 0x8A0360
LAYER_ELEM = 0x18
LAYER_N    = 5
LAYER_END  = LAYER_BASE + LAYER_N * LAYER_ELEM   # 0x8A03D8
LAYER_VFT  = 0x7E6060
ADD_IMPL   = 0x5519B0     # VectorClass<T>::Add
ADD_SLOT   = 0x1C         # LayerClass vftable 槽 +0x1C
LOCATE_SLOT= 0x10         # LayerClass vftable 槽 +0x10 (0x40CF00)
W94_OFF    = 0x94

X = capstone.x86

# 模块级反汇编器，供 reg_name 使用（capstone 5 无 capstone.x86.reg_name）
_MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
_MD.detail = True

_BIN = None
_INSNS = None
_STATS = {}
_VAS = None
_ATLAS_IV = None
_SYN_IV = None


def B():
    global _BIN
    if _BIN is None:
        _BIN = audit_lib.Bin(EXE)
    return _BIN


def md(skipdata=True):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = skipdata
    return m


def _rn(r):
    return _MD.reg_name(r) if r else None


def _opdict(op):
    sz = getattr(op, "size", None)
    if op.type == X.X86_OP_REG:
        return {"kind": "reg", "name": _rn(op.reg), "size": sz}
    if op.type == X.X86_OP_IMM:
        return {"kind": "imm", "val": op.imm, "size": sz}
    if op.type == X.X86_OP_MEM:
        mem = op.mem
        return {"kind": "mem", "base": _rn(mem.base), "index": _rn(mem.index),
                "scale": mem.scale, "disp": mem.disp, "seg": getattr(mem, "segment", None) and _rn(mem.segment), "size": sz}
    return {"kind": "other", "size": sz}


def text_insns():
    """全 .text 线性反汇编（skipdata=True）。返回真指令的轻量 dict 列表。"""
    global _INSNS, _VAS, _STATS
    if _INSNS is not None:
        return _INSNS
    b = B()
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    m = md(True)
    out = []
    nskip = 0
    for ins in m.disasm(data, t["va"]):
        if ins.id == 0:               # skipdata 产生的 .byte
            nskip += ins.size
            continue
        out.append({
            "va": ins.address, "sz": ins.size, "mn": ins.mnemonic, "os": ins.op_str,
            "ops": [_opdict(o) for o in ins.operands],
            "rw": [_MD.reg_name(r) for r in ins.regs_write],
        })
    _INSNS = out
    _VAS = [r["va"] for r in out]
    _STATS = dict(text_va=t["va"], text_end=t["va"] + t["rawsize"],
                  text_bytes=len(data), disasm_insns=len(out), skipped_bytes=nskip)
    return out


def stats():
    text_insns()
    return dict(_STATS)


def vas():
    text_insns()
    return _VAS


def fmt(rec):
    return "%08X  %-7s %s" % (rec["va"], rec["mn"], rec["os"])


def context(va, before=20, after=6):
    v = vas()
    ins = text_insns()
    i = bisect.bisect_left(v, va)
    if i >= len(v) or v[i] != va:
        i = bisect.bisect_left(v, va) - 1
    lo = max(0, i - before)
    hi = min(len(ins), i + 1 + after)
    return [fmt(ins[j]) for j in range(lo, hi)]


def _load_atlas_intervals():
    global _ATLAS_IV
    if _ATLAS_IV is not None:
        return _ATLAS_IV
    rows = []
    with open(ATLAS, "r", encoding="utf-8", errors="replace") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        ie = hdr.index("entry")
        iz = hdr.index("size")
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) <= max(ie, iz):
                continue
            try:
                e = int(p[ie], 16)
                z = int(p[iz], 10)
            except ValueError:
                continue
            if z <= 0:
                continue
            rows.append((e, e + z, "sub_%08X" % e))
    rows.sort()
    _ATLAS_IV = rows
    return rows


def _load_synth_intervals():
    """完全不依赖 atlas：入口 = 全 .text 的 call/jmp rel32 目标；区间到下一入口/text_end。"""
    global _SYN_IV
    if _SYN_IV is not None:
        return _SYN_IV
    ins = text_insns()
    st = stats()
    entries = set()
    for r in ins:
        if r["mn"] in ("call", "jmp"):
            for op in r["ops"]:
                if op["kind"] == "imm":
                    t = op["val"] & 0xFFFFFFFF
                    if st["text_va"] <= t < st["text_end"]:
                        entries.add(t)
    es = sorted(entries)
    rows = []
    for i, e in enumerate(es):
        end = es[i + 1] if i + 1 < len(es) else st["text_end"]
        rows.append((e, end, "syn_%08X" % e))
    _SYN_IV = rows
    return rows


def owner(va, which="atlas"):
    """函数区间包含判归属，返回 (entry, end, name) 或 None。"""
    ivs = _load_atlas_intervals() if which == "atlas" else _load_synth_intervals()
    es = [x[0] for x in ivs]
    i = bisect.bisect_right(es, va) - 1
    if i < 0:
        return None
    e, end, name = ivs[i]
    return (e, end, name) if e <= va < end else None


def boundary(bin_, entry, target, max_bytes=0x20000):
    """返回 (ok: bool|'unknown', insn_text|None, reason)。超限 => 'unknown'。"""
    ok, ins, why = audit_lib.boundary_check(bin_, entry, target, max_bytes=max_bytes)
    if isinstance(why, str) and ("未判定" in why or "bail" in why):
        return ("unknown", None, why)
    txt = None
    if ins is not None:
        txt = "%s %s" % (ins.mnemonic, ins.op_str)
    return (ok, txt, why)


def write_text(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for ln in lines:
            f.write(str(ln) + "\n")
