# -*- coding: utf-8 -*-
"""A09 probe1: 全 IAT 枚举 + 消息投递面（user32 消息函数）调用点普查。零真机，只读镜像。"""
import sys, struct, pickle
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("sha256:", eng.sha[:16], "...")
print("coverage: %.2f%% / %d insns / %d resync" % eng.coverage)

# ---- 1) 枚举整个 import table ----
raw = eng.raw
opt = eng.opt
dd = opt + 96
imp_rva = struct.unpack_from("<I", raw, dd + 8)[0]
o = eng.fo(eng.IB + imp_rva)
imports = []  # (slot, dll, func)
k = 0
while True:
    d = raw[o + k * 20: o + k * 20 + 20]
    if len(d) < 20 or d == b"\0" * 20:
        break
    oft, _ts, _fc, name_rva, ft = struct.unpack_from("<IIIII", d, 0)
    no = eng.fo(eng.IB + name_rva)
    dll = raw[no:raw.index(b"\0", no)].decode("ascii", "replace")
    thunk = oft or ft
    j = 0
    while True:
        tv = struct.unpack_from("<I", raw, eng.fo(eng.IB + thunk) + j * 4)[0]
        if tv == 0:
            break
        slot = eng.IB + ft + j * 4
        if tv & 0x80000000:
            imports.append((slot, dll, "ord#%d" % (tv & 0xFFFF)))
        else:
            ho = eng.fo(eng.IB + tv + 2)
            imports.append((slot, dll, raw[ho:raw.index(b"\0", ho)].decode("ascii", "replace")))
        j += 1
    k += 1
print("total imports:", len(imports))

# ---- 2) 消息相关函数 ----
MSGNAMES = ("SendMessageA", "SendMessageW", "PostMessageA", "PostMessageW",
            "DispatchMessageA", "DispatchMessageW", "PeekMessageA", "PeekMessageW",
            "GetMessageA", "GetMessageW", "TranslateMessage", "CallWindowProcA",
            "SendMessageTimeoutA", "PostThreadMessageA", "BroadcastSystemMessageA")
targets = [(slot, dll, fn) for (slot, dll, fn) in imports
           if dll.lower().startswith("user32") and fn in MSGNAMES]
print("\n=== message-related IAT slots ===")
for slot, dll, fn in targets:
    print("slot=0x%08X  %s!%s" % (slot, dll, fn))

# ---- 3) 每个槽的全部 call/jmp 引用 ----
print("\n=== call sites (message funcs) ===")
sites = {}
for slot, dll, fn in targets:
    refs = []
    for ins in eng.stream:
        if ins.mnemonic not in ("call", "jmp"):
            continue
        try:
            ops = ins.operands
        except Exception:
            continue
        if ops and ops[0].type == 3 and ops[0].mem.base == 0 and ops[0].mem.index == 0 \
                and ops[0].mem.disp == slot:
            refs.append((ins.address, ins.mnemonic))
    sites[(dll, fn, slot)] = refs
    print("\n%s!%s  slot=0x%08X  refs=%d" % (dll, fn, slot, len(refs)))
    for a, m in refs:
        print("   %s 0x%08X" % (m, a))

with open(r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\A09\A09_sites.pkl", "wb") as f:
    pickle.dump({"imports": imports, "targets": targets, "sites": sites}, f)
print("\nOK probe1")
