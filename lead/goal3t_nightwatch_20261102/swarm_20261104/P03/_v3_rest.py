# -*- coding: utf-8 -*-
"""V-P03 核验探针 3（合并版）：写0切片 / 宿主定界 / push 路径 / measure 窗 / 空桩IAT / 死代码 / 杂项"""
import sys, struct
from collections import defaultdict, Counter
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine
import capstone as CS

eng = Engine()
out = []
def P(*a):
    s = " ".join(str(x) for x in a)
    out.append(s); print(s, flush=True)

S = eng.stream
P("[coverage] %.2f%% / %d / %d" % eng.coverage)

X86 = {name: getattr(CS.x86_const, "X86_REG_" + name) for name in
       ["EAX","EBX","ECX","EDX","ESI","EDI","EBP","ESP"]}

def text_call_sites(target):
    tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
    res = []
    i = tb.find(b"\xe8")
    while i >= 0:
        va = eng.TLO + i
        if i + 5 <= len(tb):
            rel = struct.unpack_from("<i", tb, i + 1)[0]
            if va + 5 + rel == target: res.append(va)
        i = tb.find(b"\xe8", i + 1)
    return res

def sec_of(va):
    for nm, sva, vsz, rp, rsz in eng.SEC:
        if sva <= va < sva + vsz: return nm
    return "?"

def file_dword_search(val):
    pat = struct.pack("<I", val)
    res, i = [], eng.raw.find(pat)
    while i >= 0:
        res.append(i); i = eng.raw.find(pat, i + 1)
    return res

# ================= A. 9/10 写 0：独立反向切片 =================
P("")
P("===== [A] 写 0 复核（独立切片） =====")
WRITES = {
    "W1": 0x52DA08, "W2": 0x55DE81, "W3": 0x5B7329, "W4": 0x5BB20C,
    "W5": 0x5E550F, "W6": 0x5E747C, "W7": 0x68466B, "W8": 0x686765,
    "W9": 0x795234, "W10": 0x79758C,
}
HOSTS = {
    "W1": (0x52D9A0, 0x52F3F0), "W3": (0x5B7090, 0x5B7360), "W4": (0x5BAC60, 0x5BB290),
    "W5": (0x5E3D10, 0x5E5F10), "W6": (0x5E7460, 0x5E74E0), "W7": (0x684620, 0x684C30),
    "W8": (0x686730, 0x686890), "W9": (0x794BA0, 0x795650), "W10": (0x7970D0, 0x7975AC),
}

def build_cfg(lo, hi):
    ins = [i for i in S if lo <= i.address < hi]
    nxt = {ins[k].address: (ins[k+1].address if k+1 < len(ins) else None) for k in range(len(ins))}
    pred = defaultdict(list); indirect = []; outs = []
    for I in ins:
        a, mn = I.address, I.mnemonic
        try: ops = I.operands
        except Exception: ops = []
        tgt = ops[0].imm if (ops and ops[0].type == 2) else None
        if mn == "ret": continue
        if mn == "jmp":
            if tgt is None: indirect.append(a)
            elif lo <= tgt < hi: pred[tgt].append(a)
            else: outs.append((a, tgt))
            continue
        if mn.startswith("j"):
            if tgt is None: indirect.append(a)
            elif lo <= tgt < hi: pred[tgt].append(a)
            if nxt[a] is not None: pred[nxt[a]].append(a)
            continue
        if nxt[a] is not None: pred[nxt[a]].append(a)
    return ins, nxt, pred, indirect, outs

def slice_defs(lo, hi, wva, regname):
    rid = X86[regname]
    ins, nxt, pred, indirect, outs = build_cfg(lo, hi)
    seen, work = set(), [wva]
    while work:
        a = work.pop()
        if a in seen: continue
        seen.add(a)
        for p in pred.get(a, ()):
            if p not in seen: work.append(p)
    defs = []
    for I in ins:
        if I.address not in seen: continue
        try: ops = I.operands
        except Exception: continue
        for op in ops:
            if op.type == 1 and op.reg == rid and (op.access & 2):
                defs.append((I.address, I.mnemonic, I.op_str)); break
    return seen, defs, indirect, outs

REG_OF = {"W1": "EBX", "W4": "EBP", "W5": "ESI", "W7": "ESI", "W8": "EBP", "W10": "EAX"}
for w, reg in REG_OF.items():
    lo, hi = HOSTS[w]
    seen, defs, indirect, outs = slice_defs(lo, hi, WRITES[w], reg)
    P("[%s] write=0x%x host=[0x%x,0x%x) slice_size=%d indirect_jmp=%s out_edges=%s"
      % (w, WRITES[w], lo, hi, len(seen), [hex(a) for a in indirect], [(hex(a), hex(t)) for a, t in outs]))
    P("    %s defs in slice: %s" % (reg, [(hex(a), m, o) for a, m, o in defs]))

# 字面 0 写点
for w in ("W3", "W6", "W9"):
    va = WRITES[w]
    P("[%s] bytes @0x%x = %s  (expect c70584eda80000000000)" % (w, va, eng.rd(va, 10).hex()))

