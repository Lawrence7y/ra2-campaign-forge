# -*- coding: utf-8 -*-
"""S04_PUSH_B2 逐行取证 dump。读 work/index.json + b2_entries.tsv，
对 18 个 entry 逐个 dump 四环锚点到 work/dump_<entry>.txt，并写 work/summary.tsv。
只读 gamemd.exe。
"""
import json, csv, collections
from pathlib import Path
import pefile, capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_EAX

ROOT = Path(r"D:\Project\ra2-campaign-forge")
EXE = ROOT / "ra2youli" / "gamemd.exe"
OUT = ROOT / "lead/next_re_20261117_r14/S04_PUSH_B2"
raw = EXE.read_bytes()
pe = pefile.PE(data=raw, fast_load=True)
ib = pe.OPTIONAL_HEADER.ImageBase
secs = []
for s in pe.sections:
    secs.append(dict(name=s.Name.rstrip(b"\0").decode("latin1"),
                     va=ib + s.VirtualAddress, vs=s.Misc_VirtualSize,
                     rs=s.SizeOfRawData, ptr=s.PointerToRawData))
by = {s["name"]: s for s in secs}

def va2off(va):
    for s in secs:
        if s["va"] <= va < s["va"] + s["rs"]:
            o = s["ptr"] + va - s["va"]
            if o + 4 <= len(raw):
                return o
    return None

def u32(va):
    o = va2off(va)
    if o is None:
        return None
    return int.from_bytes(raw[o:o + 4], "little")

def cstr(va, lim=200):
    o = va2off(va)
    if o is None:
        return ""
    b = raw[o:o + lim]
    z = b.find(b"\0")
    if z >= 0:
        b = b[:z]
    try:
        return b.decode("ascii")
    except Exception:
        return ""

text = by[".text"]
tva = text["va"]
tend = tva + text["vs"]
code = raw[text["ptr"]:text["ptr"] + text["vs"]]

def in_text(v):
    return v is not None and tva <= v < tend

idx = json.load(open(OUT / "work" / "index.json"))
entry2slots = {int(k, 16): v for k, v in idx["entry2slots"].items()}
direct = {int(k, 16): v for k, v in idx["direct"].items()}
installs = {int(k, 16): v for k, v in idx["installs"].items()}
dispatches = {int(k, 16): v for k, v in idx["dispatches"].items()}
livevt = {int(k, 16): v for k, v in idx["livevt"].items()}
vtables = {int(k, 16): v for k, v in idx["vtables"].items()}

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

JCC_NAMES = {"je", "jne", "jz", "jnz", "jg", "jge", "jl", "jle", "ja", "jae",
             "jb", "jbe", "js", "jns", "jo", "jno", "jp", "jnp", "jcxz", "jecxz"}

def is_eax(op):
    return op.type == X86_OP_REG and op.reg == X86_REG_EAX

def writes_eax(ins):
    if ins.id == capstone.x86.X86_INS_CALL:
        return True
    try:
        _, wr = ins.regs_access()
    except Exception:
        return True
    if X86_REG_EAX in wr:
        if ins.id in (capstone.x86.X86_INS_OR, capstone.x86.X86_INS_AND,
                      capstone.x86.X86_INS_MOV, capstone.x86.X86_INS_XCHG,
                      capstone.x86.X86_INS_TEST) and len(ins.operands) == 2 \
                and is_eax(ins.operands[0]) and is_eax(ins.operands[1]):
            return False
        return True
    return False

def test_kind(ins):
    if ins.mnemonic == "test" and len(ins.operands) == 2 and is_eax(ins.operands[0]) and is_eax(ins.operands[1]):
        return ("TEST_EAX", 0)
    if ins.mnemonic == "or" and len(ins.operands) == 2 and is_eax(ins.operands[0]) and is_eax(ins.operands[1]):
        return ("OR_EAX", 0)
    if ins.mnemonic == "cmp" and len(ins.operands) == 2 and is_eax(ins.operands[0]) and ins.operands[1].type == X86_OP_IMM:
        return ("CMP_IMM", ins.operands[1].imm & 0xFFFFFFFF)
    return None

def path_sig(insns, start_idx, maxn=16):
    calls, rets = set(), set()
    has_ret = False
    eax = None
    end_eax = None
    for j in range(start_idx, min(start_idx + maxn, len(insns))):
        ins = insns[j]
        if ins.id == 0:
            continue
        if ins.mnemonic == "call":
            if ins.operands and ins.operands[0].type == X86_OP_IMM:
                calls.add(ins.operands[0].imm & 0xFFFFFFFF)
            eax = None
        elif ins.mnemonic in ("xor", "sub") and len(ins.operands) == 2 and is_eax(ins.operands[0]) and is_eax(ins.operands[1]):
            eax = 0
        elif ins.mnemonic == "mov" and len(ins.operands) == 2 and is_eax(ins.operands[0]):
            eax = ((ins.operands[1].imm & 0xFFFFFFFF) if ins.operands[1].type == X86_OP_IMM else None)
        elif ins.mnemonic == "ret":
            has_ret = True
            if eax is not None:
                rets.add(eax)
            end_eax = eax
            break
        elif ins.mnemonic == "jmp":
            end_eax = eax
            break
        else:
            end_eax = eax
    return (sorted(calls), sorted(rets), has_ret, end_eax)

