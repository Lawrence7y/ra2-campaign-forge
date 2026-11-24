# -*- coding: utf-8 -*-
"""逐行分析：③b② 站点（call→test/cmp→jcc，两路签名不同、无 eax 覆写、被调多值返回）
   + ④ 安装点（所在函数 ctor/dtor 判别、atexit、是否落在 entry 自身=㉓）。"""
import json, os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = json.load(open(os.path.join(HERE, "b1_rows.json"), encoding="utf-8"))

JCC = set()
for n in dir():
    if n.startswith("X86_INS_J"):
        JCC.add(globals()[n])
JCC.discard(X86_INS_JMP)

def is_eax_reg(op):
    return op.type == X86_OP_REG and op.reg == X86_REG_EAX

def test_kind(ins):
    if ins.id == X86_INS_TEST and len(ins.operands) == 2 and is_eax_reg(ins.operands[0]) and is_eax_reg(ins.operands[1]):
        return ("TEST_EAX", 0)
    if ins.id == X86_INS_OR and len(ins.operands) == 2 and is_eax_reg(ins.operands[0]) and is_eax_reg(ins.operands[1]):
        return ("OR_EAX", 0)
    if ins.id == X86_INS_CMP and len(ins.operands) == 2 and is_eax_reg(ins.operands[0]):
        o = ins.operands[1]
        if o.type == X86_OP_REG:
            return ("CMP_REG", ins.reg_name(o.reg))
        if o.type == X86_OP_IMM:
            return ("CMP_IMM", o.imm & 0xFFFFFFFF)
        if o.type == X86_OP_MEM:
            return ("CMP_MEM", None)
    return None

def writes_eax(ins):
    if not ins.operands:
        return False
    d = ins.operands[0]
    if d.type == X86_OP_REG and d.reg == X86_REG_EAX:
        if ins.id in (X86_INS_CMP, X86_INS_TEST):
            return False
        return True
    if d.type == X86_OP_MEM:
        # 内存写不改 eax
        return False
    return False

def path_sig(insns, idx, maxn=24):
    calls, consts, stores = [], set(), []
    end = None
    eax = None
    for j in range(idx, min(idx + maxn, len(insns))):
        ins = insns[j]
        if ins.id == 0:
            continue
        if ins.id == X86_INS_CALL:
            if ins.operands and ins.operands[0].type == X86_OP_IMM:
                calls.append(hx(ins.operands[0].imm & 0xFFFFFFFF))
            eax = None
        elif ins.id == X86_INS_MOV and len(ins.operands) == 2:
            d, s = ins.operands
            if d.type == X86_OP_REG and d.reg == X86_REG_EAX:
                eax = (s.imm & 0xFFFFFFFF) if s.type == X86_OP_IMM else None
            if d.type == X86_OP_MEM and s.type == X86_OP_IMM:
                stores.append((hx(ins.address), ins.op_str))
        elif ins.id in (X86_INS_XOR, X86_INS_SUB) and len(ins.operands) == 2 \
                and is_eax_reg(ins.operands[0]) and is_eax_reg(ins.operands[1]):
            eax = 0
        if ins.id == X86_INS_RET:
            end = ("ret", eax)
            if eax is not None:
                consts.add(eax)
            break
        if ins.id == X86_INS_JMP:
            if ins.operands and ins.operands[0].type == X86_OP_IMM:
                t = ins.operands[0].imm & 0xFFFFFFFF
                if in_text(t):
                    for k in range(len(insns)):
                        if insns[k].address == t:
                            sub = path_sig(insns, k, maxn)
                            calls += sub["calls"]; consts |= set(sub["consts"])
                            end = sub["end"]; stores += sub["stores"]
                            return {"calls": sorted(calls), "consts": sorted(consts),
                                    "end": end, "stores": stores[:6]}
            end = ("jmp", eax)
            break
    return {"calls": sorted(calls), "consts": sorted(consts), "end": end, "stores": stores[:6]}

def body_of(entry, cap=1200):
    """从 entry 反汇编，直到遇到 0xCC 填充/连续 int3 或超出 .text。"""
    data = read_va(entry, cap)
    ins = dis(entry, data)
    out = []
    end = entry
    for i in ins:
        if i.id == 0:      # skipdata -> 遇到数据/填充
            break
        out.append(i)
        end = i.address + i.size
        if i.id == X86_INS_RET and len(out) > 2:
            # 看后面是否 int3 对齐（说明函数结束）
            nxt = read_va(end, 4)
            if nxt[:1] == b"\xcc" or nxt[:1] == b"\x90":
                break
    return out

