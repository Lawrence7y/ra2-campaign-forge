# -*- coding: utf-8 -*-
"""逐 entry 机械事实抽取（复用 core.py）。只读 gamemd.exe + atlas，写本 work 目录。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
from capstone.x86 import (
    X86_OP_IMM, X86_OP_MEM, X86_OP_REG,
    X86_INS_CALL, X86_INS_MOV, X86_INS_TEST, X86_INS_CMP,
    X86_INS_RET, X86_INS_JMP, X86_REG_EAX,
)

WORK = os.path.dirname(os.path.abspath(__file__))
CAND = json.load(open(os.path.join(WORK, "candidates.json"), encoding="utf-8"))
ENTRIES = [r["entry"] for sub in ("S07", "S11") for r in CAND[sub]]
NAME = {r["entry"]: (sub, r["name"]) for sub in ("S07", "S11") for r in CAND[sub]}

JCC = lambda ins: ins.mnemonic.startswith("j") and ins.mnemonic != "jmp"

def col_offset(col):
    return core.u32(col + 4)  # RTTICompleteObjectLocator.offset @+4

def classify_ctor_dtor(func_start, size, vtable_va):
    """返回 (kind, evidence dict)。ctor: 先 call base-ctor 且装 [this+0]; dtor: delete 标志/free。"""
    body = core.func_body(func_start, size)
    ev = {"func": core.hx(func_start), "size": size, "calls": [], "vptr_stores": [], "flags": [], "free": [], "ret_this": False}
    for i in body:
        if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM:
            ev["calls"].append(core.hx(i.operands[0].imm & 0xFFFFFFFF))
        if core.is_vptr_store(i, vtable_va):
            ev["vptr_stores"].append((core.hx(i.address), i.op_str))
        # delete flag: mov al/dl,1 或 test byte [esp+8],1
        if "esp+8" in i.op_str and ("byte" in i.op_str or "0x1" in i.op_str) and i.id in (X86_INS_TEST, X86_INS_CMP):
            ev["flags"].append(core.hx(i.address) + " " + i.mnemonic + " " + i.op_str)
        if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM \
                and (i.operands[0].imm & 0xFFFFFFFF) in core.FREE_CALLS:
            ev["free"].append(core.hx(i.address))
    # free 间接: call [0x...] where target maybe free wrapper — 仅记 imm
    tail = body[-8:]
    for i in tail:
        if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG \
                and i.operands[0].reg == X86_REG_EAX and i.operands[1].type == X86_OP_REG:
            ev["ret_this"] = core.hx(i.address) + " " + i.mnemonic + " " + i.op_str
    # 判定
    freeish = bool(ev["free"]) or bool(ev["flags"])
    basector = any(c in ("0055A6C0",) for c in ev["calls"])
    basedtor = any(c in ("0055A6F0",) for c in ev["calls"])
    if freeish or basedtor:
        kind = "DTOR"
    elif basector or ev["ret_this"]:
        kind = "CTOR"
    else:
        kind = "?"
    return kind, ev

def callee_exit_constants(t, maxbytes=0x200):
    """伪证被调返回约定：找 call 目标函数体里的 `mov eax,imm` + 邻近 ret。"""
    a = core.atlas_func_of(t)
    start, size = (a if a else (t, maxbytes))
    body = core.func_body(start, min(size, maxbytes) if size < 0x100000 else maxbytes)
    out = []
    for idx, i in enumerate(body):
        if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG \
                and i.operands[0].reg == X86_REG_EAX and i.operands[1].type == X86_OP_IMM:
            imm = i.operands[1].imm & 0xFFFFFFFF
            nxt = " ".join("%s %s" % (j.mnemonic, j.op_str) for j in body[idx+1:idx+4])
            out.append((core.hx(i.address), core.hx(imm), nxt))
        if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG \
                and i.operands[0].reg == X86_REG_EAX and i.operands[1].type == X86_OP_REG \
                and i.operands[1].reg == X86_REG_EAX:  # xor eax,eax 特判
            pass
        if i.mnemonic == "xor" and len(i.operands) == 2 and i.operands[0].reg == X86_REG_EAX and i.operands[1].reg == X86_REG_EAX:
            nxt = " ".join("%s %s" % (j.mnemonic, j.op_str) for j in body[idx+1:idx+4])
            out.append((core.hx(i.address), "00000000(xor)", nxt))
    return {"func": core.hx(start), "size": size, "consts": out}

def analyze_entry(entry):
    sub, name = NAME[entry]
    ea = int(entry, 16)
    d = {"entry": entry, "subsystem": sub, "name": name}
    # ---- ① 入口 / 边界 ----
    d["in_text"] = core.in_text(ea)
    a = core.atlas_func_of(ea)
    d["atlas"] = (core.hx(a[0]), a[1]) if a else None
    start = a[0] if a else ea
    size = a[1] if a else 0x100
    body = core.func_body(start, size)
    d["insn_count"] = len(body)
    d["first"] = [(core.hx(i.address), i.bytes.hex(), i.mnemonic, i.op_str) for i in body[:6]]
    d["last"] = [(core.hx(i.address), i.bytes.hex(), i.mnemonic, i.op_str) for i in body[-6:]]
    # ---- ② vtable 槽 / RTTI ----
    refs = core.dword_refs(ea)
    slots = []
    for r in refs:
        s = core.resolve_slot(r)
        if s:
            col = s["col"]
            slots.append({
                "slot_va": core.hx(r), "vtable": core.hx(s["vtable"]),
                "slot_index": s["slot_index"], "name": s["name"],
                "col": core.hx(col), "col_offset": col_offset(col),
                "col_sig": core.u32(col), "td": core.hx(s["td"]),
                "dword_ref_count": core.dword_ref_count(ea),
            })
    d["dword_refs"] = [core.hx(r) for r in refs]
    d["dword_ref_count"] = len(refs)
    d["slots"] = slots
    # 主表/副表判定：对每个 slot 的 vtable 找它所在类的所有表
    fam = {}
    for s in slots:
        td = s["td"]
        # 收集同 td 的所有 vtable：扫描所有 slot 的 vtable[-4] COL -> td
        fam.setdefault(td, set()).add(s["vtable"])
    # 对同 td 的其他表，回扫它们的 COL.offset 与 slot0 字节
    d["family_tables"] = []
    seen_vt = set()
    for td, vts in fam.items():
        for vt_s in vts:
            vt = int(vt_s, 16)
            if vt in seen_vt: continue
            seen_vt.add(vt)
            col = core.u32(vt - 4)
            off = col_offset(col) if col else None
            slot0 = core.u32(vt)
            b0 = core.read_va(slot0, 8).hex() if slot0 else ""
            d["family_tables"].append({"vtable": core.hx(vt), "col": core.hx(col) if col else None,
                                       "col_offset": off, "slot0": core.hx(slot0) if slot0 else None,
                                       "slot0_bytes": b0})
    # ---- ③b 站点：call -> test/cmp eax -> jcc ----
    sites = []
    for idx, i in enumerate(body):
        if i.id == X86_INS_CALL:
            # 下一个非 nop 指令
            nxt = None
            for j in range(idx+1, min(idx+4, len(body))):
                if body[j].id in (X86_INS_TEST, X86_INS_CMP):
                    nxt = body[j]; ni = j; break
                if body[j].id in (X86_INS_CALL, X86_INS_RET, X86_INS_JMP):
                    break
            if nxt and ni+1 < len(body) and JCC(body[ni+1]):
                callee = None
                if i.operands and i.operands[0].type == X86_OP_IMM:
                    callee = core.hx(i.operands[0].imm & 0xFFFFFFFF)
                else:
                    callee = i.op_str  # 间接
                sites.append({
                    "call": core.hx(i.address), "call_op": i.mnemonic + " " + i.op_str,
                    "callee": callee,
                    "test": core.hx(nxt.address), "test_op": nxt.mnemonic + " " + nxt.op_str,
                    "test_bytes": nxt.bytes.hex(),
                    "jcc": core.hx(body[ni+1].address), "jcc_op": body[ni+1].mnemonic + " " + body[ni+1].op_str,
                    "jcc_bytes": body[ni+1].bytes.hex(),
                    "gap": [core.hx(body[k].address) + " " + body[k].mnemonic + " " + body[k].op_str for k in range(idx+1, ni+1)],
                })
    d["sites"] = sites
    # 对每个直接 callee 做返回常量伪证
    d["callee_returns"] = {}
    for st in sites:
        c = st["callee"]
        if c and len(c) == 8 and all(ch in "0123456789ABCDEF" for ch in c):
            if c not in d["callee_returns"]:
                d["callee_returns"][c] = callee_exit_constants(int(c, 16))
    # ---- ④ direct callers ----
    callers = []
    for ia in core.IMM_INDEX.get(ea, []):
        ins = core.INS_BY_ADDR[ia]
        if ins.id == X86_INS_CALL:
            callers.append(core.hx(ia))
    d["direct_callers"] = callers
    # ---- ④ 安装点 + ctor/dtor 分类（对 family 每张表）----
    d["installs"] = []
    for ft in d["family_tables"]:
        vt = int(ft["vtable"], 16)
        sites_i = [i for i in core.install_sites(vt) if core.is_vptr_store(i, vt)]
        for i in sites_i:
            af = core.atlas_func_of(i.address)
            fs, fz = (af if af else (i.address, 0x80))
            kind, ev = classify_ctor_dtor(fs, fz, vt)
            d["installs"].append({
                "vtable": ft["vtable"], "col_offset": ft["col_offset"],
                "site": core.hx(i.address), "ins": i.mnemonic + " " + i.op_str,
                "bytes": i.bytes.hex(), "func": core.hx(fs), "func_size": fz,
                "kind": kind, "ev": ev,
            })
    # ---- ㉓ 本体内 vptr 自装点（析构器重装）----
    self_writes = []
    for s in slots:
        vt = int(s["vtable"], 16)
        for i in body:
            if core.is_vptr_store(i, vt):
                self_writes.append(core.hx(i.address) + " " + i.mnemonic + " " + i.op_str)
    d["self_vptr_writes_in_func"] = self_writes
    return d

out = {}
for e in ENTRIES:
    print("[analyze]", e, NAME[e][1], file=sys.stderr)
    out[e] = analyze_entry(e)

json.dump(out, open(os.path.join(WORK, "facts.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# 可读摘要
lines = []
for e in ENTRIES:
    d = out[e]
    lines.append("=" * 90)
    lines.append("%s %s  in_text=%s atlas=%s size=%s" % (e, d["name"], d["in_text"], d["atlas"], d["insn_count"]))
    lines.append("  dword_refs=%d -> %s" % (d["dword_ref_count"], d["dword_refs"]))
    for s in d["slots"]:
        lines.append("  SLOT slot_idx=%d vt=%s off=%s col=%s name=%s" %
                     (s["slot_index"], s["vtable"], s["col_offset"], s["col"], s["name"]))
    for ft in d["family_tables"]:
        lines.append("  FAM  vt=%s off=%s slot0=%s b0=%s" % (ft["vtable"], ft["col_offset"], ft["slot0"], ft["slot0_bytes"]))
    lines.append("  direct_callers=%s" % d["direct_callers"])
    for st in d["sites"]:
        lines.append("  SITE call=%s [%s] callee=%s | %s @%s | %s @%s | gap=%s" %
                     (st["call"], st["call_op"], st["callee"], st["test_op"], st["test"], st["jcc_op"], st["jcc"], st["gap"]))
    for c, r in d["callee_returns"].items():
        lines.append("  RET  callee=%s func=%s consts=%s" % (c, r["func"], r["consts"]))
    for ins in d["installs"]:
        lines.append("  INST vt=%s off=%s @%s %s func=%s sz=%s kind=%s vstores=%s ctor_calls=%s flags=%s free=%s" %
                     (ins["vtable"], ins["col_offset"], ins["site"], ins["ins"], ins["func"], ins["func_size"],
                      ins["kind"], ins["ev"]["vptr_stores"], ins["ev"]["calls"][:8], ins["ev"]["flags"], ins["ev"]["free"]))
    if d["self_vptr_writes_in_func"]:
        lines.append("  SELF-WRITES(㉓)=%s" % d["self_vptr_writes_in_func"])
open(os.path.join(WORK, "dump_summary.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("wrote facts.json + dump_summary.txt", file=sys.stderr)