# W10 的 eax 在 xor 之后、写点之前有无 call（caller-saved）
ins10 = [i for i in S if 0x797541 <= i.address < 0x79758C]
P("[W10] between xor@0x797541 and write@0x79758C: calls=%s ; insns=%d"
  % ([hex(i.address) for i in ins10 if i.mnemonic == "call"], len(ins10)))
for a, b, m, o in eng.disasm(0x797541, 0x50):
    P("    0x%08x  %-16s %s %s" % (a, b, m, o))

# W1 的 ebx 在 xor@0x52D9C4 与写点 0x52DA08 之间
ins1 = [i for i in S if 0x52D9C4 <= i.address < 0x52DA08]
P("[W1] between xor@0x52D9C4 and write@0x52DA08: calls=%s ; %s"
  % ([hex(i.address) for i in ins1 if i.mnemonic == "call"],
     [(hex(i.address), i.mnemonic, i.op_str) for i in ins1]))

# ================= B. 宿主定界 =================
P("")
P("===== [B] 宿主定界 =====")
# E8 头集
tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
heads = set()
for i in range(len(tb) - 5):
    if tb[i] == 0xE8:
        va = eng.TLO + i
        rel = struct.unpack_from("<i", tb, i + 1)[0]
        t = va + 5 + rel
        if eng.TLO <= t < eng.THI:
            heads.add(t)
P("[E8 head set] unique targets = %d (claim 6719)" % len(heads))

ALL_HOSTS = dict(HOSTS)
ALL_HOSTS["W2"] = (0x55D360, 0x55DEE0)
for w, (lo, hi) in sorted(ALL_HOSTS.items()):
    ins, nxt, pred, indirect, outs = build_cfg(lo, hi)
    rets = [i.address for i in ins if i.mnemonic.startswith("ret")]
    callers = text_call_sites(lo)
    P("[%s] host=[0x%x,0x%x) rets=%d %s callers=%d %s next_head_bytes@0x%x=%s indirect=%s"
      % (w, lo, hi, len(rets), [hex(r) for r in rets], len(callers), [hex(c) for c in callers],
         hi, eng.rd(hi, 8).hex(), [hex(a) for a in indirect]))

# W2 额外：MLF 头字节
P("[MLF head 0x55D360] = %s" % eng.rd(0x55D360, 8).hex())
# W6 尾 jmp
P("[W6 tail 0x5E74D9] = %s" % eng.rd(0x5E74D9, 7).hex())
for a, b, m, o in eng.disasm(0x5E74D9, 7):
    P("    0x%08x  %s %s %s" % (a, b, m, o))
P("[W6 rets inside [0x5E7460,0x5E74E0)]: %s" %
  [hex(i.address) for i in S if 0x5E7460 <= i.address < 0x5E74E0 and i.mnemonic.startswith("ret")])

# W3 等待环回边
ins3, nxt3, pred3, ind3, outs3 = build_cfg(0x5B7090, 0x5B7360)
be3 = eng.loop_backedges(0x5B7090, 0x5B7360)
P("[W3 backedges] %s" % [(hex(a), hex(t), m) for a, t, m in be3])

# 0x77F900 调用者计数
c77 = text_call_sites(0x77F900)
P("[0x77F900 callers] = %d : %s" % (len(c77), [hex(c) for c in c77]))

# W9 调用侧守卫
P("[W9 caller guard 0x7800C0..0x7800F8]")
for a, b, m, o in eng.disasm(0x7800C0, 0x38):
    P("    0x%08x  %-16s %s %s" % (a, b, m, o))

# W9 宿主内 rep stosd + 1234..1237
P("[W9 host 1234..1237 @0x841F30]")
P("   bytes: %s" % eng.rd(0x841F30, 16).hex())

# W5 宿主 GetDlgItem/SendMessage 现场
P("[W5 0x5E54B0..0x5E5520]")
for a, b, m, o in eng.disasm(0x5E54B0, 0x70):
    P("    0x%08x  %-16s %s %s" % (a, b, m, o))

# W2 的 6 个调用者再列一遍 + init 的 2 个
P("[MLF callers] %s" % [hex(c) for c in text_call_sites(0x55D360)])
P("[init 0x52D9A0 callers] %s" % [hex(c) for c in text_call_sites(0x52D9A0)])
P("[W4 host 0x5BAC60 callers] %s" % [hex(c) for c in text_call_sites(0x5BAC60)])
P("[W3 host 0x5B7090 callers] %s" % [hex(c) for c in text_call_sites(0x5B7090)])
P("[W5 host 0x5E3D10 callers] %s" % [hex(c) for c in text_call_sites(0x5E3D10)])
P("[W6 host 0x5E7460 callers] %s" % [hex(c) for c in text_call_sites(0x5E7460)])
P("[W7 host 0x684620 callers] %s" % [hex(c) for c in text_call_sites(0x684620)])
P("[W8 host 0x686730 callers] %s" % [hex(c) for c in text_call_sites(0x686730)])
P("[W9 host 0x794BA0 callers] %s" % [hex(c) for c in text_call_sites(0x794BA0)])
P("[W10 host 0x7970D0 callers] %s" % [hex(c) for c in text_call_sites(0x7970D0)])

with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/P03/_v3_out_partAB.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("PARTAB SAVED")