def callee_profile(callee, cap=3000):
    """被调返回约定：枚举 ret 前的 eax 常量集 + ret 数。"""
    if not in_text(callee):
        return None
    ins = dis(callee, read_va(callee, cap))
    consts, nret, eax = set(), 0, ("?",)
    seen_ret = []
    for i in ins:
        if i.id == 0:
            break
        if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG \
                and i.operands[0].reg == X86_REG_EAX:
            s = i.operands[1]
            eax = ("imm", s.imm & 0xFFFFFFFF) if s.type == X86_OP_IMM else ("other",)
        elif i.id in (X86_INS_XOR, X86_INS_SUB) and len(i.operands) == 2 \
                and is_eax_reg(i.operands[0]) and is_eax_reg(i.operands[1]):
            eax = ("imm", 0)
        elif i.id == X86_INS_OR and len(i.operands) == 2 and is_eax_reg(i.operands[0]) \
                and i.operands[1].type == X86_OP_IMM:
            eax = ("imm", (eax[1] | i.operands[1].imm) & 0xFFFFFFFF) if eax[0] == "imm" else ("other",)
        elif i.id == X86_INS_CALL:
            eax = ("callret",)
        elif i.id == X86_INS_RET:
            nret += 1
            seen_ret.append((hx(i.address), eax))
            if eax[0] == "imm":
                consts.add(eax[1])
            eax = ("?",)
            if nret > 40:
                break
    return {"consts": sorted(consts), "n_ret": nret, "rets": [(a, str(b)) for a, b in seen_ret][:12]}

FREE = {0x7C8B3D, 0x406060, 0x7C8B3A}

def func_start_of(site):
    """回扫找函数入口：候选 = 指令起始且前一字节是 int3/nop/ret 结尾/段首；取最大不越过 site。"""
    best = None
    # 候选：site 前 0..2000 字节内，前导为 0xCC/0x90 填充或 0xC2/0xC3 ret
    for d in range(0, 2400):
        va = site - d
        if va < TEXT_VA:
            break
        prev = read_va(va - 1, 1)
        if not prev:
            continue
        if prev[0] in (0xCC, 0x90, 0xC3):
            # 从 va 线性反汇编，看能否精确到达 site
            ins = dis(va, read_va(va, site - va + 8))
            if any(i.address == site for i in ins) and ins and ins[0].address == va:
                best = va
                break
        elif prev[0] == 0xC2:  # ret imm16 占 3 字节
            va2 = va - 2
            b = read_va(va2, 3)
            if len(b) == 3 and b[0] == 0xC2:
                ins = dis(va, read_va(va, site - va + 8))
                if any(i.address == site for i in ins):
                    best = va
                    break
    return best

def func_profile(fstart, cap=600):
    ins = dis(fstart, read_va(fstart, cap))
    body = []
    for i in ins:
        if i.id == 0:
            break
        body.append(i)
        if i.id == X86_INS_RET:
            nxt = read_va(i.address + i.size, 2)
            if nxt[:1] in (b"\xcc", b"\x90", b""):
                break
    frees, flags, vptr = [], [], []
    rets = 0
    tail_eax = None
    for i in body:
        if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM:
            t = i.operands[0].imm & 0xFFFFFFFF
            if t in FREE:
                frees.append((hx(i.address), hx(t)))
        if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG \
                and i.operands[1].type == X86_OP_IMM and i.operands[0].reg in (X86_REG_DL, X86_REG_AL, X86_REG_BL):
            if (i.operands[1].imm & 0xFF) == 1:
                flags.append((hx(i.address), i.mnemonic + " " + i.op_str))
        if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_MEM \
                and i.operands[0].size == 4 and i.operands[1].type == X86_OP_IMM \
                and 0x7E0000 <= (i.operands[1].imm & 0xFFFFFFFF) <= 0x800000:
            vptr.append((hx(i.address), i.op_str))
        if i.id == X86_INS_RET:
            rets += 1
    last = body[-3:] if body else []
    for i in last:
        if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG \
                and i.operands[0].reg == X86_REG_EAX:
            tail_eax = i.mnemonic + " " + i.op_str
    return {"func": hx(fstart), "n_insn": len(body), "frees": frees, "del_flags": flags,
            "vptr_stores": vptr, "n_ret": rets, "tail_eax": tail_eax,
            "is_dtor": bool(frees) or (bool(flags) and len(vptr) >= 1)}