def atexit_status(site):
    """判断 install site 是否在 atexit 注册函数内（push dtor; call 7C978A）。
    简化：从 site 向前找最近的 call 0x7C978A 且中间有 push imm 指向包含 site 的函数。
    返回 (is_atexit, evidence)。这里先给保守标记：若在 site 前 0x40 内有 7C978A 调用则为疑似。"""
    # scan a window before site for E8 rel32 to 0x7C978A
    lo = max(tva, site - 0x80)
    win = raw[text["ptr"] + (lo - tva): text["ptr"] + (site - tva) + 8]
    atexit_bytes = (0x7C978A - (lo + 0))  # not used
    hits = []
    for ins in md.disasm(win, lo):
        if ins.mnemonic == "call" and ins.size == 5 and ins.bytes[0] == 0xE8:
            tgt = (ins.address + 5 + int.from_bytes(ins.bytes[1:5], "little", signed=True)) & 0xFFFFFFFF
            if tgt == 0x7C978A:
                hits.append(ins.address)
    return (bool(hits), hits)

def dump_entry(entry, size, name, grade):
    lines = []
    e = entry
    lines.append("# EVIDENCE entry %s name=%s grade=%s  (S04_PUSH_B2)" % (entry, name, grade))
    lines.append("## ① 入口")
    lines.append("  entry=0x%08X in_text=%s tva=0x%X tend=0x%X atlas_size=%d" % (e, in_text(e), tva, tend, size))
    off = va2off(e)
    if off is None:
        lines.append("  !! entry 无法映射文件偏移")
    else:
        lines.append("  bytes@entry = %s" % raw[off:off + min(size, 32)].hex(" "))
    # extent via local CFG (simple forward disasm from entry up to size, find first ret out of body)
    body_code = raw[text["ptr"] + (e - tva): text["ptr"] + (e - tva) + size] if in_text(e) else b""
    insns = list(md.disasm(body_code, e))
    last_ret = None
    for ins in insns:
        if ins.mnemonic == "ret":
            last_ret = ins.address + ins.size
    lines.append("  disasm insns=%d last_ret_end=%s body_end=0x%X" % (
        len(insns), ("0x%X" % last_ret) if last_ret else "none", e + size))

    # ---- ring 2 ----
    lines.append("## ② 类身份（RTTI 链 + 虚表归属）")
    slots = entry2slots.get(e, [])
    if not slots:
        lines.append("  未取得（entry2slots 无命中 —— 无 RTTI 虚表槽，②不成立）")
    else:
        for vt, slot, cls in sorted(slots):
            col = u32(vt - 4)
            td = u32(col + 0xC) if col else None
            nm = cstr(td + 8) if td else ""
            lines.append("  vt=0x%08X slot=+0x%X(%d) cls=%s COL@vt-4=0x%X TD@COL+0xC=0x%X TD+8='%s'" % (
                vt, slot * 4, slot, cls, col or 0, td or 0, nm))
            # install sites for this vt
            ins_site = []
            for g, lst in installs.items():
                for v, site in lst:
                    if v == vt:
                        ax, ah = atexit_status(site)
                        ins_site.append((g, site, ax, ah))
            lines.append("    install sites (global vt 写点): %d" % len(ins_site))
            for g, site, ax, ah in ins_site[:12]:
                lines.append("      g=0x%X site=0x%X atexit_near=%s hits=%s" % (g, site, ax, [hex(x) for x in ah]))

    # ---- ring 4 ----
    lines.append("## ④ 使用见证（direct call 站点 / 活虚表派发）")
    dc = direct.get(e, [])
    lines.append("  direct E8 sites count=%d: %s" % (len(dc), " ".join("0x%X" % x for x in dc[:16])))
    lv = livevt.get(e, [])
    lines.append("  livevt witnesses count=%d" % len(lv))
    for g, vt, slot, site1, site2 in lv[:16]:
        vs = set(v for v, s in installs.get(g, []))
        ax1, ah1 = atexit_status(site1)
        lines.append("    g=0x%X vt=0x%X slot=+0x%X install=0x%X dispatch=0x%X single_vt=%s atexit_near_install=%s" % (
            g, vt, slot * 4, site1, site2, len(vs) == 1, ax1))
    # also list dispatches whose vt[slot]==entry but not livevt (dead/atexit)
    lines.append("  (all vtable slots v==entry from index; livevt is subset with install+dispatch)")

    # ---- ring 3: ③b② pattern ----
    lines.append("## ③ 整体合同（③b 形态检测）")
    idx_by_addr = {ins.address: i for i, ins in enumerate(insns)}
    found = []
    for i, ins in enumerate(insns):
        if ins.mnemonic != "call":
            continue
        k = None
        for j in range(i + 1, min(i + 4, len(insns))):
            mid = insns[j]
            if mid.id == 0 or mid.mnemonic in ("jmp", "ret", "call") or mid.mnemonic in JCC_NAMES or writes_eax(mid):
                break
            tk = test_kind(mid)
            if tk:
                k = j
                break
        if k is None:
            continue
        for m in range(k + 1, min(k + 3, len(insns))):
            jc = insns[m]
            if jc.mnemonic in JCC_NAMES:
                gap = insns[k + 1:m]
                bad_gap = any(g.id == 0 or g.mnemonic in ("jmp", "ret", "call") or g.mnemonic in JCC_NAMES or writes_eax(g) for g in gap)
                tgt = None
                if jc.operands and jc.operands[0].type == X86_OP_IMM:
                    tgt = jc.operands[0].imm & 0xFFFFFFFF
                ti = idx_by_addr.get(tgt) if tgt is not None else None
                sig_t = path_sig(insns, ti) if ti is not None else ([], [], False, "OUT_OF_BODY")
                sig_f = path_sig(insns, m + 1)
                diff = sig_t != sig_f
                found.append((ins.address, k and insns[k].address, insns[k].mnemonic,
                              test_kind(insns[k]), jc.address, jc.mnemonic, jc.mnemonic,
                              tgt, bad_gap, diff, sig_t, sig_f))
                break
            if writes_eax(jc) or jc.id == 0:
                break
            if jc.mnemonic in ("jmp", "ret", "call"):
                break
    lines.append("  ③b② 候选站点数=%d" % len(found))
    for f in found:
        call_a, cmp_a, cmp_mn, tk, jcc_a, jcc_mn, _, tgt, bad_gap, diff, sig_t, sig_f = f
        lines.append("    call@0x%X -> %s@0x%X %s -> %s@0x%X -> tgt=%s | eax_trap_gap=%s path_diff=%s" % (
            call_a, cmp_mn, cmp_a, tk, jcc_mn, jcc_a,
            ("0x%X" % tgt) if tgt else "none", bad_gap, diff))
        lines.append("      sig_t=%r sig_f=%r" % (sig_t, sig_f))

    # jump tables: jmp dword ptr [reg*scale + disp] or [reg+disp*4]
    jt = []
    for ins in insns:
        if ins.mnemonic == "jmp" and ins.operands and ins.operands[0].type == X86_OP_MEM:
            m = ins.operands[0].mem
            jt.append((ins.address, ins.mnemonic, ins.op_str, m.base, m.index, m.scale, m.disp))
    lines.append("  jump-table(indirect jmp mem) count=%d" % len(jt))
    for j in jt[:8]:
        lines.append("    jmp@0x%X %s base=%s idx=%s scale=%s disp=%s" % j)

    # loops with non-stack write: backward jcc/jmp within body
    loops = []
    for i, ins in enumerate(insns):
        if ins.mnemonic in JCC_NAMES or ins.mnemonic == "jmp":
            if ins.operands and ins.operands[0].type == X86_OP_IMM:
                t = ins.operands[0].imm & 0xFFFFFFFF
                if t < ins.address and e <= t < e + size:
                    loops.append((ins.address, ins.mnemonic, t))
    lines.append("  backward-branch count=%d" % len(loops))
    for l in loops[:12]:
        lines.append("    %s@0x%X -> 0x%X (back)" % (l[1], l[0], l[2]))

    # ---- full disassembly (entry-relative) ----
    lines.append("## full disassembly (entry-relative, atlas size)")
    for ins in insns:
        off_r = ins.address - e
        lines.append("  +0x%04X  %-20s %s %s" % (off_r, ins.bytes.hex(), ins.mnemonic, ins.op_str))

    return "\n".join(lines)

