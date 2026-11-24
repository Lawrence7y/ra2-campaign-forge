"""查询层：基于 index.json + core 的反汇编。"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

IDX = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.json")))
CALLS = [(a, t) for a, t in IDX["calls"]]
VINST = [(a, imm, m) for a, imm, m in IDX["vinstall"]]
MOVABS = [(a, imm, d) for a, imm, d in IDX["mov_abs_imm"]]


def vt_installs(vt):
    return [(a, m) for a, imm, m in VINST if imm == vt]


def global_writes(g):
    return [(a, imm) for a, imm, d in MOVABS if d == g]


def callers(t):
    return [a for a, x in CALLS if x == t]


def callee_at(site):
    for a, x in CALLS:
        if a == site:
            return x
    return None


def atexit_targets():
    """所有 push imm ; call 0x7C978A 的 imm 序列。"""
    res = []
    for site, tgt in CALLS:
        if tgt != 0x7C978A:
            continue
        # 解码 site 前 8 字节
        ins = C.disasm(site - 8, 4, nbytes=12)
        prev = [i for i in ins if i.address + i.size == site]
        if prev and prev[-1].mnemonic == "push" and prev[-1].operands[0].type == 2:
            res.append((prev[-1].operands[0].imm & 0xFFFFFFFF, site))
    return res


def fn_kind(fn_entry, size):
    """粗分 ctor / dtor / other，给出证据串。"""
    ev = []
    # atexit 注册自身
    regs = atexit_targets()
    if any(t == fn_entry for t, s in regs):
        ev.append(f"atexit(self) via 0x{fn_entry:08X} push")
    freecalls = [a for a, x in CALLS if x == 0x7C8B3D and fn_entry <= a < fn_entry + size]
    if freecalls:
        ev.append("free 0x7C8B3D @ " + ",".join(f"{a:08X}" for a in freecalls[:4]))
    dtorcalls = [a for a, x in CALLS if x in (0x4101F0, 0x4109C0, 0x410320) and fn_entry <= a < fn_entry + size]
    return ev
