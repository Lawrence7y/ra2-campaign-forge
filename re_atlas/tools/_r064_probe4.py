# _r064_probe4.py -- R-064 仲裁探针4：
#  (a) 静态落实帧 D 两处间接虚拟 call（0x5cef6b [eax+8] / 0x5cef78 [edx+0x1C]）：
#      对象=0x473a80 构造 → 找其 vptr stamp → vtable 槽 → 目标函数 ret-imm（闭包法）
#  (b) 全帧 store 普查：每行 witness 槽 W 的全部 on-sim store 候选（证明 INIClass stamp 是唯一/最后写者）
#  (c) 最终 17 行逐行归属表
import struct, sys
import capstone
from _r064_probe3 import body, ret_imm, _closure_rets, decode_one, call_targets, preds
from _r064_probe1 import rd, rd32, cstr

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

def find_vptr_stamps(fn, limit=0x400):
    """函数头 fn 起 limit 字节内找 mov [reg+disp], imm32 且 imm 落 .rdata（vtable 候选）"""
    out = []
    va = fn
    for _ in range(400):
        if va not in body: break
        m, ops, sz = body[va]
        if m == "mov" and "," in ops:
            lhs, rhs = ops.split(",", 1)
            lhs = lhs.strip(); rhs = rhs.strip()
            if lhs.startswith("dword ptr [") and rhs.startswith("0x"):
                try: imm = int(rhs, 16)
                except ValueError: imm = None
                if imm is not None and 0x7E1000 <= imm < 0x812000:
                    out.append((va, lhs, imm))
        va += sz
        if va >= fn + limit: break
    return out

def vtable_name(V):
    col = rd32(V-4)
    if not col: return None, None
    td = rd32(col+0xC)
    return td, (cstr(td+8) if td else None)

print("== A. 0x473a80（帧 D 中 [esp+0x68] 对象的构造函数）的 vptr stamp ==")
st = find_vptr_stamps(0x473a80)
V68 = None
for va, lhs, imm in st:
    td, nm = vtable_name(imm)
    print("   @%#x %s = %#x -> TD=%s 名=%r" % (va, lhs, imm, hex(td) if td else None, nm))
    if nm and "INIClass" not in (nm or ""):
        V68 = imm  # 第一时间 stamp 的基 vptr
print("   -> 对象 vptr 候选 V =", hex(V68) if V68 else None)

print("\n== B. 该对象 vtable 槽 +8 / +0x1C 的目标函数及其 ret-imm ==")
if V68:
    for off in (8, 0x1C):
        tgt = rd32(V68 + off)
        ri = ret_imm(tgt) if tgt else None
        print("   [%#x+%#x] = %#x  ret-imm=%s" % (V68, off, tgt, hex(ri) if ri is not None else "None"))
        if tgt:
            for a, i in _closure_rets(tgt)[:4]:
                print("      ret@%#x imm=%#x" % (a, i))

print("\n== C. 全帧 store 普查：每行 witness 槽 W 的全部 mov [esp+X] 写候选 ==")
ROWS = [
    (0x5cefc9, 0x5cefc5, 0x38, 0x5ceef0), (0x5cf10e, 0x5cf10a, 0x38, 0x5ceef0),
    (0x5cf162, 0x5cf15e, 0x38, 0x5ceef0), (0x5cf284, 0x5cf280, 0x38, 0x5ceef0),
    (0x5cf2e0, 0x5cf2dc, 0x38, 0x5ceef0), (0x5cf42c, 0x5cf428, 0x38, 0x5ceef0),
    (0x5cf4c7, 0x5cf4c3, 0x38, 0x5ceef0), (0x5d76a9, 0x5d76a2, 0x88, 0x5d7590),
    (0x76c555, 0x76c551, 0x38, 0x76c290), (0x77884f, 0x77884b, 0x38, 0x778710),
    (0x77890c, 0x778908, 0x38, 0x778710), (0x778956, 0x778952, 0x38, 0x778710),
    (0x778bcf, 0x778bcb, 0x38, 0x778a20), (0x778dd1, 0x778dcd, 0x38, 0x778a20),
    (0x778e24, 0x778e20, 0x38, 0x778a20), (0x779c3d, 0x779c39, 0x24, 0x779b50),
    (0x779ebd, 0x779eb9, 0x24, 0x779dd0),
]
STAMPS = {
    0x7787c0: ("G-A", 0x38, 0x7E1B04), 0x7787f7: ("I-A", 0x30, 0x7EA5F4),
    0x779bb3: ("G-B", 0x24, 0x7E1B04), 0x779bea: ("I-B", 0x1c, 0x7EA5F4),
    0x779e33: ("G-C", 0x24, 0x7E1B04), 0x779e6a: ("I-C", 0x1c, 0x7EA5F4),
    0x5cef41: ("I-D", 0x28, 0x7EA5F4), 0x76c4a4: ("I-E", 0x30, 0x7EA5F4),
    0x778b20: ("I-F", 0x2c, 0x7EA5F4), 0x5d761d: ("I-16", 0x78, 0x7EA5F4),
}
STAMP_P = {  # 由 probe3 D-sim 单例 D 值换算的物理格（STRICT 模式已单例者）
    "G-A": 0x38 - 0xC4, "I-A": 0x30 - 0xC8,
    "G-B": 0x24 - 0xB0, "I-B": 0x1C - 0xB4,
    "G-C": 0x24 - 0xB0, "I-C": 0x1C - 0xB4,
    "I-D": 0x28 - 0xD4, "I-E": 0x30 - 0xDC,
    "I-F": 0x2C - 0xE4, "I-16": 0x78 - 0x124,
}
ROW_W = {  # probe3 D-sim 单例 W
    0x5cefc9: -0xAC, 0x5cf10e: -0xAC, 0x5cf162: -0xAC, 0x5cf284: -0xAC,
    0x5cf2e0: -0xAC, 0x5cf42c: -0xAC, 0x5cf4c7: -0xAC, 0x5d76a9: -0xAC,
    0x76c555: -0xAC, 0x77884f: -0x98, 0x77890c: -0x98, 0x778956: -0x98,
    0x778bcf: -0xB8, 0x778dd1: -0xB8, 0x778e24: -0xB8, 0x779c3d: -0x98, 0x779ebd: -0x98,
}