def main():
    entries = []
    with open(OUT / "work" / "b2_entries.tsv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            entries.append(r)
    summary = []
    for r in entries:
        e = int(r["entry"], 16)
        size = int(r["size"])
        txt = dump_entry(e, size, r["name"], r["grade"])
        (OUT / "work" / ("dump_%s.txt" % r["entry"])).write_text(txt, encoding="utf-8")
        slots = entry2slots.get(e, [])
        dc = direct.get(e, [])
        lv = livevt.get(e, [])
        summary.append([r["entry"], r["name"], len(slots),
                        ";".join("%s/+0x%X" % (v[2], v[1] * 4) for v in slots[:3]),
                        len(dc), ";".join("0x%X" % x for x in dc[:8]),
                        len(lv), ";".join("0x%X/vt%X/+0x%X" % (v[3], v[1], v[2] * 4) for v in lv[:4])])
    with open(OUT / "work" / "summary.tsv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["entry", "name", "n_slots", "slots", "n_direct", "direct_sites", "n_livevt", "livevt"])
        w.writerows(summary)
    print("dumped %d entries" % len(entries))
    for s in summary:
        print(s[0], s[1], "slots=%d"%s[2], s[3], "direct=%d"%s[4], "lv=%d"%s[6])

if __name__ == "__main__":
    main()
