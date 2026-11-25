#!/usr/bin/env python3
"""R132 task A: CFG-reachability function boundary vs 'first ret' boundary."""
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
text = None
for s in pe.sections:
    if s.Name.rstrip(b"\x00") == b".text":
        text = s
TEXT_VA = IB + text.VirtualAddress
TEXT_RAW = text.PointerToRawData
TEXT_SZ = text.Misc_VirtualSize
raw = open(EXE, "rb").read()
CODE = raw[TEXT_RAW:TEXT_RAW + TEXT_SZ]
TEXT_END = TEXT_VA + TEXT_SZ

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

JCC = set("""jo jno js jns je jz jne jnz jb jnae jc jnb jae jnc jbe jna ja jnbe
jl jnge jge jnl jle jng jg jnle jp jpe jnp jpo jcxz jecxz
loop loope loopne""".split())


def fetch(addr, n=16):
    off = addr - TEXT_VA
    if off < 0 or off >= TEXT_SZ:
        return None
    return CODE[off:off + n]


def dis1(addr):
    b = fetch(addr)
    if not b:
        return None
    for ins in md.disasm(b, addr, 1):
        return ins
    return None


def imm_target(op_str):
    try:
        return int(op_str, 16)
    except ValueError:
        return None


def cfg_walk(entry, maxn=4000):
    """Reachability walk; ret has no successors."""
    seen = {}
    work = [entry]
    order = []
    last_end = entry
    while work:
        a = work.pop()
        if a in seen:
            continue
        if a < TEXT_VA or a >= TEXT_END:
            seen[a] = ("OUT_OF_TEXT", 0, "")
            continue
        ins = dis1(a)
        if ins is None:
            seen[a] = ("UNDECODABLE", 0, "")
            continue
        seen[a] = (ins.mnemonic, ins.size, ins.op_str)
        order.append(a)
        end = a + ins.size
        if end > last_end:
            last_end = end
        if len(order) > maxn:
            break
        m = ins.mnemonic
        if m == "ret" or m.startswith("ret"):
            continue                      # ret: no successors
        if m == "jmp":
            t = imm_target(ins.op_str)
            if t is not None:
                work.append(t)
            continue
        if m in JCC:
            t = imm_target(ins.op_str)
            if t is not None:
                work.append(t)
            work.append(end)
            continue
        # everything else (incl. call): fall through
        work.append(end)
    return seen, order, last_end


def linear_to_first_ret(entry):
    a = entry
    n = 0
    while a < TEXT_END and n < 400:
        ins = dis1(a)
        if ins is None:
            break
        n += 1
        a += ins.size
        if ins.mnemonic.startswith("ret"):
            break
    return a - entry


def report(entry):
    seen, order, last_end = cfg_walk(entry)
    cfg_len = last_end - entry
    lin_len = linear_to_first_ret(entry)
    # instruction at first-ret boundary end == start of else block
    first_ret_end = entry + lin_len
    else_seen, else_order, else_last = cfg_walk(first_ret_end)
    out = {
        "entry": hex(entry),
        "cfg_len": cfg_len,
        "cfg_max_end": hex(last_end),
        "visited_insn_count": len(order),
        "first_ret_len": lin_len,
        "first_ret_end_va": hex(first_ret_end),
        "else_cfg_len": else_last - first_ret_end,
        "else_cfg_max_end": hex(else_last),
        "else_visited": len(else_order),
        "instructions": [
            {"addr": hex(a), "mnem": seen[a][0], "op": seen[a][2], "size": seen[a][1]}
            for a in sorted(order)
        ],
    }
    return out


res = {}
for name, va in (("A", 0x6BEDB0), ("B", 0x41C250)):
    res[name] = report(va)

# find which branch jumps past the first ret
for name, va in (("A", 0x6BEDB0), ("B", 0x41C250)):
    lin_end = va + res[name]["first_ret_len"]
    hits = []
    for ins in res[name]["instructions"]:
        if ins["mnem"] in JCC or ins["mnem"] == "jmp":
            t = imm_target(ins["op"])
            if t is not None and t >= lin_end:
                disp = dis1(t)
                hits.append({
                    "jump_addr": ins["addr"], "mnem": ins["mnem"], "op": ins["op"],
                    "target": hex(t),
                    "target_mnem": disp.mnemonic if disp else None,
                    "target_op": disp.op_str if disp else None,
                })
    res[name]["jumps_at_or_beyond_first_ret"] = hits

print(json.dumps(res, indent=1))
json.dump(res, open("a_cfg.json", "w"), indent=1)