def stores_to_frame(head):
    """该函数闭包内全部 mov [esp+disp], imm/reg 存储指令"""
    out = []
    seen = set(); q = [head]
    while q:
        a = q.pop()
        while True:
            if a in seen or a not in body: break
            seen.add(a)
            m, ops, sz = body[a]
            ins = None
            if m == "mov":
                b = rd(a, 16)
                ins = next(md.disasm(b, a), None)
            is_store = False; disp = None; imm = None; reg = None
            if m == "mov" and ins is not None and ins.operands and len(ins.operands) == 2:
                o0, o1 = ins.operands
                if o0.type == capstone.x86.X86_OP_MEM and ins.reg_name(o0.mem.base) == "esp":
                    disp = o0.mem.disp
                    if o1.type == capstone.x86.X86_OP_IMM: imm = o1.imm
                    elif o1.type == capstone.x86.X86_OP_REG: reg = ins.reg_name(o1.reg)
                    is_store = (o0.mem.index == 0)
            if is_store:
                out.append((a, disp, imm, reg))
            if m == "ret": break
            if m == "jmp":
                try: a = int(ops, 16); continue
                except ValueError: break
            if m.startswith("j"):
                try: q.append(int(ops, 16))
                except ValueError: pass
            a = a + sz
    return out

frame_cache = {}
for row_va, lea_va, disp, head in ROWS:
    if head not in frame_cache:
        frame_cache[head] = stores_to_frame(head)
    W = ROW_W[row_va]
    # 候选写者：disp − D_sim == W。D_sim 逐 store 无法全算，改用「stamp 表 + disp@D」：
    # 这里用已知 stamp 的 P 匹配 + 列出该帧内所有与 W 相关的 c7 imm 写（其 P 用行内 D 推算）
    cands = []
    for (va, d, imm, reg) in frame_cache[head]:
        if imm is not None and imm in (0x7E1B04, 0x7EA5F4, 0x7E1AFC, 0x7E1B0C, 0x7E1668):
            cands.append((va, d, imm))
    print("   行 %#x W=%s 帧内 vptr-store 候选: %s" % (
        row_va, hex(W),
        ", ".join("@%#x[esp+0x%02x]=%#x" % c for c in sorted(cands))))

print("\n== D. stamp 物理格 vs 行 W 逐行配对（用 probe3 单例 D） ==")
fam = {0x7E1B04: "GenericList", 0x7EA5F4: "INIClass", 0x7E1AFC: "List<INISection*>", 0x7E1668: "CDFileClass"}
for row_va, lea_va, disp, head in ROWS:
    W = ROW_W[row_va]
    hits = [lab for lab, p in STAMP_P.items() if p == W and head in (0x5ceef0, 0x5d7590, 0x76c290, 0x778710, 0x778a20, 0x779b50, 0x779dd0)]
    # 同帧限制
    same = {"G-A": 0x778710, "I-A": 0x778710, "G-B": 0x779b50, "I-B": 0x779b50,
            "G-C": 0x779dd0, "I-C": 0x779dd0, "I-D": 0x5ceef0, "I-E": 0x76c290,
            "I-F": 0x778a20, "I-16": 0x5d7590}
    hits = [lab for lab, p in STAMP_P.items() if p == W and same.get(lab) == head]
    print("   行 %#x (帧 %#x) W=%s <- stamp %s" % (row_va, head, hex(W), hits if hits else "无 stamp 命中"))