results = {}
for r in ROWS:
    ea = int(r["entry"], 16)
    body = body_of(ea)
    sites = []
    for idx, ins in enumerate(body):
        if ins.id != X86_INS_CALL:
            continue
        callee = None
        if ins.operands and ins.operands[0].type == X86_OP_IMM:
            callee = ins.operands[0].imm & 0xFFFFFFFF
        elif ins.operands and ins.operands[0].type == X86_OP_MEM:
            m = ins.operands[0].mem
            callee = "ind:%s%s" % (ins.reg_name(m.base) if m.base else "", ("+%#x" % m.disp) if m.disp else "")
        for k in range(idx + 1, min(idx + 4, len(body))):
            tk = test_kind(body[k])
            if not tk:
                continue
            # eax 覆写检查
            over = [hx(body[m].address) + ":" + body[m].mnemonic + " " + body[m].op_str
                    for m in range(k + 1, min(k + 3, len(body))) if writes_eax(body[k + 0]) if False]
            over = []
            for m in range(k + 1, min(k + 3, len(body))):
                if body[m].id in JCC:
                    break
                if writes_eax(body[m]):
                    over.append(hx(body[m].address) + " " + body[m].mnemonic + " " + body[m].op_str)
            for m in range(k + 1, min(k + 3, len(body))):
                jc = body[m]
                if jc.id not in JCC:
                    continue
                tgt = jc.operands[0].imm & 0xFFFFFFFF if jc.operands and jc.operands[0].type == X86_OP_IMM else None
                ti = next((x for x in range(len(body)) if body[x].address == tgt), None)
                sig_t = path_sig(body, ti) if ti is not None else None
                sig_f = path_sig(body, m + 1)
                same = (sig_t is not None and
                        sig_t["calls"] == sig_f["calls"] and sig_t["consts"] == sig_f["consts"] and
                        sig_t["end"] == sig_f["end"])
                prof = callee_profile(callee) if isinstance(callee, int) else None
                sites.append({
                    "call": hx(ins.address), "call_bytes": ins.bytes.hex(),
                    "call_text": ins.mnemonic + " " + ins.op_str, "callee": hx(callee) if isinstance(callee, int) else callee,
                    "test": hx(body[k].address), "test_bytes": body[k].bytes.hex(),
                    "test_text": body[k].mnemonic + " " + body[k].op_str, "kind": tk[0], "imm": tk[1] if isinstance(tk[1], int) else str(tk[1]),
                    "jcc": hx(jc.address), "jcc_bytes": jc.bytes.hex(),
                    "jcc_text": jc.mnemonic + " " + jc.op_str, "target": hx(tgt) if tgt else None,
                    "fallthrough": hx(jc.address + jc.size),
                    "eax_overwrite": over,
                    "sig_taken": sig_t, "sig_fall": sig_f, "same_sig": same,
                    "callee_prof": prof,
                })
                break
            break
    # ④ 安装点
    vt = resolve_slot(dword_refs(ea)[0]) if dword_refs(ea) else None
    installs = []
    if vt:
        for ins in install_sites(vt["vtable"]):
            if not is_vptr_store(ins, vt["vtable"]):
                continue
            fs = func_start_of(ins.address)
            prof = func_profile(fs) if fs else None
            atex = is_atexit_registered(fs) if fs else []
            installs.append({"site": hx(ins.address), "insn": ins.mnemonic + " " + ins.op_str,
                             "bytes": ins.bytes.hex(),
                             "in_entry": (ea <= ins.address < ea + len(body) * 8 and
                                          any(b.address == ins.address for b in body)),
                             "func_start": hx(fs) if fs else None,
                             "func": prof, "atexit": atex})
    results[r["entry"]] = {"entry": r["entry"], "name": r["name"], "body_len": len(body),
                           "body": [(hx(i.address), i.mnemonic + " " + i.op_str, i.bytes.hex()) for i in body],
                           "vtable": vt, "sites": sites, "installs": installs}
    print("=" * 96)
    print(r["entry"], r["name"], "body_insn=%d sites=%d" % (len(body), len(sites)))
    for s in sites:
        print("   site call %s %-22s -> %s | %s %s | %s %s -> %s / fall %s | over=%s same=%s" % (
            s["call"], s["call_text"], s["callee"], s["test"], s["test_text"],
            s["jcc"], s["jcc_text"], s["target"], s["fallthrough"],
            s["eax_overwrite"], s["same_sig"]))
        if s["callee_prof"]:
            print("        callee consts=%s n_ret=%d" % (
                [hex(c) for c in s["callee_prof"]["consts"]], s["callee_prof"]["n_ret"]))
    for i in installs:
        print("   install %s  %-42s in_entry=%s func=%s dtor=%s atexit=%s" % (
            i["site"], i["insn"], i["in_entry"], i["func_start"],
            i["func"]["is_dtor"] if i["func"] else None, i["atexit"]))

json.dump(results, open(os.path.join(HERE, "analysis.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nwritten analysis.json")
