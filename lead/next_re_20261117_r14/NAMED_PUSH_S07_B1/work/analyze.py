# -*- coding: utf-8 -*-
"""NAMED-PUSH S07 B1 逐行四环取证驱动 + 三陷阱检查。
复用 recore/witness_core；只读 gamemd.exe；写域仅本 work 目录。
增强：扩展 RTTI 回扫(kmax=400)、主虚表标记(vt[0]==00410260)核对、
析构器锚点检测(atexit/free)、流 I/O 方向(0x410380 read / 0x410320 write)标注。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_INS_CALL, X86_OP_MEM, X86_REG_INVALID,
                          X86_INS_OR, X86_INS_AND, X86_INS_MOV, X86_INS_XCHG,
                          X86_INS_TEST, X86_OP_REG, X86_REG_EAX, X86_OP_IMM)

WORK = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(WORK, "b1_rows.json"), encoding="utf-8"))
ENTRIES = [(r["entry"], r["name"]) for r in rows]

MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True

MAIN_VT_SLOT0 = 0x00410260
SECONDARY_SLOT0 = {0x004105E0, 0x00410580, 0x00410590}
READ_API = 0x00410380   # IStream::Read via [eax+0xC]
WRITE_API = 0x00410320  # IStream::Write via [eax+0x10]
FREE_API = 0x007C8B3D   # operator delete / free
SCALAR_DTOR_GUARD = 0x0049B720  # seen in dtors (approx)

def ins_lines(insns, n=None):
    seq = []
    for ins in (insns if n is None else insns[:n]):
        seq.append("%08X: %s %s | %s" % (ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex()))
    return seq

def find_dispatch_sites(slot_off, cap=400):
    sites = []
    for ins in MD.disasm(R.TEXT_DATA, R.TEXT_VA):
        if ins.id == X86_INS_CALL and ins.operands and ins.operands[0].type == X86_OP_MEM:
            m = ins.operands[0].mem
            if m.disp == slot_off and m.base not in (X86_REG_INVALID, 0) and m.index in (X86_REG_INVALID, 0):
                sites.append("%08X" % ins.address)
                if len(sites) >= cap:
                    break
    return sites

def eax_trap_check(insns, sites):
    res = []
    idx = {ins.address: i for i, ins in enumerate(insns)}
    for s in sites:
        ta = int(s["test_addr"], 16) if isinstance(s["test_addr"], str) else s["test_addr"]
        ja = int(s["jcc_addr"], 16) if isinstance(s["jcc_addr"], str) else s["jcc_addr"]
        ti = idx.get(ta); ji = idx.get(ja)
        overwritten = []
        if ti is not None and ji is not None and ji > ti + 1:
            for ins in insns[ti+1:ji]:
                try:
                    _, wr = ins.regs_access()
                except Exception:
                    wr = []
                if X86_REG_EAX in wr:
                    idempotent = (ins.id in (X86_INS_OR, X86_INS_AND, X86_INS_MOV, X86_INS_XCHG, X86_INS_TEST)
                                  and len(ins.operands) == 2
                                  and ins.operands[0].type == X86_OP_REG and ins.operands[0].reg == X86_REG_EAX
                                  and ins.operands[1].type == X86_OP_REG and ins.operands[1].reg == X86_REG_EAX)
                    if not idempotent:
                        overwritten.append("%08X:%s %s" % (ins.address, ins.mnemonic, ins.op_str))
        res.append({"call_addr": s["call_addr"], "test_addr": s["test_addr"],
                    "jcc_addr": s["jcc_addr"], "eax_overwritten": overwritten})
    return res

def rtti_ext(refva, kmax=400):
    """扩展 RTTI 回扫：给定槽 VA，回扫 k=0..kmax 找 COL(sig=0, TD 名 .?AV)。"""
    best = None
    for k in range(0, kmax + 1):
        vb = refva - 4 * k
        c = W.u32(vb - 4)
        if not c:
            continue
        ci = W.parse_col(c)
        if not ci or ci["sig"] != 0:
            continue
        tdi = W.parse_td(ci["td"])
        if tdi and tdi["name"] and ".?AV" in tdi["name"]:
            best = {"vtable_base": vb, "slot_off": 4 * k, "slotno": k,
                    "col": ci["col"], "td": tdi["td"],
                    "name_va": tdi["name_va"], "rtti_name": tdi["name"]}
            break
    return best

def vtable_head(vb, n=4):
    vals = []
    for i in range(n):
        v = W.u32(vb + i*4) if vb else None
        vals.append("%08X" % v if v is not None else None)
    return vals

def classify_vtable(head):
    if not head or not head[0]:
        return "unknown"
    s0 = int(head[0], 16)
    if s0 == MAIN_VT_SLOT0:
        return "MAIN"
    if s0 in SECONDARY_SLOT0:
        return "SECONDARY"
    return "OTHER(0x%08X)" % s0

def func_is_dtor(fva):
    """粗判函数是否析构器：atexit 注册、含 free API 调用、尾部 call operator delete。"""
    if fva is None:
        return {"atexit": False, "has_free": False, "verdict": "unknown"}
    fva = int(fva, 16) if isinstance(fva, str) else fva
    atexit = bool(W.is_atexit_registered(fva))
    info = R.ATLAS.get("%08X" % fva, {})
    size = info.get("size", 0)
    code = R.read_va(fva, size if size else 512)
    insns = R.disasm(fva, code)
    has_free = False
    free_sites = []
    for ins in insns:
        if ins.id == X86_INS_CALL and ins.operands and ins.operands[0].type == X86_OP_IMM:
            callee = ins.operands[0].imm & 0xFFFFFFFF
            if callee == FREE_API:
                has_free = True
                free_sites.append("%08X" % ins.address)
    verdict = "DTOR" if (atexit or has_free) else "ctor/normal"
    return {"atexit": atexit, "has_free": has_free, "free_sites": free_sites, "verdict": verdict}

def io_direction(insns):
    """检测流 I/O API 直接调用点并标注方向。"""
    out = []
    for ins in insns:
        if ins.id == X86_INS_CALL and ins.operands and ins.operands[0].type == X86_OP_IMM:
            callee = ins.operands[0].imm & 0xFFFFFFFF
            if callee == READ_API:
                out.append({"site": "%08X" % ins.address, "api": "0x00410380", "dir": "READ(in)"})
            elif callee == WRITE_API:
                out.append({"site": "%08X" % ins.address, "api": "0x00410320", "dir": "WRITE(out)"})
    # 间接 [eax+0xC] / [eax+0x10] 调用
    for ins in insns:
        if ins.id == X86_INS_CALL and ins.operands and ins.operands[0].type == X86_OP_MEM:
            m = ins.operands[0].mem
            if m.disp == 0xC:
                out.append({"site": "%08X" % ins.address, "api": "[reg+0xC]", "dir": "READ(in)?"})
            elif m.disp == 0x10:
                out.append({"site": "%08X" % ins.address, "api": "[reg+0x10]", "dir": "WRITE(out)?"})
    return out

def analyze_entry(e, hint_name):
    ea = int(e, 16)
    info = R.ATLAS.get(e, {})
    size = info.get("size", 0)
    code = R.read_va(ea, size if size else 512)
    insns = R.disasm(ea, code)
    rec = {
        "entry": e, "hint_name": hint_name, "ea": ea, "atlas": info,
        "in_text": R.in_text(ea), "body_end": ea + size,
        "body_end_in_text": R.in_text(ea + size - 1) if size else None,
        "first_insns": ins_lines(insns, 16),
        "last_insns": ins_lines(insns[-10:]) if insns else [],
        "n_insn_disasm": len(insns),
        "n_skipdata": sum(1 for i in insns if i.id == 0),
        "all_insns": ins_lines(insns),
    }
    # ③ channel A/B
    a = R.channel_screen_A(insns)
    b = R.channel_screen_B(insns)
    rec["chA"] = {k: a[k] for k in ("p1", "p2", "p3")}
    rec["chA_sites"] = a["sites"]
    rec["chA_eax_trap"] = eax_trap_check(insns, a["sites"])
    rec["chB"] = []
    for t in b:
        rec["chB"].append({
            "jmp_addr": "%08X" % t["jmp_addr"], "mnemonic": t["mnemonic"],
            "op_str": t["op_str"], "table_va": ("%08X" % t["table_va"]) if t["table_va"] else None,
            "bound": t["bound"], "ncase": t["ncase"],
            "targets": [{"case": x["case"], "target": "%08X" % x["target"], "slot_va": "%08X" % x["slot_va"]} for x in t["targets"]],
        })
    # I/O 方向
    rec["io_direction"] = io_direction(insns)
    # ② 类身份 + ④ 候选：扩展 RTTI 回扫 + 主虚表核对
    refs = W.find_dword_refs(ea)
    slots = []
    for refva, sec in refs:
        ext = rtti_ext(refva, 400)
        if not ext:
            slots.append({"slot_va": "%08X" % refva, "section": sec, "rtti": None,
                          "head": vtable_head(refva - 0) if False else None})
            continue
        head = vtable_head(ext["vtable_base"], 4)
        vtclass = classify_vtable(head)
        w = W.find_vtable_writes(ext["vtable_base"])
        # 补主虚表注册点/安装点函数判别
        installs = []
        for g in w["global"]:
            f = W.find_containing_atlas_func(g["write_va"]) if g.get("write_va") else None
            g2 = dict(g)
            g2["in_func"] = f
            g2["atexit"] = bool(W.is_atexit_registered(f[0])) if f else False
            installs.append(g2)
        for rw in w["regdisp"]:
            f = W.find_containing_atlas_func(rw)
            installs.append({"write_va": "%08X" % rw, "global": None, "in_func": f,
                             "atexit": bool(W.is_atexit_registered(f[0])) if f else False})
        # 判别每个安装点宿主是否析构器
        for ins in installs:
            ins["host_dtor"] = func_is_dtor(ins["in_func"][0]) if ins.get("in_func") else None
        slots.append({
            "slot_va": "%08X" % refva, "section": sec,
            "vtable_base": "%08X" % ext["vtable_base"], "slot_off": ext["slot_off"],
            "slotno": ext["slotno"], "col": "%08X" % ext["col"], "td": "%08X" % ext["td"],
            "name_va": "%08X" % ext["name_va"], "rtti_name": ext["rtti_name"],
            "vtable_head": head, "vtable_class": vtclass,
            "dispatch_sites": find_dispatch_sites(ext["slot_off"]),
            "installs": installs,
        })
    rec["slots"] = slots
    # direct callers
    direct = W.find_direct_calls(ea)
    rec["direct_callers"] = ["%08X" % x for x in direct]
    return rec

out = []
for e, nm in ENTRIES:
    r = analyze_entry(e, nm)
    out.append(r)
    nslots = len(r["slots"])
    nslots_rtti = sum(1 for s in r["slots"] if s.get("rtti_name"))
    nslots_main = sum(1 for s in r["slots"] if s.get("vtable_class") == "MAIN")
    print("done %s %-28s A_p3=%d chB=%d slots=%d(rtti=%d,main=%d) direct=%d io=%d" % (
        e, nm, r["chA"]["p3"], len(r["chB"]), nslots, nslots_rtti, nslots_main,
        len(r["direct_callers"]), len(r["io_direction"])), flush=True)

with open(os.path.join(WORK, "analysis.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("wrote analysis.json (%d rows)" % len(out))
